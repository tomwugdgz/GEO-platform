"""
内容生产路由 — GEO 模块③（批量生成符合大模型引用偏好的合规原创内容）
v1 占位实现：提供 CRUD 骨架 + 异步批量生成接口
Phase D 接入 LangGraph content_producer agent（封装 geo-cn 5 模板 + 8 维评分 + 合规校验）
"""
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Any

from app.models import get_db, ContentPiece, GeoTask

router = APIRouter()


# ── Pydantic schemas ─────────────────────────────────────
class ContentGenerateRequest(BaseModel):
    brand_id: str
    scenario_id: Optional[str] = None
    knowledge_unit_ids: list[str] = []
    template_type: str = "guide"  # faq / comparison / howto / entity / guide
    platform_targets: list[str] = []  # 目标 AI 平台（默认全部 17 个）
    batch_size: int = Query(default=10, ge=1, le=100)


class ContentPieceOut(BaseModel):
    id: str
    tenant_id: str
    brand_id: str
    scenario_id: Optional[str]
    knowledge_unit_ids: list
    title: str
    body_md: str
    json_ld: dict
    template_type: str
    status: str
    geo_score: Optional[float]
    geo_scores_8d: dict
    platform_targets: list
    batch_id: Optional[str]
    created_at: datetime
    published_at: Optional[datetime]


class ApproveRequest(BaseModel):
    status: str = "approved"  # approved / rejected / deferred


class ScoreDetail(BaseModel):
    dimension: str
    score: float
    reasoning: str


class ScoreResponse(BaseModel):
    content_id: str
    geo_score: float
    scores_8d: dict[str, float]
    details: list[ScoreDetail]


# ── 触发批量生成（异步任务）──────────────────────────────
@router.post("/generate")
async def trigger_content_generation(
    tenant_id: str,
    payload: ContentGenerateRequest,
    db: Session = Depends(get_db),
):
    """
    触发批量内容生成（v1 占位，Phase D 实现）
    实现要点：
    1. 创建 GeoTask 记录（task_type="content_batch"）
    2. 调用 LangGraph content_producer agent
    3. 套用 geo-cn 5 模板 + 8 维评分 + 合规校验
    4. 异步队列批量生成（绕过 Qwen 慢阻塞）
    5. 写入 ContentPiece
    """
    task = GeoTask(
        tenant_id=tenant_id,
        task_type="content_batch",
        payload={
            "brand_id": payload.brand_id,
            "scenario_id": payload.scenario_id,
            "knowledge_unit_ids": payload.knowledge_unit_ids,
            "template_type": payload.template_type,
            "platform_targets": payload.platform_targets,
            "batch_size": payload.batch_size,
        },
        status="pending",
    )
    db.add(task); db.commit(); db.refresh(task)

    batch_id = f"batch-{uuid4().hex[:16]}"
    return {
        "status": "queued",
        "task_id": str(task.id),
        "batch_id": batch_id,
        "message": "批量内容生成任务已提交（v1 占位，Phase D 接入 LangGraph Agent + 异步队列）",
        "tenant_id": tenant_id,
        "template_type": payload.template_type,
        "batch_size": payload.batch_size,
    }


# ── 查询内容列表 ─────────────────────────────────────────
@router.get("/pieces", response_model=list[ContentPieceOut])
def list_content_pieces(
    tenant_id: str,
    brand_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    template_type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(ContentPiece).filter(ContentPiece.tenant_id == tenant_id)
    if brand_id:
        query = query.filter(ContentPiece.brand_id == brand_id)
    if status:
        query = query.filter(ContentPiece.status == status)
    if template_type:
        query = query.filter(ContentPiece.template_type == template_type)
    pieces = query.order_by(ContentPiece.created_at.desc()).offset(offset).limit(limit).all()

    return [
        ContentPieceOut(
            id=str(p.id),
            tenant_id=str(p.tenant_id),
            brand_id=str(p.brand_id),
            scenario_id=str(p.scenario_id) if p.scenario_id else None,
            knowledge_unit_ids=p.knowledge_unit_ids or [],
            title=p.title,
            body_md=p.body_md,
            json_ld=p.json_ld,
            template_type=p.template_type,
            status=p.status,
            geo_score=p.geo_score,
            geo_scores_8d=p.geo_scores_8d or {},
            platform_targets=p.platform_targets or [],
            batch_id=p.batch_id,
            created_at=p.created_at,
            published_at=p.published_at,
        )
        for p in pieces
    ]


# ── 查询单个内容 ─────────────────────────────────────────
@router.get("/pieces/{piece_id}", response_model=ContentPieceOut)
def get_content_piece(
    tenant_id: str,
    piece_id: str,
    db: Session = Depends(get_db),
):
    p = db.query(ContentPiece).filter(
        ContentPiece.id == piece_id,
        ContentPiece.tenant_id == tenant_id,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="内容不存在")

    return ContentPieceOut(
        id=str(p.id),
        tenant_id=str(p.tenant_id),
        brand_id=str(p.brand_id),
        scenario_id=str(p.scenario_id) if p.scenario_id else None,
        knowledge_unit_ids=p.knowledge_unit_ids or [],
        title=p.title,
        body_md=p.body_md,
        json_ld=p.json_ld,
        template_type=p.template_type,
        status=p.status,
        geo_score=p.geo_score,
        geo_scores_8d=p.geo_scores_8d or {},
        platform_targets=p.platform_targets or [],
        batch_id=p.batch_id,
        created_at=p.created_at,
        published_at=p.published_at,
    )


# ── 审核内容（v1 占位）───────────────────────────────────
@router.post("/pieces/{piece_id}/approve")
def approve_content_piece(
    tenant_id: str,
    piece_id: str,
    payload: ApproveRequest,
    db: Session = Depends(get_db),
):
    """审核内容（v1 占位，Phase D 实现）"""
    p = db.query(ContentPiece).filter(
        ContentPiece.id == piece_id,
        ContentPiece.tenant_id == tenant_id,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="内容不存在")

    # v1 直接更新状态
    p.status = payload.status
    db.commit()

    return {
        "status": "ok",
        "content_id": piece_id,
        "new_status": payload.status,
    }


# ── 获取 8 维评分详情（v1 占位）─────────────────────────
@router.get("/pieces/{piece_id}/score", response_model=ScoreResponse)
def get_content_score(
    tenant_id: str,
    piece_id: str,
    db: Session = Depends(get_db),
):
    """
    获取内容 8 维评分详情（v1 占位，Phase D 实现）
    8 维：实体权威性 / 数据可追溯 / 结构清晰度 / FAQ 覆盖 / AI 平台适配 / SEO 双轨 / 合规安全 / 社交信号
    """
    p = db.query(ContentPiece).filter(
        ContentPiece.id == piece_id,
        ContentPiece.tenant_id == tenant_id,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="内容不存在")

    # v1 占位返回
    scores_8d = p.geo_scores_8d or {
        "entity_authority": 75.0,
        "data_traceability": 80.0,
        "structure_clarity": 85.0,
        "faq_coverage": 70.0,
        "ai_platform_fit": 78.0,
        "seo_dual_track": 72.0,
        "compliance_safety": 90.0,
        "social_signal": 65.0,
    }

    details = [
        ScoreDetail(
            dimension=dim,
            score=score,
            reasoning="v1 占位评分，Phase D 接入 geo-cn 8 维评分算法",
        )
        for dim, score in scores_8d.items()
    ]

    return ScoreResponse(
        content_id=piece_id,
        geo_score=p.geo_score or sum(scores_8d.values()) / len(scores_8d),
        scores_8d=scores_8d,
        details=details,
    )
