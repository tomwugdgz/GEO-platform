from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import random

from app.models import MediaResource, Campaign, Placement


class SchedulingOptimizer:
    """AI 排期优化引擎
    
    基于多目标优化（预算、曝光、时间窗口）生成最佳投放排期。
    """

    def generate_schedule(
        self,
        db: Session,
        campaign_id: Optional[str] = None,
        budget: float = 10000,
        days: int = 7,
        media_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """生成投放排期方案
        
        Args:
            campaign_id: 关联的投放计划 ID
            budget: 总预算
            days: 投放天数
            media_ids: 指定媒体 ID 列表，为空则自动筛选
        
        Returns:
            包含每日排期、预算分配、预期效果的排期方案
        """
        # 查询可用媒体
        query = db.query(MediaResource).filter(MediaResource.status == "available")
        if media_ids:
            from uuid import UUID
            query = query.filter(MediaResource.id.in_([UUID(m) for m in media_ids]))
        
        available_media = query.all()
        if not available_media:
            return {"slots": [], "total_cost": 0, "total_impressions": 0}

        # 按性价比排序
        scored_media = []
        for m in available_media:
            if m.daily_price and m.daily_price > 0:
                score = m.daily_impressions / float(m.daily_price)
                scored_media.append({
                    "media_id": str(m.id),
                    "name": m.name,
                    "category": m.category,
                    "daily_price": float(m.daily_price),
                    "daily_impressions": m.daily_impressions,
                    "score": score,
                })
        
        scored_media.sort(key=lambda x: x["score"], reverse=True)

        # 贪心算法：按性价比分配预算到每日槽位
        slots = []
        remaining_budget = budget
        base_date = datetime.utcnow().date()

        for day_offset in range(days):
            day_budget = budget / days  # 每天平均预算
            day_slots = []

            for media in scored_media:
                if day_budget <= 0:
                    break

                can_afford = int(day_budget / media["daily_price"]) if media["daily_price"] > 0 else 0
                if can_afford >= 1:
                    cost = media["daily_price"]
                    impressions = media["daily_impressions"]

                    # 周末/工作日差异化加权
                    target_date = base_date + timedelta(days=day_offset)
                    is_weekend = target_date.weekday() >= 5
                    weight = 1.1 if is_weekend and media["category"] in ("billboard", "bus_stop") else 1.0

                    day_slots.append({
                        "media_id": media["media_id"],
                        "media_name": media["name"],
                        "category": media["category"],
                        "date": target_date.isoformat(),
                        "cost": cost,
                        "impressions": int(impressions * weight),
                        "cpm": cost / max(impressions, 1) * 1000,
                    })

                    day_budget -= cost

            if day_slots:
                slots.extend(day_slots)

        total_cost = sum(s["cost"] for s in slots)
        total_impressions = sum(s["impressions"] for s in slots)

        return {
            "slots": slots,
            "days": days,
            "total_budget": budget,
            "total_cost": round(total_cost, 2),
            "total_impressions": total_impressions,
            "avg_cpm": round(total_cost / max(total_impressions, 1) * 1000, 2),
            "remaining_budget": round(budget - total_cost, 2),
            "campaign_id": campaign_id,
        }

    def optimize_existing(
        self,
        db: Session,
        campaign_id: str,
    ) -> Dict[str, Any]:
        """基于历史投放数据优化排期"""
        placements = db.query(Placement).filter(
            Placement.campaign_id == campaign_id
        ).all()

        if not placements:
            return {
                "message": "无历史数据，请先创建投放计划",
                "suggested_actions": ["创建新投放计划", "指定目标预算和天数"],
            }

        # 分析每日效果
        daily_data: Dict[str, Dict[str, float]] = {}
        for p in placements:
            date_str = p.date.isoformat()
            if date_str not in daily_data:
                daily_data[date_str] = {"cost": 0, "impressions": 0, "conversions": 0}
            daily_data[date_str]["cost"] += float(p.cost or 0)
            daily_data[date_str]["impressions"] += p.impressions or 0
            daily_data[date_str]["conversions"] += p.conversions or 0

        # 计算最佳投放时段
        daily_rois = []
        for date_str, data in daily_data.items():
            roi = data["conversions"] / max(data["cost"], 0.01)
            daily_rois.append({
                "date": date_str,
                "cost": round(data["cost"], 2),
                "impressions": data["impressions"],
                "conversions": data["conversions"],
                "roi": round(roi, 4),
            })

        daily_rois.sort(key=lambda x: x["roi"], reverse=True)

        return {
            "daily_analysis": daily_rois,
            "top_dates": [d["date"] for d in daily_rois[:3]],
            "recommendation": f"建议在 ROI 最高的日期 {daily_rois[0]['date']} 增加投放预算",
        }


scheduling_optimizer = SchedulingOptimizer()
