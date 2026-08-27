"""青柠 Booking — ORM 模型（挂在 app.models.Base 上）。

模型（设计文档 §4.1 / P0-3）：
- ``BookingStatus`` / ``InstallStatus`` / ``LockTier``：枚举（原生 PG 枚举）。
- ``Booking``：核心锁位实体（状态机 7 态）。
- ``LockTierConfig``：五档锁位参数（A++/A+/A/B/C），可后台配置。
- ``MediaLevelRule``：level 派生配置（媒体类型 × 城市 → 默认档）。

枚举使用 ``create_type=True``，使存量 ``init_db()``（create_all）不会因缺少枚举类型而报错；
权威 DDL（含 EXCLUDE 约束、种子）由 Alembic 迁移 ``0001_booking.py`` 建立，二者幂等共存。
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Date,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UUID,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


# ─────────────────────────────────────────────────────────────
# 枚举
# ─────────────────────────────────────────────────────────────

class BookingStatus(str, Enum):
    SELECTED = "SELECTED"
    LOCKED = "LOCKED"
    PUBLISHED = "PUBLISHED"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    TERMINATED = "TERMINATED"


class InstallStatus(str, Enum):
    PENDING = "PENDING"
    INSTALLED = "INSTALLED"
    VERIFIED = "VERIFIED"
    ABNORMAL = "ABNORMAL"


class LockTier(str, Enum):
    A_PLUS_PLUS = "A++"
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"


def _utcnow():
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────────
# 表模型
# ─────────────────────────────────────────────────────────────

class Booking(Base):
    __tablename__ = "bookings"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_no = mapped_column(String(32), nullable=False, unique=True)
    media_resource_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_resources.id"), nullable=False
    )
    campaign_id = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=True)
    customer_id = mapped_column(String(64), nullable=True)
    lock_tier = mapped_column(SAEnum("A++", "A+", "A", "B", "C", name="lock_tier", create_type=True), nullable=False)
    lock_start = mapped_column(Date, nullable=False)
    lock_end = mapped_column(Date, nullable=False)
    expire_at = mapped_column(DateTime(timezone=True), nullable=False)
    status = mapped_column(
        SAEnum(
            "SELECTED", "LOCKED", "PUBLISHED", "RELEASED", "EXPIRED", "CANCELLED", "TERMINATED",
            name="booking_status", create_type=True,
        ),
        nullable=False,
        default=BookingStatus.SELECTED,
    )
    idempotency_key = mapped_column(String(128), nullable=False, unique=True)
    unit_price_snapshot = mapped_column(Numeric(10, 2), nullable=True)
    weeks = mapped_column(Integer, nullable=True)
    discount_rate = mapped_column(Numeric(5, 4), nullable=True)
    extra_fee = mapped_column(Numeric(10, 2), nullable=True)
    final_amount = mapped_column(Numeric(12, 2), nullable=True)
    install_status = mapped_column(
        SAEnum("PENDING", "INSTALLED", "VERIFIED", "ABNORMAL", name="install_status", create_type=True),
        nullable=False,
        default=InstallStatus.PENDING,
    )
    extend_count = mapped_column(Integer, nullable=False, default=0)
    cancel_reason = mapped_column(Text, nullable=True)
    created_by = mapped_column(String(64), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    __table_args__ = (
        CheckConstraint("lock_end >= lock_start", name="ck_booking_date_order"),
    )


class LockTierConfig(Base):
    __tablename__ = "lock_tier_config"

    level = mapped_column(SAEnum("A++", "A+", "A", "B", "C", name="lock_tier", create_type=True), primary_key=True)
    base_days = mapped_column(Integer, nullable=False)
    extend_times = mapped_column(Integer, nullable=False)
    extend_days = mapped_column(Integer, nullable=False)


class MediaLevelRule(Base):
    __tablename__ = "media_level_rule"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_type = mapped_column(String(12), nullable=False)  # 'media_type' | 'city'
    match_key = mapped_column(String(64), nullable=False)
    level = mapped_column(SAEnum("A++", "A+", "A", "B", "C", name="lock_tier", create_type=True), nullable=False)
    priority = mapped_column(Integer, nullable=False, default=0)
    enabled = mapped_column(Boolean, nullable=False, default=True)
