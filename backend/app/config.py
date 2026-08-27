"""
GEO 平台配置 — 基于 AIAdPlacer 配置范式改造
端口 5006（避开 5001/5002/5003/5004/5005），新建 geo 库
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

_BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # ── 数据库 ──────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://quantdinger:quantdinger123@127.0.0.1:5432/geo"
    REDIS_URL: str = "redis://127.0.0.1:6379/1"   # DB 1（避开 AIAdPlacer 的 DB 0）

    # ── LLM 配置（复用 AIAdPlacer 范式）────────────────────
    LLM_PROVIDER: str = "ollama"                     # ollama | openai | dashscope
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    GEO_CHAT_MODEL: str = "qwen3.5:9b"               # 默认本地 Qwen3.5-9b
    OLLAMA_EMBED_MODEL: str = "modelscope.cn/bge-m3:latest"

    # OpenAI 兼容网关（DeepSeek / Qwen API / Claude 网关等）
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    # ── ChromaDB（RAG 向量库）────────────────────────────
    CHROMA_PERSIST_DIR: str = str(_BACKEND_DIR / "chroma_data")

    # ── 应用 ────────────────────────────────────────────────
    APP_NAME: str = "GEO 生成式引擎优化平台"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 5006

    # ── GEO 17 平台清单（来自 geo-cn 技能）────────────────
    GEO_PLATFORMS: list[str] = [
        "豆包", "Kimi", "文心一言", "通义千问", "DeepSeek",
        "腾讯元宝", "百度AI搜索", "微信搜一搜", "小红书COLA",
        "智谱清言", "百川智能", "360智脑", "天工AI",
        "星火", "Minimax", "钉钉AI", "飞书AI",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
