"""青柠 Booking — REST 路由（设计文档 §2 / PRD §4.1）。

挂载于 main.py 的 ``/api/v2/bookings``。

端点：
- POST /precheck              档期预检（防护①）
- POST /                      创建真实锁位（走四层防护，返回 booking_no）
- POST /{booking_no}/extend   续期（受档位约束）
- POST /{booking_no}/release  释放（→RELEASED）
- POST /{booking_no}/cancel   取消（→CANCELLED，写原因）
- POST /{booking_no}/install  安装状态流转
- GET  /                       锁位查询（media_resource_id / status 过滤）
- GET  /point/{media_resource_id}/timeline  点位档期占用时间轴
- GET  /{booking_no}           获取单条

业务异常（QinglinError）由 main.py 的全局异常处理器统一映射为 HTTP 状态码。
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.async_db import AsyncSessionLocal
from app.schemas.booking import (
    AvailabilityQuery,
    AvailabilityResult,
    BookingCancel,
    BookingCreate,
    BookingExtend,
    BookingInstall,
    BookingRead,
    BookingRelease,
)
from app.services import booking_service as svc

router = APIRouter(tags=["青柠 Booking 真实锁位"])


async def get_async_db():
    async with AsyncSessionLocal() as db:
        yield db


@router.post("/precheck", response_model=AvailabilityResult)
async def precheck(q: AvailabilityQuery, db: AsyncSession = Depends(get_async_db)):
    available, conflict = await svc.check_availability(
        db, q.media_resource_id, q.lock_start, q.lock_end
    )
    return AvailabilityResult(available=available, conflict_booking_no=conflict)


@router.post("/", response_model=BookingRead)
async def create(req: BookingCreate, db: AsyncSession = Depends(get_async_db)):
    booking = await svc.create_booking(
        db,
        media_resource_id=req.media_resource_id,
        lock_start=req.lock_start,
        lock_end=req.lock_end,
        idempotency_key=req.idempotency_key,
        customer_id=req.customer_id,
        campaign_id=req.campaign_id,
        created_by=req.created_by,
        unit_price_snapshot=req.unit_price_snapshot,
        weeks=req.weeks,
        discount_rate=req.discount_rate,
        extra_fee=req.extra_fee,
        final_amount=req.final_amount,
    )
    return BookingRead.model_validate(booking)


@router.post("/{booking_no}/extend", response_model=BookingRead)
async def extend(booking_no: str, req: BookingExtend, db: AsyncSession = Depends(get_async_db)):
    booking = await svc.extend_booking(db, booking_no, extend_days=req.extend_days)
    return BookingRead.model_validate(booking)


@router.post("/{booking_no}/release", response_model=BookingRead)
async def release(booking_no: str, req: BookingRelease, db: AsyncSession = Depends(get_async_db)):
    booking = await svc.release_booking(db, booking_no, reason=req.reason)
    return BookingRead.model_validate(booking)


@router.post("/{booking_no}/cancel", response_model=BookingRead)
async def cancel(booking_no: str, req: BookingCancel, db: AsyncSession = Depends(get_async_db)):
    booking = await svc.cancel_booking(db, booking_no, cancel_reason=req.cancel_reason)
    return BookingRead.model_validate(booking)


@router.post("/{booking_no}/install", response_model=BookingRead)
async def install(booking_no: str, req: BookingInstall, db: AsyncSession = Depends(get_async_db)):
    booking = await svc.update_install_status(db, booking_no, install_status=req.install_status)
    return BookingRead.model_validate(booking)


@router.get("/point/{media_resource_id}/timeline", response_model=list[BookingRead])
async def timeline(
    media_resource_id: UUID,
    db: AsyncSession = Depends(get_async_db),
):
    rows = await svc.get_timeline(db, media_resource_id)
    return [BookingRead.model_validate(r) for r in rows]


@router.get("/", response_model=list[BookingRead])
async def list_bookings(
    media_resource_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_async_db),
):
    rows = await svc.list_bookings(db, media_resource_id=media_resource_id, status=status)
    return [BookingRead.model_validate(r) for r in rows]


@router.get("/{booking_no}", response_model=BookingRead)
async def get_one(booking_no: str, db: AsyncSession = Depends(get_async_db)):
    booking = await svc.get_booking(db, booking_no)
    return BookingRead.model_validate(booking)
