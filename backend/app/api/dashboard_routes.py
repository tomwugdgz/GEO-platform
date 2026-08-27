from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from uuid import UUID

from app.models import get_db, Placement, Campaign, MediaResource

router = APIRouter()


@router.get("/dashboard/overview")
async def attribution_dashboard_overview(
    campaign_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
):
    """效果归因看板 — 总览"""
    query = db.query(Placement)
    if campaign_id:
        query = query.filter(Placement.campaign_id == campaign_id)

    placements = query.all()

    total_impressions = sum(p.impressions or 0 for p in placements)
    total_clicks = sum(p.clicks or 0 for p in placements)
    total_conversions = sum(p.conversions or 0 for p in placements)
    total_cost = sum(float(p.cost or 0) for p in placements)

    ctr = total_clicks / max(total_impressions, 1) * 100
    cvr = total_conversions / max(total_clicks, 1) * 100
    cpa = total_cost / max(total_conversions, 1)
    roi = (total_conversions * 50 - total_cost) / max(total_cost, 1) * 100  # 假设转化价值50元

    return {
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "total_conversions": total_conversions,
        "total_cost": round(total_cost, 2),
        "ctr": round(ctr, 2),
        "cvr": round(cvr, 2),
        "cpa": round(cpa, 2),
        "roi": round(roi, 2),
    }


@router.get("/dashboard/media-performance")
async def media_performance(
    campaign_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
):
    """效果归因看板 — 媒体表现"""
    query = db.query(
        Placement.media_id,
        MediaResource.name,
        MediaResource.category,
        func.sum(Placement.impressions).label("total_imp"),
        func.sum(Placement.clicks).label("total_clk"),
        func.sum(Placement.conversions).label("total_conv"),
        func.sum(Placement.cost).label("total_cost"),
    ).join(MediaResource, Placement.media_id == MediaResource.id)

    if campaign_id:
        query = query.filter(Placement.campaign_id == campaign_id)

    results = query.group_by(Placement.media_id, MediaResource.name, MediaResource.category).all()

    performance = []
    for r in results:
        cost = float(r.total_cost or 0)
        conv = int(r.total_conv or 0)
        imp = int(r.total_imp or 0)
        clk = int(r.total_clk or 0)

        performance.append({
            "media_id": str(r.media_id),
            "media_name": r.name,
            "category": r.category,
            "impressions": imp,
            "clicks": clk,
            "conversions": conv,
            "cost": round(cost, 2),
            "ctr": round(clk / max(imp, 1) * 100, 2),
            "cvr": round(conv / max(clk, 1) * 100, 2),
            "cpa": round(cost / max(conv, 1), 2),
        })

    return performance


@router.get("/dashboard/timeline")
async def timeline_performance(
    campaign_id: Optional[UUID] = Query(None),
    days: int = Query(30),
    db: Session = Depends(get_db),
):
    """效果归因看板 — 时间线表现"""
    from datetime import datetime, timedelta

    base_date = datetime.utcnow().date() - timedelta(days=days)
    query = db.query(Placement).filter(Placement.date >= base_date)
    if campaign_id:
        query = query.filter(Placement.campaign_id == campaign_id)

    placements = query.all()

    # 按日期聚合
    daily: dict = {}
    for p in placements:
        date_str = p.date.isoformat()
        if date_str not in daily:
            daily[date_str] = {"date": date_str, "impressions": 0, "clicks": 0, "conversions": 0, "cost": 0}
        daily[date_str]["impressions"] += p.impressions or 0
        daily[date_str]["clicks"] += p.clicks or 0
        daily[date_str]["conversions"] += p.conversions or 0
        daily[date_str]["cost"] += float(p.cost or 0)

    timeline = sorted(daily.values(), key=lambda x: x["date"])
    return timeline


@router.get("/dashboard/funnel")
async def conversion_funnel(
    campaign_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
):
    """效果归因看板 — 转化漏斗"""
    query = db.query(Placement)
    if campaign_id:
        query = query.filter(Placement.campaign_id == campaign_id)

    placements = query.all()

    total_impressions = sum(p.impressions or 0 for p in placements)
    total_clicks = sum(p.clicks or 0 for p in placements)
    total_conversions = sum(p.conversions or 0 for p in placements)

    funnel = [
        {"stage": "曝光 (Impressions)", "count": total_impressions, "rate": 100},
        {"stage": "点击 (Clicks)", "count": total_clicks, "rate": round(total_clicks / max(total_impressions, 1) * 100, 1)},
        {"stage": "转化 (Conversions)", "count": total_conversions, "rate": round(total_conversions / max(total_impressions, 1) * 100, 1)},
    ]

    return funnel


@router.get("/dashboard/roi-trend")
async def roi_trend(
    campaign_id: Optional[UUID] = Query(None),
    days: int = Query(30),
    db: Session = Depends(get_db),
):
    """
    效果归因看板 — 最近 N 天 ROI 趋势与预算消耗对比
    返回每日的 ROI、预算消耗、 impressions、clicks、conversions
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func

    base_date = datetime.utcnow().date() - timedelta(days=days)
    query = db.query(Placement).filter(Placement.date >= base_date)
    if campaign_id:
        query = query.filter(Placement.campaign_id == campaign_id)

    placements = query.all()

    # 按日期聚合
    daily: dict = {}
    for p in placements:
        date_str = p.date.isoformat()
        if date_str not in daily:
            daily[date_str] = {
                "date": date_str,
                "cost": 0.0,
                "impressions": 0,
                "clicks": 0,
                "conversions": 0,
            }
        daily[date_str]["cost"] += float(p.cost or 0)
        daily[date_str]["impressions"] += p.impressions or 0
        daily[date_str]["clicks"] += p.clicks or 0
        daily[date_str]["conversions"] += p.conversions or 0

    # 计算每日 ROI（假设每次转化价值 50 元）
    CONVERSION_VALUE = 50.0
    timeline = []
    for date_str in sorted(daily.keys()):
        d = daily[date_str]
        cost = d["cost"]
        conv_value = d["conversions"] * CONVERSION_VALUE
        roi = ((conv_value - cost) / max(cost, 1)) * 100
        d["roi"] = round(roi, 2)
        d["revenue"] = round(conv_value, 2)
        timeline.append(d)

    return timeline
