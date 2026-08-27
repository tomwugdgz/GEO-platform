"""
GEO 商业版 8 步工作流扩展路由
包含：图库管理、蒸馏主词、自媒体账号、写作任务、投喂任务
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import uuid
import os
import shutil
from datetime import datetime

from app.models import get_db
from app.models.geo import (
    ImageCategory, ImageAsset, DistillKeyword, SocialMediaAccount,
    WritingTask, FeedTask, Brand
)

router = APIRouter(tags=["business-workflow"])

# ============================================================
# 1. 图库管理
# ============================================================

class CategoryCreate(BaseModel):
    brand_id: str
    name: str
    description: Optional[str] = None

@router.get("/geo/gallery/categories")
def list_categories(tenant_id: str, brand_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(ImageCategory).filter(ImageCategory.tenant_id == tenant_id)
    if brand_id:
        q = q.filter(ImageCategory.brand_id == brand_id)
    return q.order_by(ImageCategory.created_at.desc()).all()

@router.post("/geo/gallery/categories")
def create_category(tenant_id: str, payload: CategoryCreate, db: Session = Depends(get_db)):
    cat = ImageCategory(tenant_id=tenant_id, brand_id=payload.brand_id, name=payload.name, description=payload.description)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

@router.delete("/geo/gallery/categories/{cat_id}")
def delete_category(tenant_id: str, cat_id: str, db: Session = Depends(get_db)):
    cat = db.query(ImageCategory).filter(ImageCategory.id == cat_id, ImageCategory.tenant_id == tenant_id).first()
    if not cat:
        raise HTTPException(404, "分类不存在")
    db.delete(cat)
    db.commit()
    return {"ok": True}

@router.post("/geo/gallery/upload")
async def upload_image(tenant_id: str, category_id: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 简单存本地，生产环境应换 S3/OSS
    upload_dir = f"static/uploads/{tenant_id}/{category_id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_ext = os.path.splitext(file.filename)[1]
    file_name = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(upload_dir, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_url = f"/static/uploads/{tenant_id}/{category_id}/{file_name}"
    asset = ImageAsset(
        tenant_id=tenant_id, category_id=category_id,
        file_url=file_url, file_name=file.filename,
        file_size=os.path.getsize(file_path), mime_type=file.content_type
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset

@router.get("/geo/gallery/images")
def list_images(tenant_id: str, category_id: str, db: Session = Depends(get_db)):
    return db.query(ImageAsset).filter(
        ImageAsset.tenant_id == tenant_id,
        ImageAsset.category_id == category_id
    ).order_by(ImageAsset.created_at.desc()).all()

@router.delete("/geo/gallery/images/{img_id}")
def delete_image(tenant_id: str, img_id: str, db: Session = Depends(get_db)):
    img = db.query(ImageAsset).filter(ImageAsset.id == img_id, ImageAsset.tenant_id == tenant_id).first()
    if not img:
        raise HTTPException(404, "图片不存在")
    db.delete(img)
    db.commit()
    return {"ok": True}


# ============================================================
# 2. 蒸馏主词
# ============================================================

class DistillCreate(BaseModel):
    brand_id: str
    training_keyword: str
    conversion_keyword: str
    source: str = "ai_distill"  # ai_distill / manual

@router.post("/geo/distill/keywords")
def create_distill_keyword(tenant_id: str, payload: DistillCreate, db: Session = Depends(get_db)):
    # 模拟 AI 蒸馏逻辑：基于训练词生成相关问题
    distilled_queries = []
    if payload.source == "ai_distill":
        # 真实场景应调用 LLM API 生成，这里用规则生成模拟
        base = payload.training_keyword
        prefixes = ["推荐", "专业的", "靠谱的", "广州"]
        suffixes = ["哪家好", "哪个好", "多少钱", "是什么", "排名前十"]
        for p in prefixes[:2]:
            for s in suffixes[:3]:
                distilled_queries.append(f"{p}的{base}{s}")
        distilled_queries.append(f"{base}系统")
        distilled_queries.append(f"{base}软件")
    
    kw = DistillKeyword(
        tenant_id=tenant_id, brand_id=payload.brand_id,
        training_keyword=payload.training_keyword,
        conversion_keyword=payload.conversion_keyword,
        distilled_queries=distilled_queries,
        selected=False, source=payload.source
    )
    db.add(kw)
    db.commit()
    db.refresh(kw)
    return kw

@router.get("/geo/distill/keywords")
def list_distill_keywords(tenant_id: str, brand_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(DistillKeyword).filter(DistillKeyword.tenant_id == tenant_id)
    if brand_id:
        q = q.filter(DistillKeyword.brand_id == brand_id)
    return q.order_by(DistillKeyword.created_at.desc()).all()

@router.put("/geo/distill/keywords/{kw_id}")
def update_distill_keyword(tenant_id: str, kw_id: str, selected: Optional[bool] = None, db: Session = Depends(get_db)):
    kw = db.query(DistillKeyword).filter(DistillKeyword.id == kw_id, DistillKeyword.tenant_id == tenant_id).first()
    if not kw:
        raise HTTPException(404, "蒸馏词不存在")
    if selected is not None:
        kw.selected = selected
    db.commit()
    db.refresh(kw)
    return kw

@router.delete("/geo/distill/keywords/{kw_id}")
def delete_distill_keyword(tenant_id: str, kw_id: str, db: Session = Depends(get_db)):
    kw = db.query(DistillKeyword).filter(DistillKeyword.id == kw_id, DistillKeyword.tenant_id == tenant_id).first()
    if not kw:
        raise HTTPException(404, "蒸馏词不存在")
    db.delete(kw)
    db.commit()
    return {"ok": True}


# ============================================================
# 3. 自媒体账号
# ============================================================

class SocialAccountCreate(BaseModel):
    brand_id: str
    platform: str
    account_name: str
    account_url: Optional[str] = None
    auth_code: Optional[str] = None

PLATFORMS = ["wechat", "zhihu", "toutiao", "douyin", "xhs", "bilibili", "baijiahao", "sohu", "netease", "qq", "csdn", "jianshu"]

@router.post("/geo/social/accounts")
def create_social_account(tenant_id: str, payload: SocialAccountCreate, db: Session = Depends(get_db)):
    if payload.platform not in PLATFORMS:
        raise HTTPException(400, f"不支持的平台: {payload.platform}")
    acc = SocialMediaAccount(
        tenant_id=tenant_id, brand_id=payload.brand_id,
        platform=payload.platform, account_name=payload.account_name,
        account_url=payload.account_url, auth_code=payload.auth_code,
        auth_status="authorized" if payload.auth_code else "pending"
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc

@router.get("/geo/social/accounts")
def list_social_accounts(tenant_id: str, brand_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(SocialMediaAccount).filter(SocialMediaAccount.tenant_id == tenant_id)
    if brand_id:
        q = q.filter(SocialMediaAccount.brand_id == brand_id)
    return q.order_by(SocialMediaAccount.created_at.desc()).all()

@router.put("/geo/social/accounts/{acc_id}/auth")
def authorize_account(tenant_id: str, acc_id: str, auth_code: str, db: Session = Depends(get_db)):
    acc = db.query(SocialMediaAccount).filter(SocialMediaAccount.id == acc_id, SocialMediaAccount.tenant_id == tenant_id).first()
    if not acc:
        raise HTTPException(404, "账号不存在")
    acc.auth_code = auth_code
    acc.auth_status = "authorized"
    acc.authorized_at = datetime.utcnow()
    db.commit()
    db.refresh(acc)
    return acc

@router.delete("/geo/social/accounts/{acc_id}")
def delete_social_account(tenant_id: str, acc_id: str, db: Session = Depends(get_db)):
    acc = db.query(SocialMediaAccount).filter(SocialMediaAccount.id == acc_id, SocialMediaAccount.tenant_id == tenant_id).first()
    if not acc:
        raise HTTPException(404, "账号不存在")
    db.delete(acc)
    db.commit()
    return {"ok": True}


# ============================================================
# 4. 写作任务
# ============================================================

class WritingTaskCreate(BaseModel):
    brand_id: str
    task_name: str
    keyword_ids: List[str] = []
    category_id: Optional[str] = None
    knowledge_enabled: bool = False
    content_prompt: Optional[str] = None
    title_prompt: Optional[str] = None
    max_articles: int = 10

@router.post("/geo/writing/tasks")
def create_writing_task(tenant_id: str, payload: WritingTaskCreate, db: Session = Depends(get_db)):
    task = WritingTask(
        tenant_id=tenant_id, brand_id=payload.brand_id,
        task_name=payload.task_name, keyword_ids=payload.keyword_ids,
        category_id=payload.category_id, knowledge_enabled=payload.knowledge_enabled,
        content_prompt=payload.content_prompt, title_prompt=payload.title_prompt,
        max_articles=payload.max_articles, status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.get("/geo/writing/tasks")
def list_writing_tasks(tenant_id: str, brand_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(WritingTask).filter(WritingTask.tenant_id == tenant_id)
    if brand_id:
        q = q.filter(WritingTask.brand_id == brand_id)
    return q.order_by(WritingTask.created_at.desc()).all()

@router.post("/geo/writing/tasks/{task_id}/run")
def run_writing_task(tenant_id: str, task_id: str, db: Session = Depends(get_db)):
    """模拟运行写作任务（真实场景应接入 LLM API 异步生成）"""
    task = db.query(WritingTask).filter(WritingTask.id == task_id, WritingTask.tenant_id == tenant_id).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    task.status = "completed"
    task.created_articles = task.max_articles
    task.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return {"message": "写作任务模拟完成", "task": task}

@router.delete("/geo/writing/tasks/{task_id}")
def delete_writing_task(tenant_id: str, task_id: str, db: Session = Depends(get_db)):
    task = db.query(WritingTask).filter(WritingTask.id == task_id, WritingTask.tenant_id == tenant_id).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    db.delete(task)
    db.commit()
    return {"ok": True}


# ============================================================
# 5. 投喂任务
# ============================================================

class FeedTaskCreate(BaseModel):
    brand_id: str
    task_name: str
    writing_task_id: str
    max_publish_count: int = 10
    daily_limit_per_account: int = 1
    platform_ids: List[str] = []

@router.post("/geo/feed/tasks")
def create_feed_task(tenant_id: str, payload: FeedTaskCreate, db: Session = Depends(get_db)):
    task = FeedTask(
        tenant_id=tenant_id, brand_id=payload.brand_id,
        task_name=payload.task_name, writing_task_id=payload.writing_task_id,
        max_publish_count=payload.max_publish_count,
        daily_limit_per_account=payload.daily_limit_per_account,
        platform_ids=payload.platform_ids, status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.get("/geo/feed/tasks")
def list_feed_tasks(tenant_id: str, brand_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(FeedTask).filter(FeedTask.tenant_id == tenant_id)
    if brand_id:
        q = q.filter(FeedTask.brand_id == brand_id)
    return q.order_by(FeedTask.created_at.desc()).all()

@router.post("/geo/feed/tasks/{task_id}/start")
def start_feed_task(tenant_id: str, task_id: str, db: Session = Depends(get_db)):
    """启动投喂任务（真实场景应调用客户端 exe 自动发布）"""
    task = db.query(FeedTask).filter(FeedTask.id == task_id, FeedTask.tenant_id == tenant_id).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    task.status = "running"
    task.started_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return {"message": "投喂任务已启动，客户端将自动执行", "task": task}

@router.delete("/geo/feed/tasks/{task_id}")
def delete_feed_task(tenant_id: str, task_id: str, db: Session = Depends(get_db)):
    task = db.query(FeedTask).filter(FeedTask.id == task_id, FeedTask.tenant_id == tenant_id).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    db.delete(task)
    db.commit()
    return {"ok": True}
