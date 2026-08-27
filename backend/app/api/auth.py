"""
统一鉴权中间件 — 支持 X-API-Key + Bearer Token 双模式
"""
from fastapi import HTTPException, Depends, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic_settings import BaseSettings
from typing import Optional

# ── 配置 ─────────────────────────────────────────────

class AuthConfig(BaseSettings):
    API_KEY: str = "aiad-2025-placer-token"          # 默认 Key（生产环境必须改）
    JWT_SECRET: str = "change-me-in-production"      # JWT 密钥
    JWT_ALGORITHM: str = "HS256"

auth_config = AuthConfig()

security = HTTPBearer()

# ── X-API-Key 模式 ───────────────────────────────────

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """通过请求头 X-API-Key 鉴权"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="缺少 API Key，请在请求头中传入 X-API-Key")
    if x_api_key != auth_config.API_KEY:
        raise HTTPException(status_code=403, detail="API Key 无效")
    return {"auth_type": "api_key", "key": x_api_key}

# ── Bearer Token 模式 ────────────────────────────────

def verify_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """通过 Authorization: Bearer <token> 鉴权"""
    token = credentials.credentials
    # v1：简单 key 校验（后续可替换为 JWT decode）
    if token == auth_config.API_KEY:
        return {"auth_type": "bearer", "token": token}
    raise HTTPException(status_code=403, detail="Token 无效")

# ── 可选鉴权（不强制） ──────────────────────────────

def optional_auth(x_api_key: Optional[str] = Header(None)):
    """可选鉴权 — 有则验证，无则放行"""
    if x_api_key:
        return verify_api_key(x_api_key)
    return None

# ── 路由保护装饰器 ──────────────────────────────────

def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """需要 auth 的路由直接用 Depends(require_auth)"""
    return verify_bearer_token(credentials)
