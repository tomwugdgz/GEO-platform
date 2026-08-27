from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import date

from app.models import get_db, MediaResource, Campaign, Placement, Conversion, CampaignMedia
from app.api.schemas import MediaResourceCreate, MediaResourceUpdate
from app.services.tencent_map import tencent_map_service
from app.services.ai_recommender import ai_recommender

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AI智能投放系统"}


# ========== 媒体资源管理 ==========

@router.get("/media", response_model=List[dict])
async def list_media(
    type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(MediaResource)
    if type:
        query = query.filter(MediaResource.type == type)
    if category:
        query = query.filter(MediaResource.category == category)
    if status:
        query = query.filter(MediaResource.status == status)
    
    media = query.all()
    return [
        {
            "id": str(m.id),
            "name": m.name,
            "type": m.type,
            "category": m.category,
            "latitude": m.latitude,
            "longitude": m.longitude,
            "address": m.address,
            "coverage_radius": m.coverage_radius,
            "daily_price": float(m.daily_price) if m.daily_price else None,
            "daily_impressions": m.daily_impressions,
            "status": m.status,
            "custom_data": m.custom_data,
        }
        for m in media
    ]


@router.post("/media")
async def create_media(media_data: MediaResourceCreate, db: Session = Depends(get_db)):
    # 如果提供了地址但没有坐标，使用腾讯地图地理编码
    if media_data.address and (media_data.latitude is None or media_data.longitude is None):
        try:
            geo_result = await tencent_map_service.geocode(media_data.address)
            if geo_result:
                media_data.latitude = geo_result["lat"]
                media_data.longitude = geo_result["lng"]
        except Exception:
            pass  # 地理编码失败不影响创建
    
    media = MediaResource(
        name=media_data.name,
        type=media_data.type,
        category=media_data.category,
        latitude=media_data.latitude,
        longitude=media_data.longitude,
        address=media_data.address,
        coverage_radius=media_data.coverage_radius,
        daily_price=media_data.daily_price,
        daily_impressions=media_data.daily_impressions,
        custom_data=media_data.metadata or {},
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    
    return {"id": str(media.id), "message": "媒体资源创建成功"}


@router.get("/media/{media_id}")
async def get_media(media_id: UUID, db: Session = Depends(get_db)):
    media = db.query(MediaResource).filter(MediaResource.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="媒体资源不存在")
    
    return {
        "id": str(media.id),
        "name": media.name,
        "type": media.type,
        "category": media.category,
        "latitude": media.latitude,
        "longitude": media.longitude,
        "address": media.address,
        "coverage_radius": media.coverage_radius,
        "daily_price": float(media.daily_price) if media.daily_price else None,
        "daily_impressions": media.daily_impressions,
        "status": media.status,
        "custom_data": media.custom_data,
    }


@router.put("/media/{media_id}")
async def update_media(media_id: UUID, update_data: MediaResourceUpdate, db: Session = Depends(get_db)):
    media = db.query(MediaResource).filter(MediaResource.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="媒体资源不存在")
    
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(media, field, value)
    
    db.commit()
    return {"message": "媒体资源更新成功"}


@router.delete("/media/{media_id}")
async def delete_media(media_id: UUID, db: Session = Depends(get_db)):
    media = db.query(MediaResource).filter(MediaResource.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="媒体资源不存在")
    
    db.delete(media)
    db.commit()
    return {"message": "媒体资源删除成功"}


# ========== 投放计划管理 ==========

@router.get("/campaigns", response_model=List[dict])
async def list_campaigns(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Campaign)
    if status:
        query = query.filter(Campaign.status == status)
    
    campaigns = query.all()
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "description": c.description,
            "budget": float(c.budget) if c.budget else None,
            "start_date": str(c.start_date) if c.start_date else None,
            "end_date": str(c.end_date) if c.end_date else None,
            "target_audience": c.target_audience,
            "status": c.status,
            "ai_recommendations": c.ai_recommendations,
            "created_at": str(c.created_at),
        }
        for c in campaigns
    ]


@router.post("/campaigns")
async def create_campaign(campaign_data: MediaResourceCreate, db: Session = Depends(get_db)):
    # 复用schema，实际需要独立的CampaignCreate schema
    campaign = Campaign(
        name=campaign_data.name,
        budget=campaign_data.daily_price,  # 临时使用
        target_audience=campaign_data.metadata or {},
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    return {"id": str(campaign.id), "message": "投放计划创建成功"}


@router.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: UUID, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="投放计划不存在")
    
    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "description": campaign.description,
        "budget": float(campaign.budget) if campaign.budget else None,
        "start_date": str(campaign.start_date) if campaign.start_date else None,
        "end_date": str(campaign.end_date) if campaign.end_date else None,
        "target_audience": campaign.target_audience,
        "status": campaign.status,
        "ai_recommendations": campaign.ai_recommendations,
    }


@router.post("/campaigns/{campaign_id}/activate")
async def activate_campaign(campaign_id: UUID, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="投放计划不存在")
    
    campaign.status = "active"
    db.commit()
    return {"message": "投放计划已激活"}


@router.post("/campaigns/{campaign_id}/pause")
async def pause_campaign(campaign_id: UUID, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="投放计划不存在")
    
    campaign.status = "paused"
    db.commit()
    return {"message": "投放计划已暂停"}


# ========== 腾讯地图服务 ==========

@router.get("/map/geocode")
async def map_geocode(address: str, city: str = ""):
    result = await tencent_map_service.geocode(address, city)
    if not result:
        raise HTTPException(status_code=404, detail="地址解析失败")
    return result


@router.get("/map/reverse-geocode")
async def map_reverse_geocode(lat: float, lng: float):
    result = await tencent_map_service.reverse_geocode(lat, lng)
    if not result:
        raise HTTPException(status_code=404, detail="逆地理编码失败")
    return result


@router.get("/map/search-poi")
async def map_search_poi(
    keyword: str,
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    radius: int = 3000
):
    location = ""
    if lat and lng:
        location = f"{lat},{lng}"
    
    results = await tencent_map_service.search_poi(keyword, location, radius)
    return {"pois": results, "count": len(results)}


# ========== AI推荐 ==========

@router.get("/ai/recommend-media")
async def recommend_media(
    budget: float,
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    location = None
    if lat and lng:
        location = {"lat": lat, "lng": lng}
    
    recommendations = ai_recommender.recommend_media(db, budget, location)
    return {"recommendations": recommendations, "count": len(recommendations)}


@router.get("/ai/strategy-suggestion")
async def suggest_strategy(
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    industry: Optional[str] = Query(None)
):
    location = None
    if lat and lng:
        location = {"lat": lat, "lng": lng}
    
    strategy = ai_recommender.suggest_campaign_strategy(None, location, industry)
    return strategy
