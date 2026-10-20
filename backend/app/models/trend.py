"""
MTO / GEO 指标快照表 —— 供「趋势与优化顾问」消费时序数据。

每个快照保存一期累积的关键 MTO-GEO 指标（AIVO 四维、AI 提及率、舆情健康度、
MTO 信任分、证据链完整性等），用于：
  1) 统计判别：对各关键指标做线性回归，得到斜率与下一期预测；
  2) AI 判别：把近期状态写成「人话战报」喂给 Laya 决策引擎（LAYA 本地 / JEV 远程，
     auto 自动切换），由它从若干可执行优化方向中选出最优。
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, Float, DateTime, JSON, Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models import Base


class MetricSnapshot(Base):
    """MTO / GEO 指标时序快照（趋势与优化顾问的数据源）"""

    __tablename__ = "geo_metric_snapshots"
    __table_args__ = (
        Index("ix_metric_snap_tenant_brand", "tenant_id", "brand_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    brand_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    period_label = Column(String(64), nullable=True, index=True)   # 如 2026-W42 / 2026-10-20
    source = Column(String(32), nullable=False, default="manual")  # diagnosis/monitor/manual

    # ── 反归一化关键指标（便于趋势查询与战败报）──────────────
    aivo_ai_visibility = Column(Float, nullable=True)   # AI 可见性
    aivo_infrastructure = Column(Float, nullable=True)  # 基建完善度
    aivo_advantage = Column(Float, nullable=True)       # 竞争优势
    aivo_sentiment = Column(Float, nullable=True)       # 舆情健康度（诊断侧）
    aivo_total = Column(Float, nullable=True)          # AIVO 综合分
    mention_rate = Column(Float, nullable=True)        # AI 平台平均提及率
    sentiment_health = Column(Float, nullable=True)    # 舆情健康度（监测侧）
    trust_score = Column(Float, nullable=True)         # MTO 信任量化（实验性）
    evidence_completeness = Column(Float, nullable=True)  # MTO 证据链完整性

    metrics = Column(JSONB, default=dict)              # 其余原始指标（保留全量）
    snapshot_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
