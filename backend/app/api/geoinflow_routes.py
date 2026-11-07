"""
MTO 证据充分性 API —— GEOInflow 借鉴资产的业务接入层
=================================================================================
前缀：/api/v2/mto/evidence（在 app/main.py 注册）

端点：
  GET  /catalog        AI 爬虫身份目录（结构来自 GEOInflow，范围未引入）
  GET  /policy         冻结量化策略 + 零假数据纪律声明
  POST /observation    上报一条爬取观测（自动判定证据状态）
  GET  /observations   查询观测列表
  GET  /report         证据充分性 / 覆盖率 / AI 盲点 / 冻结权重

所有响应统一经 contracts.build_response 封装，携带
data + evidence_state + policy_version + limitations 四要素。
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models import get_db
from app.models.geoinflow_evidence import CrawlerObservation
from app.geoinflow_adapter.catalog import (
    all_entries, filter_entries, find_by_name, parse_declared_ua, summarize,
)
from app.geoinflow_adapter.contracts import build_response
from app.geoinflow_adapter.coverage import compute_coverage
from app.geoinflow_adapter.evidence import (
    EvidenceState, classify_identity, evidence_gap_report, OBSERVATION_ONLY_NOTE,
)
from app.geoinflow_adapter.policy import describe_policy, weight_from_units
from app.geoinflow_adapter.quality import never_fake_banner

router = APIRouter()


def _parse_uuid(v: Optional[str]):
    """宽松解析 UUID，非法值返回 None（与 trend_routes.py 口径一致）。"""
    if not v:
        return None
    try:
        return uuid.UUID(v)
    except Exception:
        return None


class ObservationIn(BaseModel):
    tenant_id: Optional[str] = None
    brand_id: Optional[str] = None
    period_label: Optional[str] = None
    declared_token: Optional[str] = Field(None, description="UA 中声明的产品 token，如 GPTBot")
    purpose: Optional[str] = Field(None, description="ai_search / user_initiated / ai_training / other")
    path: Optional[str] = None
    http_status: Optional[int] = 200
    source: str = "manual"
    official_range_verified: bool = False
    range_snapshot_version: Optional[str] = None
    trusted_ingress: bool = False
    dns_or_edge_evidence: bool = False


@router.get("/catalog")
def get_catalog(
    vendor: Optional[str] = Query(None),
    purpose: Optional[str] = Query(None),
    ai_eligible: Optional[bool] = Query(None),
):
    """查询 AI 爬虫身份目录。注意：仅返回【声明身份】的候选，不含核验结论。"""
    entries = filter_entries(vendor=vendor, purpose=purpose, ai_eligible=ai_eligible)
    return build_response(
        {"summary": summarize(), "entries": entries, "entry_count": len(entries)},
        evidence_state=EvidenceState.OBSERVED.value,
        limitations=[
            "目录名称表示请求声明的身份，核验状态单独判定",
            "官方 IP 范围未引入（range_status=not_imported），不得据此认定请求来源",
            OBSERVATION_ONLY_NOTE,
        ],
    )


@router.get("/policy")
def get_policy():
    """返回冻结量化策略与零假数据纪律（策略哈希可用于导出快照比对）。"""
    return build_response(
        {"policy": describe_policy(), "quality": never_fake_banner()},
        evidence_state=EvidenceState.OBSERVED.value,
        limitations=[
            "系数为 Beta 参数，未经跨行业校准，不构成商业决策依据",
            "本策略描述已观测的 AI 内容访问量，不等同机器信任或成交",
        ],
    )


@router.post("/observation")
def create_observation(payload: ObservationIn, db: Session = Depends(get_db)):
    """上报一条爬取观测；证据状态由状态机判定，不由调用方直接指定。"""
    candidate = None
    if payload.declared_token:
        parsed = parse_declared_ua(payload.declared_token)
        if parsed["candidate_count"] > 0:
            candidate = parsed["candidates"][0]
        else:
            hit = find_by_name(payload.declared_token)
            candidate = hit

    verdict = classify_identity(
        declared_user_agent=payload.declared_token,
        official_range_verified=payload.official_range_verified,
        range_snapshot_version=payload.range_snapshot_version,
        trusted_ingress=payload.trusted_ingress,
        dns_or_edge_evidence=payload.dns_or_edge_evidence,
    )

    row = CrawlerObservation(
        tenant_id=_parse_uuid(payload.tenant_id),
        brand_id=_parse_uuid(payload.brand_id),
        period_label=payload.period_label,
        declared_token=payload.declared_token,
        candidate_identity_id=(candidate or {}).get("id"),
        purpose=payload.purpose or (candidate or {}).get("purpose"),
        path=payload.path,
        http_status=payload.http_status,
        source=payload.source,
        official_range_verified=payload.official_range_verified,
        range_snapshot_version=payload.range_snapshot_version,
        trusted_ingress=payload.trusted_ingress,
        dns_or_edge_evidence=payload.dns_or_edge_evidence,
        evidence_state=verdict["state"],
        can_claim_identity=verdict["can_claim_identity"],
        evidence={"verdict": verdict, "candidate": candidate},
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return build_response(
        {
            "observation_id": str(row.id),
            "evidence_state": verdict["state"],
            "can_claim_identity": verdict["can_claim_identity"],
            "candidate_identity_id": row.candidate_identity_id,
            "verdict": verdict,
        },
        evidence_state=verdict["state"],
        limitations=verdict["limitations"],
    )


@router.get("/observations")
def list_observations(
    tenant_id: Optional[str] = Query(None),
    brand_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """查询观测列表（按观测时间倒序）。"""
    q = db.query(CrawlerObservation)
    if _parse_uuid(tenant_id):
        q = q.filter(CrawlerObservation.tenant_id == _parse_uuid(tenant_id))
    if _parse_uuid(brand_id):
        q = q.filter(CrawlerObservation.brand_id == _parse_uuid(brand_id))
    rows = q.order_by(CrawlerObservation.observed_at.desc()).limit(limit).all()
    return build_response(
        {
            "count": len(rows),
            "observations": [
                {
                    "observation_id": str(r.id),
                    "declared_token": r.declared_token,
                    "candidate_identity_id": r.candidate_identity_id,
                    "purpose": r.purpose,
                    "path": r.path,
                    "http_status": r.http_status,
                    "evidence_state": r.evidence_state,
                    "can_claim_identity": r.can_claim_identity,
                    "observed_at": r.observed_at.isoformat() if r.observed_at else None,
                }
                for r in rows
            ],
        },
        evidence_state=EvidenceState.OBSERVED.value if rows else EvidenceState.MISSING_INPUT.value,
        limitations=[OBSERVATION_ONLY_NOTE],
    )


@router.get("/report")
def evidence_report(
    tenant_id: Optional[str] = Query(None),
    brand_id: Optional[str] = Query(None),
    inventory: Optional[str] = Query(None, description="内容清单路径，逗号分隔；缺省表示未提供"),
    e_search: Optional[int] = Query(None, ge=0),
    e_user: Optional[int] = Query(None, ge=0),
    e_training: Optional[int] = Query(None, ge=0),
    complete_window: bool = Query(False, description="观测窗口是否完整"),
    proved_zero: bool = Query(False, description="是否在完整观测下确证为 0"),
    db: Session = Depends(get_db),
):
    """
    综合证据报告：证据缺口 / 内容覆盖率与 AI 盲点 / 冻结权重。

    纪律：未提供清单时覆盖率返回 missing_input（不返回 0%）；
    证据不完整时权重返回 null（不返回 0）；缺口逐条列出。
    """
    q = db.query(CrawlerObservation)
    if _parse_uuid(tenant_id):
        q = q.filter(CrawlerObservation.tenant_id == _parse_uuid(tenant_id))
    if _parse_uuid(brand_id):
        q = q.filter(CrawlerObservation.brand_id == _parse_uuid(brand_id))
    rows = q.order_by(CrawlerObservation.observed_at.asc()).limit(100000).all()

    inventory_paths: Optional[List[str]] = None
    if inventory is not None:
        inventory_paths = [p.strip() for p in inventory.split(",") if p.strip()]

    observed_paths = [r.path for r in rows if r.path]
    has_range_verification = any(
        r.official_range_verified and bool(r.range_snapshot_version) for r in rows
    )

    gaps = evidence_gap_report(
        has_content_inventory=bool(inventory_paths),
        has_crawl_observations=bool(rows),
        has_range_verification=has_range_verification,
        has_referral_sessions=False,   # 本项目未接入 AI 引荐会话，如实声明
        has_complete_window=complete_window,
    )
    coverage = compute_coverage(inventory_paths, observed_paths)
    weight = weight_from_units(
        e_search, e_user, e_training,
        evidence_complete=complete_window,
        proved_zero=proved_zero,
    )

    overall_state = (
        EvidenceState.OBSERVED.value if gaps["conclusion_ready"]
        else EvidenceState.MISSING_INPUT.value
    )
    return build_response(
        {
            "observation_count": len(rows),
            "evidence_gaps": gaps,
            "coverage": coverage,
            "weight": weight,
            "separate_evidence_required": gaps["separate_evidence_required"],
        },
        evidence_state=overall_state,
        limitations=gaps["gaps"] + coverage["limitations"] + weight["limitations"],
    )
