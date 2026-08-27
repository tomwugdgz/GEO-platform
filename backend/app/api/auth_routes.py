"""
认证路由 — 登录取 token + 发 API Key
复用 AIAdPlacer 双模式鉴权范式（X-API-Key + Bearer Token）
"""
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models import get_db, User
from app.api.auth import verify_api_key, verify_bearer_token

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str   # v1 简单校验，Phase F 升级 bcrypt/JWT


class LoginResponse(BaseModel):
    token: str
    user_id: str
    tenant_id: str
    role: str


class ApiKeyRequest(BaseModel):
    email: str
    password: str


class ApiKeyResponse(BaseModel):
    api_key: str
    expires_at: str | None = None


# ── 登录（返回 Bearer token，v1 简单实现）────────────────
@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or user.hashed_pwd != req.password:   # v1 明文比对，Phase F 改 bcrypt
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="账号已禁用")
    # v1 直接用 api_key 当 token（Phase F 换 JWT）
    return LoginResponse(
        token=user.api_key or "",
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role,
    )


# ── 签发 API Key ─────────────────────────────────────────
@router.post("/apikey", response_model=ApiKeyResponse)
def issue_api_key(req: ApiKeyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or user.hashed_pwd != req.password:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    key = f"geo-{uuid4().hex[:32]}"
    user.api_key = key
    db.commit()
    return ApiKeyResponse(api_key=key)
