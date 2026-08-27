"""
意图洞察路由 — GEO 模块①
v1 占位实现：提供 CRUD 骨架 + 触发挖掘的异步任务接口
Phase B 接入 LangGraph intent_miner agent（封装 last30days-cn + WebSearch）
"""
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.models import get_db, IntentQuery, QuestionScenario, GeoTask

router = APIRouter()


# ── Pydantic schemas ─────────────────────────────────────
class IntentQueryCreate(BaseModel):
    brand_id: str
    seed_keyword: str
    question_text: str
    platform_source: Optional[str] = None
    discovered_via: str = "websearch"
    intent_type: Optional[str] = None
    search_volume: int = 0
    scenario_id: Optional[str] = None
    confidence: float = 0.5


class IntentQueryOut(BaseModel):
    id: str
    tenant_id: str
    brand_id: str
    seed_keyword: str
    question_text: str
    platform_source: Optional[str]
    discovered_via: str
    intent_type: Optional[str]
    search_volume: int
    scenario_id: Optional[str]
    status: str
    confidence: float
    created_at: datetime


class ScenarioCreate(BaseModel):
    brand_id: str
    title: str
    intent_cluster: Optional[str] = None
    traffic_gap_score: float = 0.0
    priority: str = "medium"
    related_queries: list[str] = []
    recommended_angle: Optional[str] = None
    confidence: float = 0.5


class ScenarioOut(BaseModel):
    id: str
    tenant_id: str
    brand_id: str
    title: str
    intent_cluster: Optional[str]
    traffic_gap_score: float
    priority: str
    related_queries: list
    recommended_angle: Optional[str]
    confidence: float
    created_at: datetime


class MineTrigger(BaseModel):
    brand_id: str
    seed_keywords: list[str]
    platforms: list[str] = ["websearch", "last30days"]
    top_k: int = Query(default=50, ge=1, le=200)


# ── 提交种子词 / 手动录入问题 ────────────────────────────
@router.post("/queries", response_model=IntentQueryOut)
def create_intent_query(
    tenant_id: str,
    payload: IntentQueryCreate,
    db: Session = Depends(get_db),
):
    q = IntentQuery(
        tenant_id=tenant_id,
        brand_id=tenant_id,  # v1 简化：tenant_id 作 brand_id（Phase B 改从 payload 取）
        seed_keyword=payload.seed_keyword,
        question_text=payload.question_text,
        platform_source=payload.platform_source,
        discovered_via=payload.discovered_via,
        intent_type=payload.intent_type,
        search_volume=payload.search_volume,
        scenario_id=payload.scenario_id,
        confidence=payload.confidence,
    )
    db.add(q); db.commit(); db.refresh(q)
    return IntentQueryOut(
        id=str(q.id), tenant_id=str(q.tenant_id), brand_id=str(q.brand_id),
        seed_keyword=q.seed_keyword, question_text=q.question_text,
        platform_source=q.platform_source, discovered_via=q.discovered_via,
        intent_type=q.intent_type, search_volume=q.search_volume,
        scenario_id=str(q.scenario_id) if q.scenario_id else None,
        status=q.status, confidence=q.confidence, created_at=q.created_at,
    )


# ── 查询问题列表 ─────────────────────────────────────────
@router.get("/queries", response_model=list[IntentQueryOut])
def list_intent_queries(
    tenant_id: str,
    brand_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(IntentQuery).filter(IntentQuery.tenant_id == tenant_id)
    if brand_id:
        query = query.filter(IntentQuery.brand_id == brand_id)
    queries = query.order_by(IntentQuery.created_at.desc()).offset(offset).limit(limit).all()
    return [
        IntentQueryOut(
            id=str(q.id), tenant_id=str(q.tenant_id), brand_id=str(q.brand_id),
            seed_keyword=q.seed_keyword, question_text=q.question_text,
            platform_source=q.platform_source, discovered_via=q.discovered_via,
            intent_type=q.intent_type, search_volume=q.search_volume,
            scenario_id=str(q.scenario_id) if q.scenario_id else None,
            status=q.status, confidence=q.confidence, created_at=q.created_at,
        )
        for q in queries
    ]


# ── 查询场景地图 ─────────────────────────────────────────
@router.get("/scenarios", response_model=list[ScenarioOut])
def list_scenarios(
    tenant_id: str,
    brand_id: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(QuestionScenario).filter(QuestionScenario.tenant_id == tenant_id)
    if brand_id:
        query = query.filter(QuestionScenario.brand_id == brand_id)
    scenarios = query.order_by(
        QuestionScenario.traffic_gap_score.desc()
    ).offset(offset).limit(limit).all()
    return [
        ScenarioOut(
            id=str(s.id), tenant_id=str(s.tenant_id), brand_id=str(s.brand_id),
            title=s.title, intent_cluster=s.intent_cluster,
            traffic_gap_score=s.traffic_gap_score or 0.0,
            priority=s.priority or "medium",
            related_queries=s.related_queries or [],
            recommended_angle=s.recommended_angle,
            confidence=s.confidence or 0.5,
            created_at=s.created_at,
        )
        for s in scenarios
    ]


# ── 创建场景 ─────────────────────────────────────────────
@router.post("/scenarios", response_model=ScenarioOut)
def create_scenario(
    tenant_id: str,
    payload: ScenarioCreate,
    db: Session = Depends(get_db),
):
    s = QuestionScenario(
        tenant_id=tenant_id,
        brand_id=payload.brand_id,
        title=payload.title,
        intent_cluster=payload.intent_cluster,
        traffic_gap_score=payload.traffic_gap_score,
        priority=payload.priority,
        related_queries=payload.related_queries,
        recommended_angle=payload.recommended_angle,
        confidence=payload.confidence,
    )
    db.add(s); db.commit(); db.refresh(s)
    return ScenarioOut(
        id=str(s.id), tenant_id=str(s.tenant_id), brand_id=str(s.brand_id),
        title=s.title, intent_cluster=s.intent_cluster,
        traffic_gap_score=s.traffic_gap_score or 0.0,
        priority=s.priority or "medium",
        related_queries=s.related_queries or [],
        recommended_angle=s.recommended_angle,
        confidence=s.confidence or 0.5,
        created_at=s.created_at,
    )


# ── 触发意图挖掘（异步任务占位）──────────────────────────
@router.post("/mine")
async def trigger_intent_mining(
    tenant_id: str,
    payload: MineTrigger,
    db: Session = Depends(get_db),
):
    """
    触发意图挖掘任务（v1 占位，Phase B 实现）
    实现要点：
    1. 创建 GeoTask 记录（task_type="intent_mine"）
    2. 调用 LangGraph intent_miner agent
    3. 封装 last30days-cn + WebSearch 做种子词拓展
    4. 写入 IntentQuery + QuestionScenario
    """
    task = GeoTask(
        tenant_id=tenant_id,
        task_type="intent_mine",
        payload={
            "brand_id": payload.brand_id,
            "seed_keywords": payload.seed_keywords,
            "platforms": payload.platforms,
            "top_k": payload.top_k,
        },
        status="pending",
    )
    db.add(task); db.commit(); db.refresh(task)
    return {
        "status": "queued",
        "task_id": str(task.id),
        "message": "意图挖掘任务已提交（v1 占位，Phase B 接入 LangGraph Agent）",
        "tenant_id": tenant_id,
        "seed_keywords_count": len(payload.seed_keywords),
        "platforms": payload.platforms,
    }
