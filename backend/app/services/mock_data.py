"""
模拟数据源 - 替代真实API
QADN点位数据 + 天工智投库存 + XXAPP行为 + 友盟人群画像
"""
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any


class MockDataSource:
    """模拟数据源"""
    
    # 广州主要商圈坐标
    GUANGZHOU_DISTRICTS = [
        {"name": "天河体育中心", "lat": 23.136, "lng": 113.326, "type": "cbd"},
        {"name": "北京路步行街", "lat": 23.125, "lng": 113.264, "type": "shopping"},
        {"name": "珠江新城", "lat": 23.118, "lng": 113.321, "type": "cbd"},
        {"name": "江南西", "lat": 23.099, "lng": 113.264, "type": "residential"},
        {"name": "番禺万达", "lat": 22.948, "lng": 113.366, "type": "suburban"},
        {"name": "白云大道", "lat": 23.185, "lng": 113.259, "type": "residential"},
        {"name": "海珠客村", "lat": 23.095, "lng": 113.318, "type": "residential"},
        {"name": "荔湾上下九", "lat": 23.115, "lng": 113.245, "type": "shopping"},
    ]
    
    INTEREST_TAGS = ["购物", "美食", "运动", "旅游", "科技", "教育", "母婴", "汽车", "房产", "金融"]
    AGE_GROUPS = ["18-24", "25-34", "35-44", "45-54", "55+"]
    INCOME_LEVELS = ["low", "medium", "high", "ultra_high"]
    
    @staticmethod
    def get_qadn_location_data(city: str = "广州", date_range: dict = None) -> List[Dict[str, Any]]:
        """QADN点位数据模拟"""
        data = []
        for district in MockDataSource.GUANGZHOU_DISTRICTS:
            # 每个商圈生成多个点位
            for i in range(random.randint(3, 8)):
                poi_id = f"QADN_{district['name']}_{i+1:02d}"
                data.append({
                    "poi_id": poi_id,
                    "name": f"{district['name']}点位{i+1}",
                    "lat": district["lat"] + random.uniform(-0.005, 0.005),
                    "lng": district["lng"] + random.uniform(-0.005, 0.005),
                    "district": district["name"],
                    "district_type": district["type"],
                    "foot_traffic_daily": random.randint(5000, 50000),
                    "dwell_time_avg_min": random.randint(2, 15),
                    "peak_hours": random.sample(range(7, 22), 3),
                    "audience_profile": {
                        "age_group": random.choice(MockDataSource.AGE_GROUPS),
                        "gender_ratio": round(random.uniform(0.3, 0.7), 2),
                        "income_level": random.choice(MockDataSource.INCOME_LEVELS),
                        "top_interests": random.sample(MockDataSource.INTEREST_TAGS, 3),
                    },
                    "device_data": {
                        "mobile_visitors_pct": round(random.uniform(0.6, 0.95), 2),
                        "unique_devices_daily": random.randint(1000, 10000),
                    },
                })
        return data
    
    @staticmethod
    def get_tiangong_ad_inventory() -> List[Dict[str, Any]]:
        """天工智投点位库存模拟"""
        inventory = []
        ad_types = ["电梯框架", "户外大屏", "公交站牌", "社区灯箱", "停车场道闸"]
        
        for district in MockDataSource.GUANGZHOU_DISTRICTS:
            for ad_type in ad_types:
                # 每种类型在每个商圈有多个广告位
                count = random.randint(2, 10)
                for i in range(count):
                    inventory.append({
                        "id": f"TG_{district['name']}_{ad_type[:2]}_{i+1:02d}",
                        "ad_type": ad_type,
                        "district": district["name"],
                        "lat": district["lat"] + random.uniform(-0.003, 0.003),
                        "lng": district["lng"] + random.uniform(-0.003, 0.003),
                        "price_daily": round(random.uniform(200, 5000), 0),
                        "price_weekly": round(random.uniform(1200, 30000), 0),
                        "available": random.choice([True, True, True, False]),
                        "impression_est_daily": random.randint(1000, 20000),
                        "specifications": {
                            "width_m": random.choice([1.2, 2.4, 3.6, 6, 12]),
                            "height_m": random.choice([1.8, 3, 5, 8]),
                            "format": random.choice(["静态", "电子屏", "互动屏"]),
                        },
                        "available_dates": MockDataSource._generate_available_dates(),
                    })
        return inventory
    
    @staticmethod
    def get_qinlin_app_behavior(user_count: int = 1000) -> List[Dict[str, Any]]:
        """XXAPP行为数据模拟"""
        behaviors = []
        action_types = ["browse", "click", "search", "purchase", "share", "comment"]
        
        for i in range(user_count):
            user_id = f"ql_user_{uuid.uuid4().hex[:8]}"
            cookie_id = f"cookie_{uuid.uuid4().hex[:12]}"
            device_fp = f"fp_{uuid.uuid4().hex[:16]}"
            
            # 每个用户生成多个行为会话
            session_count = random.randint(1, 5)
            for _ in range(session_count):
                session_id = f"session_{uuid.uuid4().hex[:10]}"
                actions = []
                action_count = random.randint(3, 15)
                for _ in range(action_count):
                    actions.append({
                        "type": random.choice(action_types),
                        "timestamp": (datetime.now() - timedelta(hours=random.randint(0, 720))).isoformat(),
                        "category": random.choice(MockDataSource.INTEREST_TAGS),
                        "duration_sec": random.randint(1, 300),
                    })
                
                behaviors.append({
                    "user_id": user_id,
                    "cookie_id": cookie_id,
                    "device_fingerprint": device_fp,
                    "session_id": session_id,
                    "actions": actions,
                    "location_visited": random.sample([d["name"] for d in MockDataSource.GUANGZHOU_DISTRICTS], random.randint(1, 3)),
                    "conversion": random.random() < 0.05,  # 5%转化率
                    "conversion_value": round(random.uniform(50, 500), 2) if random.random() < 0.05 else 0,
                })
        
        return behaviors
    
    @staticmethod
    def get_umeng_audience_data(region: str = "广州") -> Dict[str, Any]:
        """友盟人群画像数据模拟"""
        district_data = {}
        
        for district in MockDataSource.GUANGZHOU_DISTRICTS:
            district_data[district["name"]] = {
                "total_users": random.randint(50000, 500000),
                "age_distribution": {
                    age: round(random.uniform(0.05, 0.35), 2)
                    for age in MockDataSource.AGE_GROUPS
                },
                "gender_distribution": {
                    "male": round(random.uniform(0.35, 0.65), 2),
                    "female": round(random.uniform(0.35, 0.65), 2),
                },
                "income_distribution": {
                    level: round(random.uniform(0.1, 0.4), 2)
                    for level in MockDataSource.INCOME_LEVELS
                },
                "interest_ranking": random.sample(MockDataSource.INTEREST_TAGS, 5),
                "active_hours": {
                    f"{h}:00": round(random.uniform(0.01, 0.15), 2)
                    for h in range(0, 24)
                },
                "device_distribution": {
                    "ios": round(random.uniform(0.3, 0.5), 2),
                    "android": round(random.uniform(0.5, 0.7), 2),
                },
                "app_usage_categories": random.sample(MockDataSource.INTEREST_TAGS, 3),
            }
        
        return {
            "region": region,
            "total_region_users": sum(d["total_users"] for d in district_data.values()),
            "districts": district_data,
            "generated_at": datetime.now().isoformat(),
        }
    
    @staticmethod
    def _generate_available_dates() -> List[str]:
        """生成可用日期列表（未来30天）"""
        dates = []
        today = datetime.now().date()
        for i in range(30):
            date = today + timedelta(days=i)
            if random.random() < 0.8:  # 80%可用
                dates.append(date.isoformat())
        return dates


# 全局实例
mock_data = MockDataSource()
