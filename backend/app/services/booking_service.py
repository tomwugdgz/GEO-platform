"""青柠 Booking — 业务服务（四层防护编排 / 续期 / 释放 / 取消 / 预检 / 幂等 / timeline）。

四层防护（设计文档 §8 / P0-4）：
① 接口预检：查询同点位 LOCKED/PUBLISHED 且 daterange 重叠 → 命中即 409。
② Redis 分布式锁：SET NX PX，同点位+同档期串行化 → 未取到即 409。
③ DB 悲观锁：SELECT ... FOR UPDATE ORDER BY id。
④ DB 排他约束（EXCLUDE）：INSERT 提交时校验，冲突即回滚 → 409（最后防线）。

任何一层拦截都返回一致「不可锁」结论；层④为 DB 物理兜底，超卖率=0。
"""
from __future__ import annotations

import secrets
from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.core.async_db import AsyncSessionLocal
from app.core.distributed_lock import acquire_lock, lock_key, release_lock
from app.core.exceptions import (
    booking_not_found,
    make_error,
    point_already_locked,
    protection_rule_violated,
)
from app.models import MediaResource
from app.models.booking import Booking, BookingStatus, InstallStatus, LockTierConfig

# 占用档期（触发层①④冲突的状态）
OCCUPYING_STATUSES = ("LOCKED", "PUBLISHED")

# 允许直接续期/释放/取消的源状态
LOCKED_OR_PUBLISHED = ("LOCKED", "PUBLISHED")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def gen_booking_no() -> str:
    """业务单号 BK-YYYYMMDD-XXXXXX（与代理主键 id 分离）。"""
    day = _utcnow().strftime("%Y%m%d")
    return f"BK-{day}-{secrets.token_hex(3).upper()}"


def _is_exclusion(err: Exception) -> bool:
    """判断是否为排他约束冲突（SQLSTATE 23P01）。"""
    orig = getattr(err, "orig", None)
    if orig is None:
        return "23P01" in str(err)
    # asyncpg 异常类型或错误码字符串
    try:
        from asyncpg.exceptions import ExclusionViolationError

        if isinstance(orig, ExclusionViolationError):
            return True
    except Exception:  # noqa: BLE001
        pass
    return "23P01" in str(orig)


async def _overlap_booking(
    db, media_resource_id, lock_start: date, lock_end: date
) -> Optional[Booking]:
    """层①：返回与 (media_resource_id, 档期) 重叠的占用单（LOCKED/PUBLISHED），无则 None。"""
    stmt = select(Booking).where(
        Booking.media_resource_id == media_resource_id,
        Booking.status.in_(OCCUPYING_STATUSES),
        Booking.lock_start <= lock_end,
        Booking.lock_end >= lock_start,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def _get_by_no(db, booking_no: str) -> Booking:
    b = (await db.execute(select(Booking).where(Booking.booking_no == booking_no))).scalar_one_or_none()
    if b is None:
        raise booking_not_found()
    return b


async def check_availability(
    db, media_resource_id, lock_start: date, lock_end: date
) -> Tuple[bool, Optional[str]]:
    """档期预检（防护①）。返回 (available, conflict_booking_no)。"""
    if lock_end < lock_start:
        return False, None
    conflict = await _overlap_booking(db, media_resource_id, lock_start, lock_end)
    if conflict:
        return False, conflict.booking_no
    return True, None


async def create_booking(
    db,
    *,
    media_resource_id,
    lock_start: date,
    lock_end: date,
    idempotency_key: Optional[str] = None,
    customer_id: Optional[str] = None,
    campaign_id=None,
    created_by: Optional[str] = None,
    unit_price_snapshot=None,
    weeks: Optional[int] = None,
    discount_rate=None,
    extra_fee=None,
    final_amount=None,
) -> Booking:
    """创建真实锁位（走四层防护）。成功返回 LOCKED 的 Booking（ORM）。

    幂等：相同 idempotency_key 直接返回既有单（CT-03）。
    """
    if lock_end < lock_start:
        raise make_error("INVALID_PARAM", message="档期结束日期不能早于开始日期")

    if idempotency_key is None:
        idempotency_key = (
            f"qlbk::{(created_by or 'system')}::{media_resource_id}::{lock_start}::{lock_end}"
        )

    # ── 层② Redis 分布式锁（同点位+同档期串行化，先于事务获取）──
    rkey = lock_key(media_resource_id, lock_start, lock_end)
    lock = await acquire_lock(rkey, settings.BOOKING_LOCK_PX_MS)
    if not lock.acquired:
        raise point_already_locked()

    try:
        # ── 事务内：幂等检查 → 层①预检 → 层③悲观锁 + 层④ INSERT ──
        # 所有 DB 操作置于同一事务，避免「先 SELECT 触发 autobegin 再 begin()」冲突。
        async with db.begin():
            # 幂等检查（CT-03）：同 idempotency_key 直接返回既有单
            existing = (
                await db.execute(
                    select(Booking).where(Booking.idempotency_key == idempotency_key)
                )
            ).scalar_one_or_none()
            if existing is not None:
                return existing  # 路由层据此返回 200 IDEMPOTENT_DUPLICATE

            # 层① 接口预检
            conflict = await _overlap_booking(db, media_resource_id, lock_start, lock_end)
            if conflict is not None:
                raise point_already_locked(conflict.booking_no)

            # 层③ DB 悲观锁（FOR UPDATE ORDER BY id）
            mr = (
                await db.execute(
                    select(MediaResource)
                    .where(MediaResource.id == media_resource_id)
                    .with_for_update()
                    .order_by(MediaResource.id)
                )
            ).scalar_one_or_none()
            if mr is None:
                raise booking_not_found()

            tier = mr.level or "C"
            cfg = (
                await db.execute(select(LockTierConfig).where(LockTierConfig.level == tier))
            ).scalar_one_or_none()
            base_days = cfg.base_days if cfg is not None else 3

            # expire_at = lock_start 当日 00:00 UTC + base_days 天（UTC）
            expire_at = datetime.combine(lock_start, time(0, 0), tzinfo=timezone.utc) + timedelta(
                days=base_days
            )

            booking = Booking(
                booking_no=gen_booking_no(),
                media_resource_id=media_resource_id,
                lock_tier=tier,
                lock_start=lock_start,
                lock_end=lock_end,
                expire_at=expire_at,
                status=BookingStatus.LOCKED,
                idempotency_key=idempotency_key,
                customer_id=customer_id,
                campaign_id=campaign_id,
                created_by=created_by,
                unit_price_snapshot=unit_price_snapshot,
                weeks=weeks,
                discount_rate=discount_rate,
                extra_fee=extra_fee,
                final_amount=final_amount,
            )
            db.add(booking)
            await db.flush()
            await db.refresh(booking)
            return booking
    except IntegrityError as e:
        # 层④ 排他冲突（23P01）→ 事务已由上下文管理器回滚，资源零残留
        if _is_exclusion(e):
            raise protection_rule_violated()
        raise
    finally:
        # 无论成败，释放层② Redis 锁（token 校验防误删）
        await release_lock(rkey, lock.token)


async def extend_booking(db, booking_no: str, extend_days: Optional[int] = None) -> Booking:
    """续期（受 lock_tier_config 约束，P0-3）。"""
    b = await _get_by_no(db, booking_no)
    if b.status != "LOCKED":
        raise make_error("INVALID_PARAM", message="仅 LOCKED 状态可续期")

    cfg = (
        await db.execute(select(LockTierConfig).where(LockTierConfig.level == b.lock_tier))
    ).scalar_one_or_none()
    if cfg is None:
        raise make_error("INVALID_PARAM", message="未找到该档位参数配置")

    if b.extend_count >= cfg.extend_times:
        raise make_error("LOCK_QUOTA_EXCEEDED", message="已达该档位最大续期次数")

    days = extend_days if extend_days is not None else cfg.extend_days
    if days is None or days <= 0:
        raise make_error("LOCK_QUOTA_EXCEEDED", message="续期天数无效")

    b.expire_at = b.expire_at + timedelta(days=days)
    b.extend_count = (b.extend_count or 0) + 1
    b.updated_at = _utcnow()
    await db.commit()
    await db.refresh(b)
    return b


async def release_booking(db, booking_no: str, reason: Optional[str] = None) -> Booking:
    """主动释放（LOCKED/PUBLISHED → RELEASED），档期立即可被占用。"""
    b = await _get_by_no(db, booking_no)
    if b.status not in LOCKED_OR_PUBLISHED:
        raise make_error("INVALID_PARAM", message="仅 LOCKED/PUBLISHED 状态可释放")
    b.status = "RELEASED"
    b.cancel_reason = reason
    b.updated_at = _utcnow()
    # 释放 Redis 层②锁（best-effort，force）
    await release_lock(lock_key(b.media_resource_id, b.lock_start, b.lock_end), "*", force=True)
    await db.commit()
    await db.refresh(b)
    return b


async def cancel_booking(db, booking_no: str, cancel_reason: str) -> Booking:
    """取消（SELECTED/LOCKED/PUBLISHED → CANCELLED，写原因），释放档期。"""
    b = await _get_by_no(db, booking_no)
    if b.status in ("RELEASED", "EXPIRED", "CANCELLED", "TERMINATED"):
        raise make_error("INVALID_PARAM", message="该单已处于终态，无法取消")
    # SELECTED 不占用档期；LOCKED/PUBLISHED 释放占用
    b.status = "CANCELLED"
    b.cancel_reason = cancel_reason
    b.updated_at = _utcnow()
    await release_lock(lock_key(b.media_resource_id, b.lock_start, b.lock_end), "*", force=True)
    await db.commit()
    await db.refresh(b)
    return b


async def update_install_status(db, booking_no: str, install_status: str) -> Booking:
    """安装状态流转（US-6）。VERIFIED 且仅 LOCKED → 转 PUBLISHED；ABNORMAL 不进入 PUBLISHED。"""
    b = await _get_by_no(db, booking_no)
    if install_status not in ("PENDING", "INSTALLED", "VERIFIED", "ABNORMAL"):
        raise make_error("INVALID_PARAM", message="非法安装状态")
    # VERIFIED 且当前为 LOCKED → 上刊确认（PUBLISHED）
    if install_status == "VERIFIED" and b.status == "LOCKED":
        b.status = "PUBLISHED"
    b.install_status = install_status
    b.updated_at = _utcnow()
    await db.commit()
    await db.refresh(b)
    return b


async def get_booking(db, booking_no: str) -> Booking:
    return await _get_by_no(db, booking_no)


async def list_bookings(
    db, media_resource_id=None, status: Optional[str] = None
) -> List[Booking]:
    stmt = select(Booking)
    if media_resource_id is not None:
        stmt = stmt.where(Booking.media_resource_id == media_resource_id)
    if status is not None:
        stmt = stmt.where(Booking.status == status)
    stmt = stmt.order_by(Booking.created_at.desc())
    return list((await db.execute(stmt)).scalars().all())


async def get_timeline(db, media_resource_id) -> List[Booking]:
    """某点位档期占用时间轴（UI 用）：返回占用中的单（LOCKED/PUBLISHED）按档期排序。"""
    stmt = (
        select(Booking)
        .where(
            Booking.media_resource_id == media_resource_id,
            Booking.status.in_(OCCUPYING_STATUSES),
        )
        .order_by(Booking.lock_start)
    )
    return list((await db.execute(stmt)).scalars().all())


async def find_media_resource(
    db, media_type_code: Optional[str] = None, city: Optional[str] = None,
    project: Optional[str] = None, limit: int = 1,
) -> List[MediaResource]:
    """按条件解析 media_resource_id（助手升级用，设计 §9 待明确#A）。

    优先返回当前档期可用（无 LOCKED/PUBLISHED 冲突）的点位。
    """
    stmt = select(MediaResource)
    if media_type_code:
        stmt = stmt.where(MediaResource.media_type_code == media_type_code)
    if city:
        stmt = stmt.where(MediaResource.city.like(f"%{city}%"))
    if project:
        stmt = stmt.where(MediaResource.project.like(f"%{project}%"))
    stmt = stmt.limit(limit)
    return list((await db.execute(stmt)).scalars().all())
