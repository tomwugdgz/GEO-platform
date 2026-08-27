from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.models import get_db
from app.services.scheduling_optimizer import scheduling_optimizer
from app.services.competitor_monitor import competitor_monitor

router = APIRouter()


# ========== AI 排期优化 ==========

@router.get("/scheduling/generate")
async def generate_schedule(
    budget: float = Query(10000, description="总预算"),
    days: int = Query(7, description="投放天数"),
    media_ids: Optional[str] = Query(None, description="媒体 ID 列表，逗号分隔"),
    campaign_id: Optional[str] = Query(None, description="关联投放计划 ID"),
    db: Session = Depends(get_db),
):
    """AI 智能排期优化 — 生成最佳投放排期"""
    media_id_list = media_ids.split(",") if media_ids else None
    result = scheduling_optimizer.generate_schedule(
        db, campaign_id=campaign_id, budget=budget, days=days, media_ids=media_id_list
    )
    return result


@router.get("/scheduling/optimize")
async def optimize_schedule(
    campaign_id: str = Query(..., description="投放计划 ID"),
    db: Session = Depends(get_db),
):
    """基于历史数据优化排期"""
    result = scheduling_optimizer.optimize_existing(db, campaign_id)
    return result


# ========== 竞品监控报告 ==========

@router.get("/competitor/report")
async def competitor_report(
    competitor_name: str = Query(..., description="竞品名称"),
    brand: Optional[str] = Query(None, description="品牌名称"),
    industry: Optional[str] = Query(None, description="行业"),
    days: int = Query(30, description="监控天数"),
    db: Session = Depends(get_db),
):
    """生成竞品监控报告"""
    report = competitor_monitor.generate_report(
        db, competitor_name=competitor_name, brand=brand, industry=industry, days=days
    )
    return report


@router.get("/competitor/compare")
async def compare_competitors(
    names: str = Query(..., description="竞品名称列表，逗号分隔"),
    days: int = Query(30, description="对比天数"),
    db: Session = Depends(get_db),
):
    """竞品对比分析"""
    competitor_list = [n.strip() for n in names.split(",")]
    result = competitor_monitor.compare_competitors(db, competitor_list, days=days)
    return result
