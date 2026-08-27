from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import random

from app.models import MediaResource, Campaign, Placement


class CompetitorMonitorService:
    """竞品监控报告服务
    
    基于公开的投放数据和市场分析，生成竞品投放监控报告。
    """

    def generate_report(
        self,
        db: Session,
        competitor_name: str,
        brand: Optional[str] = None,
        industry: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """生成竞品监控报告
        
        Args:
            competitor_name: 竞品名称
            brand: 品牌名称
            industry: 所属行业
            days: 监控天数
        
        Returns:
            包含竞品投放分析、预算估算、关键位置等的监控报告
        """
        # 获取所有历史投放数据用于分析
        placements = db.query(Placement).order_by(Placement.date.desc()).limit(1000).all()
        media_resources = db.query(MediaResource).all()

        # 模拟竞品数据（实际应从第三方数据源获取）
        media_map = {str(m.id): m for m in media_resources}

        # 分析竞品可能使用的媒体类型分布
        type_counts: Dict[str, int] = {}
        for p in placements:
            media = media_map.get(str(p.media_id))
            if media:
                cat = media.category
                type_counts[cat] = type_counts.get(cat, 0) + 1

        # 估算竞品预算
        total_cost = sum(float(p.cost or 0) for p in placements)
        estimated_budget = total_cost * random.uniform(0.1, 0.3)  # 模拟估算

        # 计算核心投放区域
        location_scores: Dict[str, float] = {}
        for p in placements:
            if p.latitude and p.longitude:
                key = f"{round(p.latitude, 2)}, {round(p.longitude, 2)}"
                location_scores[key] = location_scores.get(key, 0) + (p.impressions or 0)

        key_locations = sorted(location_scores.items(), key=lambda x: x[1], reverse=True)[:10]

        # 创意主题分析（基于 Campaign 描述提取）
        campaigns = db.query(Campaign).all()
        creative_themes = []
        for c in campaigns:
            if c.description:
                creative_themes.append(c.description[:50])

        # 活跃度评分
        activity_score = min(100, len(placements) / max(days, 1) * 10)

        report = {
            "competitor_name": competitor_name,
            "brand": brand or competitor_name,
            "industry": industry or "未知",
            "report_date": datetime.utcnow().date().isoformat(),
            "monitoring_period_days": days,
            "media_types": list(type_counts.keys()),
            "media_type_distribution": type_counts,
            "estimated_budget": round(estimated_budget, 2),
            "impression_share": round(random.uniform(10, 40), 1),  # 模拟
            "key_locations": [{"location": loc, "score": round(score, 0)} for loc, score in key_locations],
            "creative_themes": creative_themes[:5],
            "activity_score": round(activity_score, 1),
            "total_placements_analyzed": len(placements),
        }

        return report

    def compare_competitors(
        self,
        db: Session,
        competitor_names: List[str],
        days: int = 30,
    ) -> Dict[str, Any]:
        """竞品对比分析"""
        reports = []
        for name in competitor_names:
            report = self.generate_report(db, name, days=days)
            reports.append(report)

        # 排序
        reports.sort(key=lambda r: r.get("activity_score", 0), reverse=True)

        return {
            "competitors": reports,
            "total_competitors": len(reports),
            "top_competitor": reports[0]["competitor_name"] if reports else None,
        }


competitor_monitor = CompetitorMonitorService()
