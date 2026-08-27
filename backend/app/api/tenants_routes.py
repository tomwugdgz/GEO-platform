"""
租户管理路由 — CRUD for Tenant / Brand / User / Competitor
v1 单用户多品牌 + tenant_id 软隔离，Phase F 加 RBAC
"""
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.models import get_db, Tenant, Brand, User, Competitor
from app.api.auth import verify_bearer_token

router = APIRouter()


# ── Pydantic schemas ─────────────────────────────────────
class TenantCreate(BaseModel):
    slug: str
    name: str
    plan: str = "free"


class TenantOut(BaseModel):
    id: str
    slug: str
    name: str
    plan: str
    status: str
    created_at: datetime


class BrandCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    official_site: Optional[str] = None
    description: Optional[str] = None


class BrandOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    industry: Optional[str]
    official_site: Optional[str]
    description: Optional[str]


class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "member"


class UserOut(BaseModel):
    id: str
    tenant_id: str
    email: str
    role: str
    api_key: Optional[str]
    status: str


class CompetitorCreate(BaseModel):
    brand_id: str
    name: str
    official_site: Optional[str] = None


class CompetitorOut(BaseModel):
    id: str
    tenant_id: str
    brand_id: str
    name: str
    official_site: Optional[str]


# ── Tenant ───────────────────────────────────────────────
@router.post("", response_model=TenantOut)
def create_tenant(payload: TenantCreate, db: Session = Depends(get_db)):
    exists = db.query(Tenant).filter(Tenant.slug == payload.slug).first()
    if exists:
        raise HTTPException(status_code=409, detail=f"租户 slug '{payload.slug}' 已存在")
    t = Tenant(slug=payload.slug, name=payload.name, plan=payload.plan)
    db.add(t); db.commit(); db.refresh(t)
    return TenantOut(id=str(t.id), slug=t.slug, name=t.name, plan=t.plan,
                     status=t.status, created_at=t.created_at)


@router.get("", response_model=list[TenantOut])
def list_tenants(db: Session = Depends(get_db)):
    return [
        TenantOut(id=str(t.id), slug=t.slug, name=t.name, plan=t.plan,
                  status=t.status, created_at=t.created_at)
        for t in db.query(Tenant).all()
    ]


@router.get("/{tenant_id}", response_model=TenantOut)
def get_tenant(tenant_id: str, db: Session = Depends(get_db)):
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t: raise HTTPException(status_code=404, detail="租户不存在")
    return TenantOut(id=str(t.id), slug=t.slug, name=t.name, plan=t.plan,
                     status=t.status, created_at=t.created_at)


# ── Brand ────────────────────────────────────────────────
@router.post("/{tenant_id}/brands", response_model=BrandOut)
def create_brand(tenant_id: str, payload: BrandCreate, db: Session = Depends(get_db)):
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t: raise HTTPException(status_code=404, detail="租户不存在")
    b = Brand(tenant_id=t.id, name=payload.name, industry=payload.industry,
              official_site=payload.official_site, description=payload.description)
    db.add(b); db.commit(); db.refresh(b)
    return BrandOut(id=str(b.id), tenant_id=str(b.tenant_id), name=b.name,
                    industry=b.industry, official_site=b.official_site,
                    description=b.description)


@router.get("/{tenant_id}/brands", response_model=list[BrandOut])
def list_brands(tenant_id: str, db: Session = Depends(get_db)):
    return [
        BrandOut(id=str(b.id), tenant_id=str(b.tenant_id), name=b.name,
                 industry=b.industry, official_site=b.official_site,
                 description=b.description)
        for b in db.query(Brand).filter(Brand.tenant_id == tenant_id).all()
    ]


# ── User ─────────────────────────────────────────────────
@router.post("/{tenant_id}/users", response_model=UserOut)
def create_user(tenant_id: str, payload: UserCreate, db: Session = Depends(get_db)):
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t: raise HTTPException(status_code=404, detail="租户不存在")
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists: raise HTTPException(status_code=409, detail="邮箱已存在")
    api_key = f"geo-{uuid4().hex[:32]}"
    u = User(tenant_id=t.id, email=payload.email, hashed_pwd=payload.password,
             role=payload.role, api_key=api_key)
    db.add(u); db.commit(); db.refresh(u)
    return UserOut(id=str(u.id), tenant_id=str(u.tenant_id), email=u.email,
                   role=u.role, api_key=u.api_key, status=u.status)


@router.get("/{tenant_id}/users", response_model=list[UserOut])
def list_users(tenant_id: str, db: Session = Depends(get_db)):
    return [
        UserOut(id=str(u.id), tenant_id=str(u.tenant_id), email=u.email,
                role=u.role, api_key=u.api_key, status=u.status)
        for u in db.query(User).filter(User.tenant_id == tenant_id).all()
    ]


# ── Competitor ───────────────────────────────────────────
@router.post("/{tenant_id}/competitors", response_model=CompetitorOut)
def create_competitor(tenant_id: str, payload: CompetitorCreate,
                      db: Session = Depends(get_db)):
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t: raise HTTPException(status_code=404, detail="租户不存在")
    b = db.query(Brand).filter(Brand.id == payload.brand_id,
                               Brand.tenant_id == tenant_id).first()
    if not b: raise HTTPException(status_code=404, detail="品牌不存在")
    c = Competitor(tenant_id=t.id, brand_id=b.id, name=payload.name,
                   official_site=payload.official_site)
    db.add(c); db.commit(); db.refresh(c)
    return CompetitorOut(id=str(c.id), tenant_id=str(c.tenant_id),
                         brand_id=str(c.brand_id), name=c.name,
                         official_site=c.official_site)
