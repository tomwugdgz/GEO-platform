from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import numpy as np
from app.models import MediaResource, Placement, Campaign


class AIRecommender:
    """AI智能推荐引擎"""
    
    @staticmethod
    def recommend_media(
        db: Session,
        budget: float,
        location: Optional[Dict[str, float]] = None,
        target_impressions: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        根据预算和位置推荐最佳媒体组合
        """
        query = db.query(MediaResource).filter(MediaResource.status == "available")
        
        # 如果指定了位置，按距离排序
        if location and location.get("lat") and location.get("lng"):
            # 简化实现：按覆盖半径过滤
            # 实际应使用PostGIS计算精确距离
            query = query.filter(
                MediaResource.latitude.isnot(None),
                MediaResource.longitude.isnot(None)
            )
        
        available_media = query.all()
        
        if not available_media:
            return []
        
        # 计算性价比（曝光量/价格）
        media_scores = []
        for media in available_media:
            if media.daily_price and media.daily_price > 0:
                efficiency = media.daily_impressions / float(media.daily_price)
                media_scores.append({
                    "media_id": str(media.id),
                    "name": media.name,
                    "category": media.category,
                    "daily_price": float(media.daily_price),
                    "daily_impressions": media.daily_impressions,
                    "efficiency_score": efficiency,
                    "lat": media.latitude,
                    "lng": media.longitude,
                })
        
        # 按性价比排序
        media_scores.sort(key=lambda x: x["efficiency_score"], reverse=True)
        
        # 预算分配
        recommendations = []
        remaining_budget = budget
        
        for media in media_scores:
            if remaining_budget <= 0:
                break
            
            # 每个媒体至少分配1天预算
            allocation = min(remaining_budget, media["daily_price"])
            days = int(allocation / media["daily_price"]) if media["daily_price"] > 0 else 1
            
            recommendations.append({
                **media,
                "recommended_days": days,
                "budget_allocation": allocation,
                "estimated_impressions": int(media["daily_impressions"] * days),
            })
            
            remaining_budget -= allocation
        
        return recommendations
    
    @staticmethod
    def optimize_budget_allocation(
        db: Session,
        campaign_id: str,
        total_budget: float
    ) -> Dict[str, Any]:
        """
        基于历史数据优化预算分配
        """
        # 获取该计划的历史投放数据
        placements = db.query(
            Placement.media_id,
            func.sum(Placement.impressions).label('total_impressions'),
            func.sum(Placement.clicks).label('total_clicks'),
            func.sum(Placement.conversions).label('total_conversions'),
            func.sum(Placement.cost).label('total_cost')
        ).filter(
            Placement.campaign_id == campaign_id
        ).group_by(Placement.media_id).all()
        
        if not placements:
            return {"message": "无历史数据，按性价比分配"}
        
        # 计算各媒体ROI
        media_roi = []
        for p in placements:
            roi = 0
            if p.total_cost and p.total_cost > 0:
                roi = float(p.total_conversions) / float(p.total_cost)
            
            media_roi.append({
                "media_id": str(p.media_id),
                "roi": roi,
                "total_cost": float(p.total_cost),
                "total_conversions": int(p.total_conversions),
            })
        
        # 按ROI排序
        media_roi.sort(key=lambda x: x["roi"], reverse=True)
        
        # 预算分配（ROI高的获得更多预算）
        total_roi = sum(m["roi"] for m in media_roi)
        if total_roi == 0:
            # 如果都没有ROI，平均分配
            avg_allocation = total_budget / len(media_roi)
            for m in media_roi:
                m["recommended_budget"] = avg_allocation
        else:
            for m in media_roi:
                m["recommended_budget"] = total_budget * (m["roi"] / total_roi)
        
        return {
            "optimization": media_roi,
            "total_budget": total_budget,
            "expected_conversions": sum(
                m["recommended_budget"] * m["roi"] for m in media_roi
            ),
        }
    
    @staticmethod
    def suggest_campaign_strategy(
        db: Session,
        location: Optional[Dict[str, float]] = None,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        基于位置和行业推荐投放策略
        """
        strategy = {
            "recommended_categories": [],
            "optimal_time_slots": [],
            "budget_suggestions": {},
        }
        
        # 根据位置推荐
        if location:
            # 获取周边POI分析
            from app.services.tencent_map import tencent_map_service
            # 简化：直接基于经验规则
            strategy["location_tips"] = f"在坐标({location['lat']}, {location['lng']})附近投放"
            strategy["recommended_categories"] = ["elevator", "billboard"]
        
        # 根据行业推荐
        if industry:
            industry_strategies = {
                "retail": {
                    "categories": ["elevator", "bus_stop", "billboard"],
                    "time_slots": ["morning_rush", "evening_rush"],
                    "budget_focus": "high_traffic_areas"
                },
                "f&b": {
                    "categories": ["elevator", "app"],
                    "time_slots": ["lunch_time", "dinner_time"],
                    "budget_focus": "residential_areas"
                },
                "tech": {
                    "categories": ["app", "web", "elevator"],
                    "time_slots": ["work_hours"],
                    "budget_focus": "business_districts"
                },
            }
            
            if industry in industry_strategies:
                strategy.update(industry_strategies[industry])
        
        return strategy


ai_recommender = AIRecommender()
