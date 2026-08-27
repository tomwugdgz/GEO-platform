"""
GEO 多租户数据模型
所有 GEO 实体带 tenant_id 实现品牌/客户软隔离；v1 仅 tenant_id 过滤，Phase F 加 RBAC 行级策略。

材料补充（来自 Tom 的 GEO 风口文档）：
- 多源权威信源矩阵（EEAT 可信度）：KnowledgeUnit.unit_type 扩展 Whitepaper/CaseStudy/ThirdPartyEndorsement/PublicReport
- 监测指标：除 mention_rate/first_rec_rate 外，加 entity_relevance_score + cross_model_consistency
- SEO+GEO 双线策略：预留 SEOResource 模型（v1 不启用路由，Phase F 启用时零破坏）
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, Text, Float, Boolean, Integer, DateTime,
    ForeignKey, UniqueConstraint, Index, JSON,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models import Base


# ─────────────────────────────────────────────────────────────
# 1. 租户 & 品牌 & 用户（多租户基座）
# ─────────────────────────────────────────────────────────────

class Tenant(Base):
    """租户（品牌/客户隔离单元）"""
    __tablename__ = "geo_tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(64), unique=True, nullable=False, index=True)   # URL 友好名
    name = Column(String(128), nullable=False)
    plan = Column(String(16), nullable=False, default="free")            # free / pro / enterprise
    status = Column(String(16), nullable=False, default="active")        # active / suspended
    settings = Column(JSON, default=dict)                                # 租户级配置
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    brands = relationship("Brand", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")


class Brand(Base):
    """品牌（租户下可多品牌）"""
    __tablename__ = "geo_brands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("geo_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    industry = Column(String(64))
    official_site = Column(String(256))
    description = Column(Text)
    json_ld_profile = Column(JSON, default=dict)                         # 品牌整体 JSON-LD
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="brands")
    competitors = relationship("Competitor", back_populates="brand", cascade="all, delete-orphan")


class User(Base):
    """用户"""
    __tablename__ = "geo_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("geo_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(256), nullable=False, unique=True)
    hashed_pwd = Column(String(256), nullable=False)
    role = Column(String(16), nullable=False, default="member")          # owner / admin / member / viewer
    api_key = Column(String(128), unique=True, index=True)
    status = Column(String(16), nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="users")


# ─────────────────────────────────────────────────────────────
# 2. 意图洞察（模块①）
# ─────────────────────────────────────────────────────────────

class QuestionScenario(Base):
    """品牌问题场景地图 / 流量缺口"""
    __tablename__ = "geo_question_scenarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("geo_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("geo_brands.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(256), nullable=False)                           # 场景标题
    intent_cluster = Column(String(64))                                   # 意图聚类（选型/比价/使用/售后...）
    traffic_gap_score = Column(Float, default=0.0)                        # 流量缺口得分（0-100，越高越有价值）
    priority = Column(String(16), default="medium")                       # high/medium/low
    related_queries = Column(JSON, default=list)                          # 关联问题 ID 列表
    recommended_angle = Column(Text)                                      # 推荐切入角度
    eeat_score = Column(Float)                                            # EEAT 得分（Experience/Expertise/Authoritativeness/Trustworthiness 综合）
    confidence = Column(Float, default=0.5)                               # 推断置信度（v1 种子词+网络研究为间接推断）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    queries = relationship("IntentQuery", back_populates="scenario")


class IntentQuery(Base):
    """问题意图（种子 + 网络研究推断）"""
    __tablename__ = "geo_intent_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("geo_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("geo_brands.id", ondelete="CASCADE"), nullable=False, index=True)
    seed_keyword = Column(String(128), nullable=False)                    # 原始种子词
    question_text = Column(Text, nullable=False)                          # 用户实际提问 / 推断问题
    platform_source = Column(String(32))                                  # 来源平台（微博/知乎/小红书...）
    discovered_via = Column(String(32), default="websearch")              # seed / last30days / websearch / manual
    intent_type = Column(String(32))                                      # informational / transactional / comparison
    search_volume = Column(Integer, default=0)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("geo_question_scenarios.id", ondelete="SET NULL"))
    status = Column(String(16), default="active")                         # active / archived
    confidence = Column(Float, default=0.5)                               # 推断置信度
    eeat_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    scenario = relationship("QuestionScenario", back_populates="queries")


# ─────────────────────────────────────────────────────────────
# 3. 品牌知识库（模块②，JSON-LD 结构化语义单元）
# ─────────────────────────────────────────────────────────────

class KnowledgeUnit(Base):
    """
    知识单元 — 产品参数/案例/资质/白皮书等，自动转为大模型可识别的 JSON-LD
    材料要求"多源交叉印证"，unit_type 支持 9 类覆盖多源信源矩阵
    """
    __tablename__ = "geo_knowledge_units"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("geo_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("geo_brands.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_type = Column(String(32), nullable=False)                        # FAQ/Product/Organization/Article/Breadcrumb/Whitepaper/CaseStudy/ThirdPartyEndorsement/PublicReport
    title = Column(String(256), nullable=False)
    body_md = Column(Text)                                                # Markdown 原文
    json_ld = Column(JSON, nullable=False, default=dict)                  # JSON-LD payload（schema.org 兼容）
    cross_validation_source_ids = Column(JSON, default=list)              # 交叉验证的其他 KU id（多源互相佐证）
    embedding_id = Column(String(256))                                    # ChromaDB 中的 id
    source_ref = Column(String(512))                                      # 来源 URL / 出处
    compliance_status = Column(String(16), default="pending")             # pending / approved / flagged
    eeat_score = Column(Float)                                            # EEAT 综合分
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─────────────────────────────────────────────────────────────
# 4. 内容生产（模块③）
# ─────────────────────────────────────────────────────────────

class ContentPiece(Base):
    """生成内容 — 套用 geo-cn 5 模板 + 8 维评分 + 合规校验"""
    __tablename__ = "geo_content_pieces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("geo_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("geo_brands.id", ondelete="CASCADE"), nullable=False, index=True)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("geo_question_scenarios.id", ondelete="SET NULL"))
    knowledge_unit_ids = Column(JSON, default=list)                       # 引用的知识单元 ID
    title = Column(String(256), nullable=False)
    body_md = Column(Text, nullable=False)
    json_ld = Column(JSON, default=dict)
    template_type = Column(String(32))                                    # 5 模板：faq / comparison / howto / entity / guide
    status = Column(String(16), default="draft")                          # draft/review/approved/published/deferred
    geo_score = Column(Float)                                             # 8 维综合 GEO 得分（0-100）
    geo_scores_8d = Column(JSON, default=dict)                            # 8 维分项得分
    platform_targets = Column(JSON, default=list)                         # 目标 AI 平台
    batch_id = Column(String(64))                                         # 批次 ID（异步批量生成）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    published_at = Column(DateTime)


# ─────────────────────────────────────────────────────────────
# 5. 监测看板（模块④，含材料补充的实体关联度 + 跨模型一致性）
# ─────────────────────────────────────────────────────────────

class Competitor(Base):
    """竞品"""
    __tablename__ = "geo_competitors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("geo_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("geo_brands.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    official_site = Column(String(256))
    json_ld_profile = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    brand = relationship("Brand", back_populates="competitors")


class MonitorSnapshot(Base):
    """
    监测快照 — 每个 (brand, platform, date) 一条
    材料补充：加 entity_relevance_score + cross_model_consistency
    """
    __tablename__ = "geo_monitor_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("geo_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("geo_brands.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(64), nullable=False)                         # 17 个 AI 平台之一
    mention_rate = Column(Float, default=0.0)                             # 提及率（%）
    first_rec_rate = Column(Float, default=0.0)                           # 首推占比（%）
    entity_relevance_score = Column(Float, default=0.0)                   # 实体关联度（材料补充）
    cross_model_consistency = Column(Float, default=0.0)                  # 跨模型一致性（材料补充，0-100）
    citation_sources = Column(JSON, default=list)                         # 引用来源列表
    top_questions = Column(JSON, default=list)                            # 该平台 top 相关问题
    snapshot_date = Column(DateTime, nullable=False)
    competitor_id = Column(UUID(as_uuid=True), ForeignKey("geo_competitors.id", ondelete="SET NULL"))  # 空 = 自家

    __table_args__ = (
        Index("ix_geo_snapshot_brand_platform_date", "brand_id", "platform", "snapshot_date"),
    )


# ─────────────────────────────────────────────────────────────
# 6. SEO 协同（v1 数据模型预留，路由 Phase F 启用）
# ─────────────────────────────────────────────────────────────

class SEOResource(Base):
    """
    SEO 资源 — 网页落地页与 GEO 知识单元的反向关联
    材料明确"SEO+GEO 双线并行，网页承接落地转化"
    v1 仅建表，不注册路由；Phase F 启用时零破坏
    """
    __tablename__ = "geo_seo_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("geo_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("geo_brands.id", ondelete="CASCADE"), nullable=False, index=True)
    page_url = Column(String(512), nullable=False)
    page_title = Column(String(256))
    keywords_json = Column(JSON, default=list)
    rank_position = Column(Integer)                                       # 当前搜索排名
    geo_linkage_to_ku_ids = Column(JSON, default=list)                    # 关联的 KnowledgeUnit id（SEO↔GEO 双向）
    last_crawl_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ─────────────────────────────────────────────────────────────
# 7. 异步任务（D 模块批处理）
# ─────────────────────────────────────────────────────────────

class GeoTask(Base):
    """异步任务（内容批量生成、监测扫描等）"""
    __tablename__ = "geo_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("geo_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    task_type = Column(String(32), nullable=False)                        # intent_mine / content_batch / monitor_scan
    payload = Column(JSON, default=dict)
    status = Column(String(16), default="pending")                        # pending/running/done/failed
    progress = Column(Integer, default=0)                                 # 0-100
    result_summary = Column(Text)
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime)


# ─────────────────────────────────────────────────────────────
# 8. 真实工作流扩展（商业版 8 步 SOP）
# ─────────────────────────────────────────────────────────────

class ImageCategory(Base):
    """图库分类"""
    __tablename__ = "geo_image_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("geo_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("geo_brands.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False)                            # 分类名称
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ImageAsset(Base):
    """图片资产"""
    __tablename__ = "geo_image_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("geo_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("geo_image_categories.id", ondelete="CASCADE"), nullable=False, index=True)
    file_url = Column(String(512), nullable=False)
    file_name = Column(String(256), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DistillKeyword(Base):
    """蒸馏主词（训练主词 + 目标转化词 + AI 蒸馏结果）"""
    __tablename__ = "geo_distill_keywords"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("geo_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("geo_brands.id", ondelete="CASCADE"), nullable=False, index=True)
    training_keyword = Column(String(128), nullable=False)                # 训练主词（如：geo优化）
    conversion_keyword = Column(String(128), nullable=False)              # 目标转化词（品牌名/公司名）
    distilled_queries = Column(JSON, default=list)                        # AI 蒸馏出的问题列表
    selected = Column(Boolean, default=False)                             # 是否选中
    source = Column(String(16), default="ai_distill")                     # ai_distill / manual
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SocialMediaAccount(Base):
    """自媒体账号（12 平台授权）"""
    __tablename__ = "geo_social_media_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("geo_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("geo_brands.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(32), nullable=False)                         # wechat / zhihu / toutiao / douyin / xhs / bilibili / ...
    account_name = Column(String(128), nullable=False)
    account_url = Column(String(256))
    auth_status = Column(String(16), default="pending")                   # pending / authorized / expired
    auth_code = Column(String(128))                                       # GEO助手授权码
    authorized_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class WritingTask(Base):
    """写作任务（选蒸馏词 + 图库 + 知识库 + AI 指令）"""
    __tablename__ = "geo_writing_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("geo_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("geo_brands.id", ondelete="CASCADE"), nullable=False, index=True)
    task_name = Column(String(256), nullable=False)
    keyword_ids = Column(JSON, default=list)                              # 关联的 DistillKeyword id
    category_id = Column(UUID(as_uuid=True), ForeignKey("geo_image_categories.id", ondelete="SET NULL"))
    knowledge_enabled = Column(Boolean, default=False)                    # 是否启用知识库
    content_prompt = Column(Text)                                         # 内容创作指令
    title_prompt = Column(Text)                                           # 标题创作指令
    max_articles = Column(Integer, default=10)                            # AI 创作数量
    status = Column(String(16), default="pending")                        # pending / running / completed
    created_articles = Column(Integer, default=0)                         # 已创作文章数
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)


class FeedTask(Base):
    """投喂任务（选文章分类 + 平台 + 每日限量）"""
    __tablename__ = "geo_feed_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("geo_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("geo_brands.id", ondelete="CASCADE"), nullable=False, index=True)
    task_name = Column(String(256), nullable=False)
    writing_task_id = Column(UUID(as_uuid=True), ForeignKey("geo_writing_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    max_publish_count = Column(Integer, default=10)                       # 任务最大发布量
    daily_limit_per_account = Column(Integer, default=1)                  # 每日/号发布量
    platform_ids = Column(JSON, default=list)                             # 选中的平台账号 ID
    status = Column(String(16), default="pending")                        # pending / running / completed / paused
    published_count = Column(Integer, default=0)                          # 已发布数
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
