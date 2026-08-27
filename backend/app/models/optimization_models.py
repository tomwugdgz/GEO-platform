from sqlalchemy import Column, String, Integer, Float, DateTime, Date, JSON, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from app.models import Base
from datetime import datetime
import uuid


class SchedulingOptimization(Base):
    """AI 排期优化结果表"""
    __tablename__ = "scheduling_optimizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=True)
    optimization_date = Column(Date, default=datetime.utcnow().date)
    total_budget = Column(DECIMAL(12, 2))
    days = Column(Integer, default=7)
    slots = Column(JSON, default=list)  # 排期槽位列表
    total_impressions = Column(Integer, default=0)
    total_cost = Column(DECIMAL(12, 2), default=0)
    avg_cpm = Column(Float, default=0)
    expected_conversions = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class CompetitorMonitor(Base):
    """竞品监控报告表"""
    __tablename__ = "competitor_monitors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_name = Column(String(100), nullable=False)
    brand = Column(String(100))
    industry = Column(String(50))
    monitor_date = Column(Date, default=datetime.utcnow().date)
    media_types = Column(JSON, default=list)  # 使用的媒体类型
    estimated_budget = Column(DECIMAL(12, 2), default=0)
    impression_share = Column(Float, default=0)  # 曝光份额 (%)
    key_locations = Column(JSON, default=list)  # 核心投放区域
    creative_theme = Column(String(200))  # 创意主题
    activity_score = Column(Float, default=0)  # 活跃度 0-100
    created_at = Column(DateTime, default=datetime.utcnow)
