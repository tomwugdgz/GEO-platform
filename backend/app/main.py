"""
GEO 平台 FastAPI 入口 — 基于 AIAdPlacer 改造
端口 5006，只注册 GEO 路由（OOH 旧路由全部剥离，文件保留但不 import）
"""
import sys
import types
import os

# ── Windows 兼容：mock pwd 模块 ─────────────────────
sys.modules["pwd"] = types.ModuleType("pwd")
os.environ.setdefault("USERNAME", "user")
os.environ.setdefault("USER", "user")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import init_db

# ── 路由导入（仅 GEO 路由，OOH 全部剥离）──────────────
from app.api.auth_routes import router as auth_router
from app.api.tenants_routes import router as tenants_router
from app.api.intent_routes import router as geo_intent_router
from app.api.knowledge_routes import router as geo_knowledge_router
from app.api.content_routes import router as geo_content_router
from app.api.monitor_routes import router as geo_monitor_router
from app.api.business_routes import router as business_router
from app.api.diagnosis_routes import router as diagnosis_router
from app.api.multimodal_routes import router as multimodal_router
from app.api.competitor_routes import router as competitor_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 路由注册 ─────────────────────────────────────────────
app.include_router(auth_router, prefix="/api/v2/auth", tags=["认证"])
app.include_router(tenants_router, prefix="/api/v2/tenants", tags=["租户管理"])
app.include_router(geo_intent_router, prefix="/api/v2/geo/intent", tags=["GEO 意图洞察"])
app.include_router(geo_knowledge_router, prefix="/api/v2/geo/knowledge", tags=["GEO 品牌知识库"])
app.include_router(geo_content_router, prefix="/api/v2/geo/content", tags=["GEO 内容生产"])
app.include_router(geo_monitor_router, prefix="/api/v2/geo/monitor", tags=["GEO 监测看板"])
app.include_router(business_router, prefix="/api/v2", tags=["商业工作流"])
app.include_router(diagnosis_router, prefix="/api/v2/geo/diagnosis", tags=["品牌GEO诊断"])
app.include_router(multimodal_router, prefix="/api/v2/geo/multimodal", tags=["多模态诊断"])
app.include_router(competitor_router, prefix="/api/v2/geo/competitor", tags=["竞品逆向"])


@app.on_event("startup")
async def startup():
    init_db()
    # 强制展开 FastAPI 0.141.1 的 _IncludedRouter 懒加载路由
    # 通过生成 openapi schema 触发所有路由展开到 app.router.routes
    app.openapi()
    route_count = sum(1 for r in app.router.routes if hasattr(r, 'path'))
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 已启动")
    print(f"📍 路由总数: {route_count}")
    print(f"📍 API文档: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"🎯 多租户: POST /api/v2/tenants")
    print(f"🔍 意图洞察: POST /api/v2/geo/intent/seed")
    print(f"📚 知识库: POST /api/v2/geo/knowledge/units")
    print(f"✍️ 内容生产: POST /api/v2/geo/content/generate")
    print(f"📊 监测看板: GET /api/v2/geo/monitor/board")
    print(f"🎯 品牌诊断: POST /api/v2/geo/diagnosis/start")
    print(f"🖼️ 多模态诊断: POST /api/v2/geo/multimodal/image/analyze")
    print(f"🔍 竞品逆向: POST /api/v2/geo/competitor/analyze")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "GEO 平台",
        "version": settings.APP_VERSION,
        "port": settings.PORT,
    }
