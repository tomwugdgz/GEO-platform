"""
品牌知识库路由 — GEO 模块②（JSON-LD 结构化语义单元）
v1 占位实现：提供 CRUD 骨架 + 合规校验占位接口
Phase C 接入 LangGraph knowledge_builder agent（封装 geo-cn schema 模板 + 实体抽取）
"""
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Any

from app.models import get_db, KnowledgeUnit

router = APIRouter()


# ── Pydantic schemas ─────────────────────────────────────
class KnowledgeUnitCreate(BaseModel):
    brand_id: str
    unit_type: str  # FAQ / Product / Organization / Article / Breadcrumb / Whitepaper / CaseStudy / ThirdPartyEndorsement / PublicReport
    title: str
    body_md: Optional[str] = None
    json_ld: dict[str, Any]
    source_ref: Optional[str] = None
    cross_validation_source_ids: list[str] = []


class KnowledgeUnitOut(BaseModel):
    id: str
    tenant_id: str
    brand_id: str
    unit_type: str
    title: str
    body_md: Optional[str]
    json_ld: dict
    source_ref: Optional[str]
    cross_validation_source_ids: list
    embedding_id: Optional[str]
    compliance_status: str
    eeat_score: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]


class ValidateRequest(BaseModel):
    check_eeat: bool = True
    check_facts: bool = True


class ValidateResponse(BaseModel):
    unit_id: str
    is_valid: bool
    issues: list[str]
    eeat_breakdown: Optional[dict[str, float]] = None
    suggestions: list[str] = []


# ── 创建知识单元 ─────────────────────────────────────────
@router.post("/units", response_model=KnowledgeUnitOut)
def create_knowledge_unit(
    tenant_id: str,
    payload: KnowledgeUnitCreate,
    db: Session = Depends(get_db),
):
    # v1 简单校验：unit_type 必须在允许列表
    allowed_types = {
        "FAQ", "Product", "Organization", "Article", "Breadcrumb",
        "Whitepaper", "CaseStudy", "ThirdPartyEndorsement", "PublicReport",
    }
    if payload.unit_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"unit_type 必须是 {allowed_types} 之一",
        )

    ku = KnowledgeUnit(
        tenant_id=tenant_id,
        brand_id=payload.brand_id,
        unit_type=payload.unit_type,
        title=payload.title,
        body_md=payload.body_md,
        json_ld=payload.json_ld,
        source_ref=payload.source_ref,
        cross_validation_source_ids=payload.cross_validation_source_ids,
        compliance_status="pending",  # v1 默认待审核
    )
    db.add(ku); db.commit(); db.refresh(ku)

    return KnowledgeUnitOut(
        id=str(ku.id),
        tenant_id=str(ku.tenant_id),
        brand_id=str(ku.brand_id),
        unit_type=ku.unit_type,
        title=ku.title,
        body_md=ku.body_md,
        json_ld=ku.json_ld,
        source_ref=ku.source_ref,
        cross_validation_source_ids=ku.cross_validation_source_ids or [],
        embedding_id=ku.embedding_id,
        compliance_status=ku.compliance_status,
        eeat_score=ku.eeat_score,
        created_at=ku.created_at,
        updated_at=ku.updated_at,
    )


# ── 查询知识单元列表 ─────────────────────────────────────
@router.get("/units", response_model=list[KnowledgeUnitOut])
def list_knowledge_units(
    tenant_id: str,
    brand_id: Optional[str] = Query(default=None),
    unit_type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(KnowledgeUnit).filter(KnowledgeUnit.tenant_id == tenant_id)
    if brand_id:
        query = query.filter(KnowledgeUnit.brand_id == brand_id)
    if unit_type:
        query = query.filter(KnowledgeUnit.unit_type == unit_type)
    units = query.order_by(KnowledgeUnit.created_at.desc()).offset(offset).limit(limit).all()

    return [
        KnowledgeUnitOut(
            id=str(u.id),
            tenant_id=str(u.tenant_id),
            brand_id=str(u.brand_id),
            unit_type=u.unit_type,
            title=u.title,
            body_md=u.body_md,
            json_ld=u.json_ld,
            source_ref=u.source_ref,
            cross_validation_source_ids=u.cross_validation_source_ids or [],
            embedding_id=u.embedding_id,
            compliance_status=u.compliance_status,
            eeat_score=u.eeat_score,
            created_at=u.created_at,
            updated_at=u.updated_at,
        )
        for u in units
    ]


# ── 查询单个知识单元 ─────────────────────────────────────
@router.get("/units/{unit_id}", response_model=KnowledgeUnitOut)
def get_knowledge_unit(
    tenant_id: str,
    unit_id: str,
    db: Session = Depends(get_db),
):
    ku = db.query(KnowledgeUnit).filter(
        KnowledgeUnit.id == unit_id,
        KnowledgeUnit.tenant_id == tenant_id,
    ).first()
    if not ku:
        raise HTTPException(status_code=404, detail="知识单元不存在")

    return KnowledgeUnitOut(
        id=str(ku.id),
        tenant_id=str(ku.tenant_id),
        brand_id=str(ku.brand_id),
        unit_type=ku.unit_type,
        title=ku.title,
        body_md=ku.body_md,
        json_ld=ku.json_ld,
        source_ref=ku.source_ref,
        cross_validation_source_ids=ku.cross_validation_source_ids or [],
        embedding_id=ku.embedding_id,
        compliance_status=ku.compliance_status,
        eeat_score=ku.eeat_score,
        created_at=ku.created_at,
        updated_at=ku.updated_at,
    )


# ── 合规校验（v1 占位）───────────────────────────────────
@router.post("/units/{unit_id}/validate", response_model=ValidateResponse)
def validate_knowledge_unit(
    tenant_id: str,
    unit_id: str,
    payload: ValidateRequest,
    db: Session = Depends(get_db),
):
    """
    合规校验接口（v1 占位，Phase C 实现）
    实现要点：
    1. 调用 LangGraph knowledge_builder agent 的 validate 子图
    2. 复用 geo-cn 技能的合规/敏感词检测
    3. 计算 EEAT 四维得分（Experience/Expertise/Authoritativeness/Trustworthiness）
    4. 检查多源交叉验证（cross_validation_source_ids）
    """
    ku = db.query(KnowledgeUnit).filter(
        KnowledgeUnit.id == unit_id,
        KnowledgeUnit.tenant_id == tenant_id,
    ).first()
    if not ku:
        raise HTTPException(status_code=404, detail="知识单元不存在")

    # v1 占位返回
    return ValidateResponse(
        unit_id=unit_id,
        is_valid=True,
        issues=[],
        eeat_breakdown={
            "experience": 0.8,
            "expertise": 0.7,
            "authoritativeness": 0.6,
            "trustworthiness": 0.9,
        },
        suggestions=["建议补充更多第三方佐证来源"],
    )
