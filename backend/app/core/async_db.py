"""青柠 Booking — 并行异步引擎与会话。

设计约定（见设计文档 §0.3）：在保留存量**同步** SQLAlchemy 引擎/会话（app/models）
零改动的前提下，新增一个**异步**引擎 + ``AsyncSessionLocal`` 供 Booking 模块使用。
两者共用同一个 ``Base`` 声明基类，因此 async session 可操作同步映射的 ORM 类。

URL 派生规则：将 ``postgresql://`` 替换为 ``postgresql+asyncpg://``。
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings


def _to_async_url(url: str) -> str:
    """把同步 PG URL 转为 asyncpg 异步 URL。"""
    if url.startswith("postgresql+asyncpg"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    # 兜底：其它 scheme 原样返回（不应发生）
    return url


ASYNC_DATABASE_URL: str = _to_async_url(settings.DATABASE_URL)

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
