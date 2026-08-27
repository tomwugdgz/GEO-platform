"""青柠 Booking — Pydantic v2 schemas（设计文档 §3.2 / PRD §4.1）。"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.booking import BookingStatus, InstallStatus, LockTier


class AvailabilityQuery(BaseModel):
    media_resource_id: UUID
    lock_start: date  # PRD start_date
    lock_end: date    # PRD end_date（含端点，最后展示日）


class AvailabilityResult(BaseModel):
    available: bool
    conflict_booking_no: Optional[str] = None


class BookingCreate(BaseModel):
    media_resource_id: UUID
    customer_id: Optional[str] = None
    campaign_id: Optional[UUID] = None
    lock_start: date
    lock_end: date
    idempotency_key: Optional[str] = None  # 不传则由服务端按会话+点位+档期生成
    created_by: Optional[str] = None
    # 价格快照（可选，锁位瞬间固化；不传则留空）
    unit_price_snapshot: Optional[Decimal] = None
    weeks: Optional[int] = None
    discount_rate: Optional[Decimal] = None
    extra_fee: Optional[Decimal] = None
    final_amount: Optional[Decimal] = None


class BookingExtend(BaseModel):
    extend_days: Optional[int] = None  # 不传则取该档位 extend_days


class BookingRelease(BaseModel):
    reason: Optional[str] = None


class BookingCancel(BaseModel):
    cancel_reason: str


class BookingInstall(BaseModel):
    install_status: str  # PENDING/INSTALLED/VERIFIED/ABNORMAL


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    booking_no: str
    media_resource_id: UUID
    lock_tier: str
    lock_start: date
    lock_end: date
    expire_at: datetime
    status: str
    install_status: str
    idempotency_key: str
    customer_id: Optional[str] = None
    campaign_id: Optional[UUID] = None
    unit_price_snapshot: Optional[Decimal] = None
    weeks: Optional[int] = None
    discount_rate: Optional[Decimal] = None
    extra_fee: Optional[Decimal] = None
    final_amount: Optional[Decimal] = None
    extend_count: int = 0
    cancel_reason: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BookingListQuery(BaseModel):
    media_resource_id: Optional[UUID] = None
    status: Optional[str] = None
