"""青柠 Booking — level 派生规则（设计文档 §7 / P0 决策①）。

派生逻辑：
1) 基础档：按 ``media_type_code`` 查 ``media_level_rule``（match_type='media_type'）。
2) 城市覆盖：match_type='city' 且 ``city`` 含 ``match_key``（如 '广州天河'），
   取 priority 最高者；若其 priority > 基础档 priority，则覆盖为城市档（封顶 A++）。

规则可后台改 ``media_level_rule`` 即生效，无需改代码。
"""
from __future__ import annotations

from typing import Dict, List, Optional

# 默认规则（与迁移 0001 种子一致），DB 不可用或为空时兜底。
DEFAULT_RULES: List[Dict] = [
    {"match_type": "media_type", "match_key": "door_access", "level": "A+", "priority": 0, "enabled": True},
    {"match_type": "media_type", "match_key": "mall_led", "level": "A++", "priority": 0, "enabled": True},
    {"match_type": "media_type", "match_key": "smart_screen_l9", "level": "A", "priority": 0, "enabled": True},
    {"match_type": "media_type", "match_key": "smart_screen_202507", "level": "A", "priority": 0, "enabled": True},
    {"match_type": "media_type", "match_key": "unit_door", "level": "B", "priority": 0, "enabled": True},
    {"match_type": "media_type", "match_key": "boom_gate", "level": "C", "priority": 0, "enabled": True},
    {"match_type": "city", "match_key": "广州天河", "level": "A++", "priority": 10, "enabled": True},
    {"match_type": "city", "match_key": "广州珠江新城", "level": "A++", "priority": 10, "enabled": True},
    {"match_type": "city", "match_key": "北京朝阳", "level": "A++", "priority": 10, "enabled": True},
    {"match_type": "city", "match_key": "上海浦东", "level": "A++", "priority": 10, "enabled": True},
]

# 媒体类型编码 -> 中文名（仅用于日志/可读）
MEDIA_TYPE_LABELS = {
    "door_access": "门禁点位",
    "mall_led": "商场LED",
    "smart_screen_l9": "智能屏L9",
    "smart_screen_202507": "智能屏202507",
    "unit_door": "单元门点位",
    "boom_gate": "道闸点位",
}


def derive_level_from_rules(
    media_type_code: str,
    city: Optional[str],
    rules: List[Dict],
) -> str:
    """纯函数：根据规则列表派生 level。

    - 基础档取 media_type 命中项；
    - 城市命中（substring）且 priority 更高则覆盖；
    - 无命中基础档时回退 'C'。
    """
    base_level: Optional[str] = None
    base_priority = -1
    city_rule: Optional[Dict] = None

    for r in rules:
        if not r.get("enabled", True):
            continue
        if r["match_type"] == "media_type" and r["match_key"] == media_type_code:
            base_level = r["level"]
            base_priority = r["priority"]
        elif r["match_type"] == "city":
            key = r["match_key"] or ""
            if city and key and key in city:
                if city_rule is None or r["priority"] > city_rule["priority"]:
                    city_rule = r

    if base_level is None:
        base_level = "C"
        base_priority = -1

    if city_rule is not None and city_rule["priority"] > base_priority:
        return city_rule["level"]
    return base_level


async def load_level_rules(db) -> List[Dict]:
    """从 PG ``media_level_rule`` 加载规则（启用项）。"""
    from sqlalchemy import select

    from app.models.booking import MediaLevelRule

    rows = (await db.execute(select(MediaLevelRule))).scalars().all()
    return [
        {
            "match_type": r.match_type,
            "match_key": r.match_key,
            "level": r.level,
            "priority": r.priority,
            "enabled": r.enabled,
        }
        for r in rows
    ]


async def derive_level(media_type_code: str, city: Optional[str]) -> str:
    """异步版：优先读 DB 规则，缺失则回退 DEFAULT_RULES。"""
    from app.core.async_db import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as db:
            rules = await load_level_rules(db)
        if not rules:
            rules = DEFAULT_RULES
    except Exception:  # noqa: BLE001
        rules = DEFAULT_RULES
    return derive_level_from_rules(media_type_code, city, rules)
