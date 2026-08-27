"""青柠 Booking — 到期释放 job（设计文档 §10 / P0-6）。

扫描 LOCKED 且 expire_at 过期的单 → 置 EXPIRED，档期立即恢复可用（CT-02）；
同时 DEL 对应 Redis 层②锁键。可作为 APScheduler 入口，也可由 OS 计划任务
独立调用（``python -m app.tasks.booking_release``）。
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.async_db import AsyncSessionLocal
from app.core.distributed_lock import lock_key, release_lock
from app.models.booking import Booking, BookingStatus


async def release_expired_bookings() -> int:
    """释放所有过期 LOCKED 单。返回释放条数。"""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    released = 0
    async with AsyncSessionLocal() as db:
        rows = (
            await db.execute(
                select(Booking).where(
                    Booking.status == BookingStatus.LOCKED,
                    Booking.expire_at < now,
                )
            )
        ).scalars().all()
        for b in rows:
            b.status = BookingStatus.EXPIRED
            b.updated_at = now
            # 释放 Redis 层②锁（best-effort）
            await release_lock(
                lock_key(b.media_resource_id, b.lock_start, b.lock_end), "*", force=True
            )
            released += 1
        await db.commit()
    return released


if __name__ == "__main__":
    async def _main():
        n = await release_expired_bookings()
        print(f"释放过期锁位 {n} 条")

    asyncio.run(_main())
