"""
MTO 趋势与优化顾问 API
────────────────────────────────────────────────────────────────────────────
端点（前缀 /api/v2/trend）：
  POST /snapshot          上报一期 MTO/GEO 指标快照（落库 geo_metric_snapshots）
  GET  /snapshots         查询近期快照列表
  POST /predict          基于累积数据判别未来趋势 + 推荐优化方向（LAYA/JEV 可切换）
  GET  /predict          同上（查询参数版，便于 Agent / 浏览器直接调）
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models import get_db
from app.models.trend import MetricSnapshot
from app.services.trend_advisor import (
    predict_trend,
    snapshot_to_metrics,
)

router = APIRouter()

# 可落库的关键指标字段（与 MetricSnapshot 列对应）
_NUMERIC_FIELDS = [
    "aivo_ai_visibility", "aivo_infrastructure", "aivo_advantage",
    "aivo_sentiment", "aivo_total", "mention_rate", "sentiment_health",
    "trust_score", "evidence_completeness",
]


def _parse_uuid(v: Optional[str]):
    if not v:
        return None
    try:
        return uuid.UUID(v)
    except Exception:
        return None


class SnapshotIn(BaseModel):
    tenant_id: Optional[str] = None
    brand_id: Optional[str] = None
    period_label: Optional[str] = None
    source: str = "manual"               # diagnosis / monitor / manual
    metrics: Dict[str, Any] = Field(default_factory=dict)


class PredictIn(BaseModel):
    tenant_id: Optional[str] = None
    brand_id: Optional[str] = None
    backend: str = "auto"                # local / remote / auto
    limit: int = 12


@router.post("/snapshot")
def create_snapshot(payload: SnapshotIn, db: Session = Depends(get_db)):
    """上报一期 MTO/GEO 指标快照（供趋势顾问消费）。"""
    m = payload.metrics or {}
    kw = {f: (m.get(f) if isinstance(m.get(f), (int, float)) else None) for f in _NUMERIC_FIELDS}
    snap = MetricSnapshot(
        tenant_id=_parse_uuid(payload.tenant_id),
        brand_id=_parse_uuid(payload.brand_id),
        period_label=payload.period_label,
        source=payload.source,
        metrics=m,
        **kw,
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return {
        "snapshot_id": str(snap.id),
        "snapshot_at": snap.snapshot_at.isoformat() if snap.snapshot_at else None,
        "period_label": snap.period_label,
        "source": snap.source,
    }


@router.get("/snapshots")
def list_snapshots(
    tenant_id: Optional[str] = Query(None),
    brand_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """查询近期快照列表（按时间倒序）。"""
    q = db.query(MetricSnapshot)
    if _parse_uuid(tenant_id):
        q = q.filter(MetricSnapshot.tenant_id == _parse_uuid(tenant_id))
    if _parse_uuid(brand_id):
        q = q.filter(MetricSnapshot.brand_id == _parse_uuid(brand_id))
    rows = q.order_by(MetricSnapshot.snapshot_at.desc()).limit(limit).all()
    return {
        "count": len(rows),
        "snapshots": [
            {
                "snapshot_id": str(r.id),
                "period_label": r.period_label,
                "source": r.source,
                "snapshot_at": r.snapshot_at.isoformat() if r.snapshot_at else None,
                "aivo_total": r.aivo_total,
                "mention_rate": r.mention_rate,
                "trust_score": r.trust_score,
                "evidence_completeness": r.evidence_completeness,
            }
            for r in rows
        ],
    }


@router.post("/predict")
def predict(payload: PredictIn, db: Session = Depends(get_db)):
    """基于累积数据判别 MTO 未来趋势并推荐优化方向（LAYA/JEV 可切换）。"""
    q = db.query(MetricSnapshot)
    if _parse_uuid(payload.tenant_id):
        q = q.filter(MetricSnapshot.tenant_id == _parse_uuid(payload.tenant_id))
    if _parse_uuid(payload.brand_id):
        q = q.filter(MetricSnapshot.brand_id == _parse_uuid(payload.brand_id))
    rows = q.order_by(MetricSnapshot.snapshot_at.asc()).limit(payload.limit).all()
    if len(rows) < 2:
        raise HTTPException(
            status_code=400,
            detail=f"累积快照不足 2 期（当前 {len(rows)} 期），请先通过 POST /api/v2/trend/snapshot 上报多期指标",
        )
    snapshots = [snapshot_to_metrics(r) for r in rows]
    return predict_trend(snapshots, backend=payload.backend)


@router.get("/predict")
def predict_get(
    tenant_id: Optional[str] = Query(None),
    brand_id: Optional[str] = Query(None),
    backend: str = Query("auto"),
    limit: int = Query(12, ge=2, le=200),
    db: Session = Depends(get_db),
):
    """GET 版趋势预测（便于 Agent / 浏览器 / A2A 直接调用）。"""
    q = db.query(MetricSnapshot)
    if _parse_uuid(tenant_id):
        q = q.filter(MetricSnapshot.tenant_id == _parse_uuid(tenant_id))
    if _parse_uuid(brand_id):
        q = q.filter(MetricSnapshot.brand_id == _parse_uuid(brand_id))
    rows = q.order_by(MetricSnapshot.snapshot_at.asc()).limit(limit).all()
    if len(rows) < 2:
        raise HTTPException(
            status_code=400,
            detail=f"累积快照不足 2 期（当前 {len(rows)} 期），请先上报多期指标",
        )
    snapshots = [snapshot_to_metrics(r) for r in rows]
    return predict_trend(snapshots, backend=backend)
