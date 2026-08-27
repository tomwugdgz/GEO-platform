"""
监测看板路由 — GEO 模块④（多平台提及率/首推率/引用来源/竞品对比/趋势追踪）
v1 占位实现：提供 CRUD 骨架 + 监测触发接口 + 看板聚合接口
Phase E 接入 LangGraph monitor agent（封装 geo-cn 17 平台查询 + 8 维评分）
"""
from datetime import datetime, date
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Any

from app.models import get_db, MonitorSnapshot, Competitor, GeoTask

router = APIRouter()


# ── Pydantic schemas ─────────────────────────────────────
class SnapshotCreate(BaseModel):
    brand_id: str
    platform: str
    mention_rate: float = 0.0
    first_rec_rate: float = 0.0
    entity_relevance_score: float = 0.0
    cross_model_consistency: float = 0.0
    citation_sources: list[str] = []
    top_questions: list[str] = []
    snapshot_date: date
    competitor_id: Optional[str] = None  # null = 自家


class SnapshotOut(BaseModel):
    id: str
    tenant_id: str
    brand_id: str
    platform: str
    mention_rate: float
    first_rec_rate: float
    entity_relevance_score: float
    cross_model_consistency: float
    citation_sources: list
    top_questions: list
    snapshot_date: date
    competitor_id: Optional[str]


class SnapshotTrigger(BaseModel):
    brand_id: str
    platforms: list[str] = []  # 空 = 全部 17 平台
    competitor_ids: list[str] = []


class BoardData(BaseModel):
    brand_id: str
    platform: str
    mention_rate_avg: float
    first_rec_rate_avg: float
    entity_relevance_avg: float
    cross_model_consistency_avg: float
    snapshot_count: int
    latest_date: Optional[date]


class BoardResponse(BaseModel):
    tenant_id: str
    brand_id: str
    boards: list[BoardData]
    period_start: Optional[date]
    period_end: Optional[date]


class TrendPoint(BaseModel):
    date: date
    mention_rate: float
    first_rec_rate: float


class TrendResponse(BaseModel):
    brand_id: str
    platform: str
    trend: list[TrendPoint]


# ── 创建监测快照 ─────────────────────────────────────────
@router.post("/snapshots", response_model=SnapshotOut)
def create_snapshot(
    tenant_id: str,
    payload: SnapshotCreate,
    db: Session = Depends(get_db),
):
    """创建单条监测快照（v1 手动录入，Phase E 接入自动监测）"""
    s = MonitorSnapshot(
        tenant_id=tenant_id,
        brand_id=payload.brand_id,
        platform=payload.platform,
        mention_rate=payload.mention_rate,
        first_rec_rate=payload.first_rec_rate,
        entity_relevance_score=payload.entity_relevance_score,
        cross_model_consistency=payload.cross_model_consistency,
        citation_sources=payload.citation_sources,
        top_questions=payload.top_questions,
        snapshot_date=payload.snapshot_date,
        competitor_id=payload.competitor_id,
    )
    db.add(s); db.commit(); db.refresh(s)

    return SnapshotOut(
        id=str(s.id),
        tenant_id=str(s.tenant_id),
        brand_id=str(s.brand_id),
        platform=s.platform,
        mention_rate=s.mention_rate,
        first_rec_rate=s.first_rec_rate,
        entity_relevance_score=s.entity_relevance_score,
        cross_model_consistency=s.cross_model_consistency,
        citation_sources=s.citation_sources or [],
        top_questions=s.top_questions or [],
        snapshot_date=s.snapshot_date,
        competitor_id=str(s.competitor_id) if s.competitor_id else None,
    )


# ── 查询快照列表 ─────────────────────────────────────────
@router.get("/snapshots", response_model=list[SnapshotOut])
def list_snapshots(
    tenant_id: str,
    brand_id: Optional[str] = Query(default=None),
    platform: Optional[str] = Query(default=None),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(MonitorSnapshot).filter(MonitorSnapshot.tenant_id == tenant_id)
    if brand_id:
        query = query.filter(MonitorSnapshot.brand_id == brand_id)
    if platform:
        query = query.filter(MonitorSnapshot.platform == platform)
    if start_date:
        query = query.filter(MonitorSnapshot.snapshot_date >= start_date)
    if end_date:
        query = query.filter(MonitorSnapshot.snapshot_date <= end_date)
    snapshots = query.order_by(
        MonitorSnapshot.snapshot_date.desc()
    ).offset(offset).limit(limit).all()

    return [
        SnapshotOut(
            id=str(s.id),
            tenant_id=str(s.tenant_id),
            brand_id=str(s.brand_id),
            platform=s.platform,
            mention_rate=s.mention_rate,
            first_rec_rate=s.first_rec_rate,
            entity_relevance_score=s.entity_relevance_score,
            cross_model_consistency=s.cross_model_consistency,
            citation_sources=s.citation_sources or [],
            top_questions=s.top_questions or [],
            snapshot_date=s.snapshot_date,
            competitor_id=str(s.competitor_id) if s.competitor_id else None,
        )
        for s in snapshots
    ]


# ── 触发监测任务（异步）──────────────────────────────────
@router.post("/scan")
async def trigger_monitor_scan(
    tenant_id: str,
    payload: SnapshotTrigger,
    db: Session = Depends(get_db),
):
    """
    触发跨平台监测扫描（v1 占位，Phase E 实现）
    实现要点：
    1. 创建 GeoTask 记录（task_type="monitor_scan"）
    2. 调用 LangGraph monitor agent
    3. 对 17 个 AI 平台逐个用 WebSearch/last30days 查询
    4. 计算 mention_rate / first_rec_rate / entity_relevance / cross_model_consistency
    5. 写入 MonitorSnapshot
    """
    task = GeoTask(
        tenant_id=tenant_id,
        task_type="monitor_scan",
        payload={
            "brand_id": payload.brand_id,
            "platforms": payload.platforms,
            "competitor_ids": payload.competitor_ids,
        },
        status="pending",
    )
    db.add(task); db.commit(); db.refresh(task)

    return {
        "status": "queued",
        "task_id": str(task.id),
        "message": "监测扫描任务已提交（v1 占位，Phase E 接入 LangGraph Agent + 17 平台查询）",
        "tenant_id": tenant_id,
        "brand_id": payload.brand_id,
        "platforms_count": len(payload.platforms) if payload.platforms else 17,
    }


# ── 看板聚合数据 ─────────────────────────────────────────
@router.get("/board", response_model=BoardResponse)
def get_monitor_board(
    tenant_id: str,
    brand_id: str,
    period_start: Optional[date] = Query(default=None),
    period_end: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    看板聚合：按平台分组，计算均值
    Phase E 实现：接入缓存 + 异步刷新
    """
    query = db.query(MonitorSnapshot).filter(
        MonitorSnapshot.tenant_id == tenant_id,
        MonitorSnapshot.brand_id == brand_id,
        MonitorSnapshot.competitor_id.is_(None),  # 只聚合自家数据
    )
    if period_start:
        query = query.filter(MonitorSnapshot.snapshot_date >= period_start)
    if period_end:
        query = query.filter(MonitorSnapshot.snapshot_date <= period_end)
    snapshots = query.all()

    # 按平台分组聚合
    platform_groups: dict[str, list[MonitorSnapshot]] = {}
    for s in snapshots:
        platform_groups.setdefault(s.platform, []).append(s)

    boards = []
    for platform, group in platform_groups.items():
        mention_rates = [s.mention_rate for s in group]
        first_rec_rates = [s.first_rec_rate for s in group]
        entity_scores = [s.entity_relevance_score for s in group]
        consistency_scores = [s.cross_model_consistency for s in group]

        boards.append(BoardData(
            brand_id=brand_id,
            platform=platform,
            mention_rate_avg=sum(mention_rates) / len(mention_rates) if mention_rates else 0,
            first_rec_rate_avg=sum(first_rec_rates) / len(first_rec_rates) if first_rec_rates else 0,
            entity_relevance_avg=sum(entity_scores) / len(entity_scores) if entity_scores else 0,
            cross_model_consistency_avg=sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0,
            snapshot_count=len(group),
            latest_date=max(s.snapshot_date for s in group) if group else None,
        ))

    # 按 mention_rate_avg 降序
    boards.sort(key=lambda b: b.mention_rate_avg, reverse=True)

    return BoardResponse(
        tenant_id=tenant_id,
        brand_id=brand_id,
        boards=boards,
        period_start=period_start,
        period_end=period_end,
    )


# ── 趋势追踪 ─────────────────────────────────────────────
@router.get("/trend", response_model=TrendResponse)
def get_monitor_trend(
    tenant_id: str,
    brand_id: str,
    platform: str,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    趋势追踪：按日期排序的提及率/首推率时间序列
    Phase E 实现：接入缓存 + 插值补全缺失日期
    """
    query = db.query(MonitorSnapshot).filter(
        MonitorSnapshot.tenant_id == tenant_id,
        MonitorSnapshot.brand_id == brand_id,
        MonitorSnapshot.platform == platform,
        MonitorSnapshot.competitor_id.is_(None),
    )
    if start_date:
        query = query.filter(MonitorSnapshot.snapshot_date >= start_date)
    if end_date:
        query = query.filter(MonitorSnapshot.snapshot_date <= end_date)
    snapshots = query.order_by(MonitorSnapshot.snapshot_date.asc()).all()

    trend = [
        TrendPoint(
            date=s.snapshot_date,
            mention_rate=s.mention_rate,
            first_rec_rate=s.first_rec_rate,
        )
        for s in snapshots
    ]

    return TrendResponse(
        brand_id=brand_id,
        platform=platform,
        trend=trend,
    )


# ── 竞品对比 ─────────────────────────────────────────────
@router.get("/competitors")
def get_competitor_comparison(
    tenant_id: str,
    brand_id: str,
    platform: Optional[str] = Query(default=None),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    竞品对比：自家 vs 竞品在同一平台的指标对比
    Phase E 实现：接入缓存 + 多维对比矩阵
    """
    # 查询自家数据
    own_query = db.query(MonitorSnapshot).filter(
        MonitorSnapshot.tenant_id == tenant_id,
        MonitorSnapshot.brand_id == brand_id,
        MonitorSnapshot.competitor_id.is_(None),
    )
    if platform:
        own_query = own_query.filter(MonitorSnapshot.platform == platform)
    if start_date:
        own_query = own_query.filter(MonitorSnapshot.snapshot_date >= start_date)
    if end_date:
        own_query = own_query.filter(MonitorSnapshot.snapshot_date <= end_date)
    own_snapshots = own_query.all()

    # 查询竞品数据
    competitor_query = db.query(MonitorSnapshot).filter(
        MonitorSnapshot.tenant_id == tenant_id,
        MonitorSnapshot.brand_id == brand_id,
        MonitorSnapshot.competitor_id.isnot(None),
    )
    if platform:
        competitor_query = competitor_query.filter(MonitorSnapshot.platform == platform)
    if start_date:
        competitor_query = competitor_query.filter(MonitorSnapshot.snapshot_date >= start_date)
    if end_date:
        competitor_query = competitor_query.filter(MonitorSnapshot.snapshot_date <= end_date)
    competitor_snapshots = competitor_query.all()

    # 按竞品分组聚合
    competitor_groups: dict[str, list[MonitorSnapshot]] = {}
    for s in competitor_snapshots:
        cid = str(s.competitor_id)
        competitor_groups.setdefault(cid, []).append(s)

    # 自家均值
    own_mention = sum(s.mention_rate for s in own_snapshots) / len(own_snapshots) if own_snapshots else 0
    own_first_rec = sum(s.first_rec_rate for s in own_snapshots) / len(own_snapshots) if own_snapshots else 0

    # 竞品均值
    competitor_data = []
    for cid, group in competitor_groups.items():
        comp_mention = sum(s.mention_rate for s in group) / len(group)
        comp_first_rec = sum(s.first_rec_rate for s in group) / len(group)
        competitor_data.append({
            "competitor_id": cid,
            "mention_rate_avg": comp_mention,
            "first_rec_rate_avg": comp_first_rec,
            "snapshot_count": len(group),
            "gap_vs_own": {
                "mention_rate": comp_mention - own_mention,
                "first_rec_rate": comp_first_rec - own_first_rec,
            },
        })

    return {
        "tenant_id": tenant_id,
        "brand_id": brand_id,
        "platform": platform,
        "own_metrics": {
            "mention_rate_avg": own_mention,
            "first_rec_rate_avg": own_first_rec,
            "snapshot_count": len(own_snapshots),
        },
        "competitors": competitor_data,
    }
