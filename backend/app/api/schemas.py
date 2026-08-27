from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID


class MediaResourceCreate(BaseModel):
    name: str
    type: str  # offline/online
    category: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    coverage_radius: int = 1000
    daily_price: Optional[float] = None
    daily_impressions: int = 0
    metadata: Optional[Dict[str, Any]] = {}


class MediaResourceUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    daily_price: Optional[float] = None
    daily_impressions: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    budget: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    target_audience: Optional[Dict[str, Any]] = {}


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    budget: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    target_audience: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class PlacementCreate(BaseModel):
    campaign_id: UUID
    media_id: UUID
    date: date
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    cost: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = {}


class ConversionCreate(BaseModel):
    placement_id: UUID
    user_id: Optional[str] = None
    conversion_type: str
    conversion_value: Optional[float] = None
    touchpoint_order: int = 1
    attribution_model: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None


class GeoAttributionResponse(BaseModel):
    geo_data: List[Dict[str, Any]]
    total_locations: int


class FunnelResponse(BaseModel):
    funnel: List[Dict[str, Any]]
    ctr: float
    cvr: float
