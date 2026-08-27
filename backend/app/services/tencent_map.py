import httpx
from typing import Optional, List, Dict, Any
from app.config import settings


class TencentMapService:
    """腾讯地图API封装服务"""
    
    def __init__(self):
        self.api_key = settings.TENCENT_MAP_KEY
        self.base_url = settings.TENCENT_MAP_BASE_URL
    
    async def geocode(self, address: str, city: str = "") -> Optional[Dict[str, Any]]:
        """地址转坐标（地理编码）"""
        url = f"{self.base_url}geocoder/v1/"
        params = {
            "key": self.api_key,
            "address": address,
        }
        if city:
            params["region"] = city
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if data.get("status") == 0 and data.get("result"):
                location = data["result"]["location"]
                return {
                    "lat": location["lat"],
                    "lng": location["lng"],
                    "formatted_address": data["result"].get("formatted_addresses", {}).get("recommend", address)
                }
        return None
    
    async def reverse_geocode(self, lat: float, lng: float) -> Optional[Dict[str, Any]]:
        """坐标转地址（逆地理编码）"""
        url = f"{self.base_url}geocoder/v1/"
        params = {
            "key": self.api_key,
            "location": f"{lat},{lng}",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if data.get("status") == 0 and data.get("result"):
                return {
                    "address": data["result"].get("formatted_addresses", {}).get("recommend", ""),
                    "province": data["result"].get("address_component", {}).get("province", ""),
                    "city": data["result"].get("address_component", {}).get("city", ""),
                    "district": data["result"].get("address_component", {}).get("district", ""),
                }
        return None
    
    async def search_poi(
        self, 
        keyword: str, 
        location: str = "", 
        radius: int = 5000,
        page_index: int = 1,
        page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """周边POI搜索"""
        url = f"{self.base_url}place/v1/search"
        params = {
            "key": self.api_key,
            "keyword": keyword,
            "radius": radius,
            "page_index": page_index,
            "page_size": page_size,
        }
        if location:
            params["location"] = location
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if data.get("status") == 0 and data.get("data"):
                pois = data["data"]
                return [
                    {
                        "id": poi.get("id", ""),
                        "name": poi.get("title", ""),
                        "lat": poi.get("location", {}).get("lat", 0),
                        "lng": poi.get("location", {}).get("lng", 0),
                        "address": poi.get("address", ""),
                        "category": poi.get("category", ""),
                    }
                    for poi in pois
                ]
        return []
    
    async def search_nearby(
        self, 
        lat: float, 
        lng: float, 
        keyword: str = "", 
        radius: int = 3000
    ) -> List[Dict[str, Any]]:
        """附近搜索（指定坐标）"""
        location = f"{lat},{lng}"
        return await self.search_poi(keyword=keyword, location=location, radius=radius)
    
    async def get_distance_matrix(
        self, 
        origins: List[str], 
        destinations: List[str],
        mode: str = "walking"
    ) -> List[List[Dict[str, Any]]]:
        """距离矩阵计算"""
        url = f"{self.base_url}distancematrix/v1/"
        params = {
            "key": self.api_key,
            "from": ";".join(origins),
            "to": ";".join(destinations),
            "mode": mode,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if data.get("status") == 0 and data.get("result"):
                return data["result"].get("elements", [])
        return []
    
    async def get_district_data(self, city: str) -> Optional[Dict[str, Any]]:
        """获取行政区划数据"""
        url = f"{self.base_url}district/v1/list"
        params = {
            "key": self.api_key,
            "keyword": city,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if data.get("status") == 0 and data.get("result"):
                return data["result"]
        return None
    
    async def get_ip_location(self, ip: str = "") -> Optional[Dict[str, Any]]:
        """IP定位"""
        url = f"{self.base_url}location/v1/ip"
        params = {"key": self.api_key}
        if ip:
            params["ip"] = ip
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if data.get("status") == 0 and data.get("result"):
                return data["result"]
        return None


# 全局实例
tencent_map_service = TencentMapService()
