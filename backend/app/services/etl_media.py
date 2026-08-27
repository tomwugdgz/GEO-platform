"""青柠 Booking — ETL：SQLite 只读 → 派生 level → 幂等 upsert PG media_resources。

设计文档 §7（方案 A）：把真实 SQLite 6 张媒体表（只读、异构、无 level 列）归一化进
PG ``media_resources``（SSOT），补全 ``level/city/area/project/point_no/media_type_code/
source_table/dedup_key`` 并写回 ``level``（派生）。

铁律（见设计 §15）：
- SQLite **只读**：连接串加 ``mode=ro``；绝不写 SQLite、绝不跨库 join。
- 幂等：``id = uuid5(NAMESPACE, dedup_key)`` 确定性生成，``ON CONFLICT (id) DO UPDATE``
  可安全重跑。
- 行数对齐：6 表总计入 ``media_resources``（派生列）应对齐 SQLite 6 表总行数。

用法：``python -m app.services.etl_media``
"""
from __future__ import annotations

import asyncio
import sqlite3
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.sql.expression import text

from app.config import settings
from app.core.async_db import AsyncSessionLocal
from app.models import MediaResource
from app.services.level_rule import derive_level_from_rules, load_level_rules

# 确定性命名空间（固定 UUID，保证幂等 id 稳定）
NAMESPACE = uuid.UUID("6f9619ff-8b86-d011-b42d-00cf4fc964ff")

# 6 张 SQLite 媒体表 → 媒体类型编码 + 列映射（异构 schema 逐表归一）
TABLE_SPECS: Dict[str, Dict[str, Any]] = {
    "门禁点位": dict(
        media_type_code="door_access",
        city="城市", area="区", project="楼盘名称", point_no="id",
        address="楼盘地址", lat="纬度", lng="经度",
    ),
    "智能屏L9": dict(
        media_type_code="smart_screen_l9",
        city="城市", area="区域", project="楼盘名称", point_no="楼盘ID",
        address="详细地址", lat="经度", lng="纬度",
    ),
    "智能屏202507": dict(
        media_type_code="smart_screen_202507",
        city="所属城市", area="区县", project="楼盘名称", point_no="id",
        address="详细地址", lat="经度", lng="纬度",
    ),
    "单元门点位": dict(
        media_type_code="unit_door",
        city="城市", area="区域", project="资源名称", point_no="id",
        address="详细地址", lat="经度", lng="纬度",
    ),
    "商场LED点位": dict(
        media_type_code="mall_led",
        city="城市", area="行政区", project="点位名称", point_no="点位名称",
        address="地址", lat="经度", lng="纬度",
    ),
    "道闸点位": dict(
        media_type_code="boom_gate",
        city="行政区域", area="商圈", project="社区名称", point_no="点位ID",
        address="社区地址", lat=None, lng=None,
    ),
}


def _norm(v) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _to_float(v) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _dedup_key(city: Optional[str], project: Optional[str], area: Optional[str],
               point_no: Optional[str], media_type_code: str) -> str:
    """确定性去重键（设计：normalize(city+project+building+elevatorNo+mediaType)）。"""
    parts = [
        _norm(city) or "",
        _norm(project) or "",
        _norm(area) or "",
        _norm(point_no) or "",
        media_type_code,
    ]
    return "|".join(parts)


def _read_sqlite(path: str):
    """只读游标遍历 SQLite 6 表，逐行 yield (table_name, media_type_code, row_dict)。"""
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        for table_name, spec in TABLE_SPECS.items():
            try:
                cur = conn.execute(f'SELECT * FROM "{table_name}"')
            except sqlite3.Error as e:
                print(f"  [warn] 读取表 {table_name} 失败: {e}")
                continue
            for row in cur:
                yield table_name, spec["media_type_code"], dict(row)
    finally:
        conn.close()


def _build_record(table_name: str, media_type_code: str, row: Dict[str, Any]) -> Dict[str, Any]:
    spec = TABLE_SPECS[table_name]
    city = _norm(row.get(spec["city"]))
    project = _norm(row.get(spec["project"]))
    area = _norm(row.get(spec["area"]))
    point_no = _norm(row.get(spec["point_no"]))
    address = _norm(row.get(spec["address"]))
    lat = _to_float(row.get(spec["lat"])) if spec.get("lat") else None
    lng = _to_float(row.get(spec["lng"])) if spec.get("lng") else None

    level = derive_level_from_rules(media_type_code, city, DEFAULT_RULES_HOLDER)
    dedup = _dedup_key(city, project, area, point_no, media_type_code)
    rid = uuid.uuid5(NAMESPACE, dedup)

    name = project or point_no or table_name
    return {
        "id": rid,
        "name": name[:100] if name else table_name,
        "type": "offline",
        "category": media_type_code,
        "latitude": lat,
        "longitude": lng,
        "address": address,
        "status": "available",
        # 派生字段
        "level": level,
        "city": city,
        "area": area,
        "project": project,
        "point_no": point_no,
        "source_table": table_name,
        "dedup_key": dedup,
        "media_type_code": media_type_code,
    }


# 模块级默认规则占位（run_etl 启动时替换为 DB 规则或 DEFAULT_RULES）
DEFAULT_RULES_HOLDER: List[Dict] = []


async def run_etl(batch_size: int = 1000, limit: Optional[int] = None) -> Dict[str, Any]:
    """执行全量 ETL：读 SQLite → 派生 level → 幂等 upsert PG。

    返回统计：read / written / distinct_ids / 各媒体类型计数。
    """
    from app.services.level_rule import DEFAULT_RULES

    global DEFAULT_RULES_HOLDER
    # 加载规则：优先 DB，缺失回退默认
    async with AsyncSessionLocal() as db:
        try:
            rules = await load_level_rules(db)
            DEFAULT_RULES_HOLDER = rules if rules else DEFAULT_RULES
        except Exception:  # noqa: BLE001
            DEFAULT_RULES_HOLDER = DEFAULT_RULES

    path = settings.QINGLIN_DB_PATH  # 指向含真实数据的 qinlin_local.db
    stats = {"read": 0, "written": 0, "distinct_ids": 0,
             "by_type": {}, "errors": 0}

    batch: List[Dict[str, Any]] = []
    seen_ids = set()

    async with AsyncSessionLocal() as db:
        for table_name, media_type_code, row in _read_sqlite(path):
            try:
                rec = _build_record(table_name, media_type_code, row)
            except Exception as e:  # noqa: BLE001
                stats["errors"] += 1
                continue
            batch.append(rec)
            seen_ids.add(rec["id"])
            stats["read"] += 1
            stats["by_type"][media_type_code] = stats["by_type"].get(media_type_code, 0) + 1

            if limit and stats["read"] >= limit:
                break
            if len(batch) >= batch_size:
                await _upsert_batch(db, batch)
                stats["written"] += len(batch)
                batch = []
        if batch:
            await _upsert_batch(db, batch)
            stats["written"] += len(batch)

    stats["distinct_ids"] = len(seen_ids)
    return stats


async def _upsert_batch(db, batch: List[Dict[str, Any]]) -> None:
    stmt = pg_insert(MediaResource).values(batch)
    stmt = stmt.on_conflict_do_update(
        index_elements=[MediaResource.id],
        set_={
            MediaResource.level: stmt.excluded.level,
            MediaResource.city: stmt.excluded.city,
            MediaResource.area: stmt.excluded.area,
            MediaResource.project: stmt.excluded.project,
            MediaResource.point_no: stmt.excluded.point_no,
            MediaResource.source_table: stmt.excluded.source_table,
            MediaResource.dedup_key: stmt.excluded.dedup_key,
            MediaResource.media_type_code: stmt.excluded.media_type_code,
            MediaResource.name: stmt.excluded.name,
            MediaResource.address: stmt.excluded.address,
            MediaResource.latitude: stmt.excluded.latitude,
            MediaResource.longitude: stmt.excluded.longitude,
            MediaResource.category: stmt.excluded.category,
            MediaResource.updated_at: func.now(),
        },
    )
    await db.execute(stmt)
    await db.commit()


async def count_etl_rows() -> int:
    """统计 media_resources 中由 ETL 写入的行数（source_table 非空）。"""
    async with AsyncSessionLocal() as db:
        n = await db.scalar(
            select(func.count()).select_from(MediaResource).where(
                MediaResource.source_table.isnot(None)
            )
        )
        return int(n or 0)


if __name__ == "__main__":
    async def _main():
        print("开始全量 ETL（SQLite 只读 → PG media_resources）...")
        result = await run_etl()
        total = await count_etl_rows()
        print("ETL 完成：", result)
        print(f"media_resources 中 ETL 行数（source_table 非空）：{total}")

    asyncio.run(_main())
