"""
GEO 平台数据模型基础设施
基于 AIAdPlacer 范式改造：剥离 OOH 媒体模型，只保留 Base/engine/get_db + GEO 模型注册。
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI Depends 注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── 导入 GEO 模型（必须放在 Base 定义之后，使其进入 Base.metadata）
# models/geo.py 使用 `from app.models import Base`，这里再 import 它触发模型注册
from app.models.geo import (  # noqa: E402,F401
    Tenant, Brand, User,
    QuestionScenario, IntentQuery,
    KnowledgeUnit,
    ContentPiece,
    Competitor, MonitorSnapshot,
    SEOResource,
    GeoTask,
    # 商业版 8 步工作流扩展
    ImageCategory, ImageAsset,
    DistillKeyword,
    SocialMediaAccount,
    WritingTask,
    FeedTask,
)


def init_db():
    """初始化数据库表（启动时调用一次即可）"""
    Base.metadata.create_all(bind=engine)
    print(f"✅ GEO 数据库表初始化完成（{len(Base.metadata.tables)} 张表）→ {settings.DATABASE_URL.split('@')[-1]}")


if __name__ == "__main__":
    init_db()
