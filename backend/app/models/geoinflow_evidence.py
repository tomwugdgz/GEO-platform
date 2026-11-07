"""
爬取观测与身份核验证据表 —— GEOInflow 借鉴资产的持久化层。
=================================================================================
设计依据（上游 docs/crawler-recognition.md / docs/traffic-quality.md）：
  · 「声明的 UA、官方 IP 范围匹配、DNS 或可信边缘证据分别独立存储」；
  · 「每条日志保留核验时的版本及观测时间，后续更新不改写该证据」；
  · 「质量表不保存原始 IP 或完整 UA」→ 本表只存 UA 中的产品 token 与规范化路径。

与现有表的区分（避免重复冲突）：
  · geo_monitor_snapshots  —— AI 平台提及率/首推率等聚合快照
  · geo_metric_snapshots   —— MTO/GEO 指标时序快照（趋势顾问数据源）
  · geo_crawler_observations（本表）—— 单条爬取观测 + 身份核验证据链
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models import Base


class CrawlerObservation(Base):
    """单条爬取观测记录及其身份核验证据（不存原始 IP / 完整 UA）。"""

    __tablename__ = "geo_crawler_observations"
    __table_args__ = (
        Index("ix_crawler_obs_tenant_brand", "tenant_id", "brand_id"),
        Index("ix_crawler_obs_observed_at", "observed_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    brand_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    period_label = Column(String(64), nullable=True, index=True)

    # ── 观测事实 ───────────────────────────────────────────────
    declared_token = Column(String(128), nullable=True)      # UA 中声明的产品 token（非完整 UA）
    candidate_identity_id = Column(String(128), nullable=True)  # 目录稳定 ID（候选，非核验结论）
    purpose = Column(String(32), nullable=True)              # ai_search / user_initiated / ai_training / ...
    path = Column(String(2048), nullable=True)               # 规范化路径，保留尾部斜线
    http_status = Column(Integer, nullable=True)              # 200 / 304 等
    method = Column(String(8), nullable=True, default="GET")
    source = Column(String(32), nullable=False, default="manual")  # server_log / cdn_log / manual

    # ── 身份核验证据（三项独立存储，互不推导）──────────────────
    official_range_verified = Column(Boolean, nullable=False, default=False)
    range_snapshot_version = Column(String(128), nullable=True)  # 归档的范围快照版本
    trusted_ingress = Column(Boolean, nullable=False, default=False)
    dns_or_edge_evidence = Column(Boolean, nullable=False, default=False)
    evidence_state = Column(String(32), nullable=False, default="unknown", index=True)
    can_claim_identity = Column(Boolean, nullable=False, default=False)

    # ── 附加证据（原始字段不落库，避免留存访客隐私）────────────
    evidence = Column(JSONB, default=dict)
    observed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
