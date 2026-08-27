"""
数据库访问层（DAO）- qinlin_local.db

提供统一的数据库访问接口，支持：
- 获取所有表名和记录数
- 按条件查询点位数据（支持省份/城市/区域/商圈筛选）
- 获取统计数据（总记录数/按城市分组统计等）
- 全文搜索

作者: 寇豆码（Kou）
日期: 2026-03-04
"""

import sqlite3
import os
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

# ── 数据库路径 ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# 主库路径优先级：
#   1. config.QINGLIN_DB_PATH（支持环境变量 QINGLIN_DB_PATH 覆盖）
#   2. backend/data/qinlin_local.db（真实主库，历史资产，文件名不改）
# 若 config 不可用（极端情况下的裸脚本调用），回退到默认路径，保证模块仍可 import。
try:
    from app.config import settings as _settings

    DB_PATH = Path(_settings.QINGLIN_DB_PATH)
except Exception:  # noqa: BLE001 — 配置缺失不应导致 DAO 不可用
    DB_PATH = BASE_DIR / "data" / "qinlin_local.db"

# 二级兜底：脱敏样本库（不再指向真实主库，避免与 DB_PATH 指向同一文件造成语义混乱）
LEGACY_DB_PATH = BASE_DIR / "data" / "qinlin_local_sample.db"
# 脱敏样本库，最后兜底（可提交到 Git）
SAMPLE_DB_PATH = BASE_DIR / "data" / "qinlin_local_sample.db"

# ── 日志 ────────────────────────────────────────────────────────────────────────
import logging
logger = logging.getLogger(__name__)

# ── 点位类型映射 ────────────────────────────────────────────────────────────────

# 点位类型 -> 表名映射
type_to_table = {
    "unit_door": "单元门点位",
    "access_door": "门禁点位",
    "dao_zha": "道闸点位",
    "led": "商场LED点位",
    "smart_screen": "智能屏202507",
    "smart_screen_l9": "智能屏L9"
}


# ── 数据库连接 ────────────────────────────────────────────────────────────────────

def get_db_connection() -> sqlite3.Connection:
    """
    获取数据库连接（自动兜底）。
    
    优先级：
    1. DB_PATH —— config.QINGLIN_DB_PATH 指定的库，默认 qinlin_local.db（真实主库，含敏感字段）
    2. LEGACY_DB_PATH —— qinlin_local.db（历史命名，兼容既有部署）
    3. SAMPLE_DB_PATH —— qinlin_local_sample.db（样本数据库，已脱敏，可提交到 Git）
    
    Returns:
        sqlite3.Connection: SQLite 数据库连接对象
        
    Raises:
        FileNotFoundError: 三个数据库文件都不存在时抛出
    """
    for candidate, note in (
        (DB_PATH, ""),
        (LEGACY_DB_PATH, "主库不存在，回退到历史命名库"),
        (SAMPLE_DB_PATH, "完整数据库不存在，使用样本库"),
    ):
        if not candidate.exists():
            continue
        if note:
            logger.warning(f"{note}: {candidate}")
        conn = sqlite3.connect(str(candidate))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    raise FileNotFoundError(
        f"数据库文件不存在！\n"
        f"请放置完整数据库到：{DB_PATH}\n"
        f"或放置历史命名库到：{LEGACY_DB_PATH}\n"
        f"或放置样本数据库到：{SAMPLE_DB_PATH}"
    )


# ── 1. 获取所有表名和记录数 ───────────────────────────────────────────────────

def get_all_tables() -> List[Dict[str, Any]]:
    """
    获取数据库中所有表的信息（表名、记录数）
    
    Returns:
        List[Dict[str, Any]]: 表信息列表，每个元素包含：
            - name: 表名
            - count: 记录数
            - columns: 字段列表
            
    Example:
        >>> get_all_tables()
        [
            {"name": "单元门点位", "count": 8114, "columns": ["省份", "城市", ...]},
            {"name": "商场LED点位", "count": 1365, "columns": ["省份", "城市", ...]},
            ...
        ]
    """
    logger.info("获取所有表信息")
    
    conn = get_db_connection()
    try:
        # 查询所有表名（排除 SQLite 系统表）
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = cursor.fetchall()
        
        result = []
        for row in tables:
            table_name = row["name"]
            
            # 获取记录数
            count_cursor = conn.execute(f'SELECT COUNT(*) as cnt FROM "{table_name}"')
            count = count_cursor.fetchone()["cnt"]
            
            # 获取字段列表
            schema_cursor = conn.execute(f'PRAGMA table_info("{table_name}")')
            columns = [col["name"] for col in schema_cursor.fetchall()]
            
            result.append({
                "name": table_name,
                "count": count,
                "columns": columns
            })
        
        logger.info(f"找到 {len(result)} 个表")
        return result
        
    finally:
        conn.close()


# ── 2. 查询表数据（支持筛选和分页）────────────────────────────────────────────

def query_table(
    table_name: str,
    filters: Optional[Dict[str, Any]] = None,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """
    查询指定表的数据（支持筛选和分页）
    
    Args:
        table_name: 表名（支持中文表名，如 "单元门点位"）
        filters: 筛选条件字典，支持的键：
            - province: 省份（模糊匹配）
            - city: 城市（模糊匹配）
            - district: 区域/行政区（模糊匹配）
            - business_district: 商圈（模糊匹配）
            - min_price: 最低价格
            - max_price: 最高价格
        page: 页码（从 1 开始）
        page_size: 每页记录数（默认 20，最大 1000）
        
    Returns:
        Dict[str, Any]: 包含以下字段：
            - data: 数据列表
            - total: 总记录数
            - page: 当前页码
            - page_size: 每页记录数
            - total_pages: 总页数
            
    Raises:
        ValueError: 表名不存在或参数无效
        
    Example:
        >>> query_table("单元门点位", filters={"city": "广州", "district": "天河"}, page=1, page_size=20)
        {
            "data": [...],
            "total": 150,
            "page": 1,
            "page_size": 20,
            "total_pages": 8
        }
    """
    logger.info(f"查询表: table={table_name}, filters={filters}, page={page}, page_size={page_size}")
    
    # 参数验证
    if page < 1:
        raise ValueError("page 必须大于等于 1")
    if page_size < 1 or page_size > 1000:
        raise ValueError("page_size 必须在 1-1000 之间")
    
    filters = filters or {}
    
    conn = get_db_connection()
    try:
        # 验证表是否存在并获取字段列表
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        if not cursor.fetchone():
            raise ValueError(f"表不存在: {table_name}")
        
        # 获取表的字段列表（用于检查价格字段是否存在）
        schema_cursor = conn.execute(f'PRAGMA table_info("{table_name}")')
        existing_columns = [col[1] for col in schema_cursor.fetchall()]
        logger.debug(f"表 {table_name} 的字段: {existing_columns}")
        
        # 构建 WHERE 子句
        where_clauses = []
        params = []
        
        # 省份筛选
        if filters.get("province"):
            where_clauses.append('"省份" LIKE ?')
            params.append(f"%{filters['province']}%")
        
        # 城市筛选
        if filters.get("city"):
            where_clauses.append('"城市" LIKE ?')
            params.append(f"%{filters['city']}%")
        
        # 区域/行政区筛选
        if filters.get("district"):
            # 尝试匹配"区域"或"行政区"字段
            where_clauses.append('("区域" LIKE ? OR "行政区" LIKE ?)')
            params.append(f"%{filters['district']}%")
            params.append(f"%{filters['district']}%")
        
        # 商圈筛选
        if filters.get("business_district"):
            where_clauses.append('"商圈" LIKE ?')
            params.append(f"%{filters['business_district']}%")
        
        # 价格范围筛选（智能检查字段是否存在）
        price_clauses = []
        if filters.get("min_price") is not None:
            # 检查"楼盘价格"字段是否存在
            if "楼盘价格" in existing_columns:
                price_clauses.append('"楼盘价格" >= ?')
                params.append(filters['min_price'])
            # 检查"刊例价"字段是否存在
            if "刊例价" in existing_columns:
                price_clauses.append('"刊例价" >= ?')
                params.append(filters['min_price'])
            
            if price_clauses:
                where_clauses.append("(" + " OR ".join(price_clauses) + ")")
            else:
                logger.warning(f"表 {table_name} 没有价格字段（楼盘价格/刊例价），跳过价格过滤")
        
        if filters.get("max_price") is not None:
            # 重新检查（因为上面可能已经添加了部分条件）
            price_clauses_max = []
            if "楼盘价格" in existing_columns:
                price_clauses_max.append('"楼盘价格" <= ?')
                params.append(filters['max_price'])
            if "刊例价" in existing_columns:
                price_clauses_max.append('"刊例价" <= ?')
                params.append(filters['max_price'])
            
            if price_clauses_max:
                where_clauses.append("(" + " OR ".join(price_clauses_max) + ")")
            else:
                logger.warning(f"表 {table_name} 没有价格字段（楼盘价格/刊例价），跳过价格过滤")
        
        # 组装 WHERE 子句
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)
        
        # 查询总记录数
        count_sql = f'SELECT COUNT(*) as cnt FROM "{table_name}" {where_sql}'
        cursor = conn.execute(count_sql, params)
        total = cursor.fetchone()["cnt"]
        
        # 计算分页
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        offset = (page - 1) * page_size
        
        # 查询数据
        data_sql = f'SELECT * FROM "{table_name}" {where_sql} LIMIT ? OFFSET ?'
        cursor = conn.execute(data_sql, params + [page_size, offset])
        
        # 转换为字典列表
        columns = [desc[0] for desc in cursor.description]
        data = []
        for row in cursor.fetchall():
            data.append(dict(zip(columns, row)))
        
        logger.info(f"查询成功: 返回 {len(data)} 条记录，总计 {total} 条")
        
        return {
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
        
    finally:
        conn.close()


# ── 3. 获取表统计信息 ───────────────────────────────────────────────────────────

def get_table_stats(table_name: str) -> Dict[str, Any]:
    """
    获取表的统计信息
    
    Args:
        table_name: 表名
        
    Returns:
        Dict[str, Any]: 统计信息，包含：
            - total_count: 总记录数
            - city_stats: 按城市分组的统计（城市名 -> 记录数）
            - province_stats: 按省份分组的统计（省份名 -> 记录数）
            - has_coordinates: 有经纬度的记录数
            - null_coordinates: 缺少经纬度的记录数
            
    Raises:
        ValueError: 表名不存在
        
    Example:
        >>> get_table_stats("单元门点位")
        {
            "total_count": 8114,
            "city_stats": {"广州": 3500, "深圳": 2500, ...},
            "province_stats": {"广东省": 7000, "湖南省": 1114, ...},
            "has_coordinates": 7500,
            "null_coordinates": 614
        }
    """
    logger.info(f"获取表统计信息: table={table_name}")
    
    conn = get_db_connection()
    try:
        # 验证表是否存在
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        if not cursor.fetchone():
            raise ValueError(f"表不存在: {table_name}")
        
        # 获取字段列表
        cursor = conn.execute(f'PRAGMA table_info("{table_name}")')
        columns_info = cursor.fetchall()
        column_names = [col["name"] for col in columns_info]
        
        result = {}
        
        # 总记录数
        cursor = conn.execute(f'SELECT COUNT(*) as cnt FROM "{table_name}"')
        result["total_count"] = cursor.fetchone()["cnt"]
        
        # 按城市分组统计（如果表有"城市"字段）
        if "城市" in column_names:
            cursor = conn.execute(
                f'SELECT "城市", COUNT(*) as cnt FROM "{table_name}" GROUP BY "城市" ORDER BY cnt DESC'
            )
            result["city_stats"] = {row["城市"]: row["cnt"] for row in cursor.fetchall()}
        
        # 按省份分组统计（如果表有"省份"字段）
        if "省份" in column_names:
            cursor = conn.execute(
                f'SELECT "省份", COUNT(*) as cnt FROM "{table_name}" GROUP BY "省份" ORDER BY cnt DESC'
            )
            result["province_stats"] = {row["省份"]: row["cnt"] for row in cursor.fetchall()}
        
        # 经纬度统计（如果表有"经度"和"纬度"字段）
        if "经度" in column_names and "纬度" in column_names:
            cursor = conn.execute(
                f'SELECT COUNT(*) as cnt FROM "{table_name}" WHERE "经度" IS NOT NULL AND "纬度" IS NOT NULL'
            )
            result["has_coordinates"] = cursor.fetchone()["cnt"]
            result["null_coordinates"] = result["total_count"] - result["has_coordinates"]
        
        logger.info(f"统计信息获取成功: {table_name}")
        return result
        
    finally:
        conn.close()


# ── 4. 全文搜索 ─────────────────────────────────────────────────────────────────

def search_table(table_name: str, keyword: str) -> List[Dict[str, Any]]:
    """
    在指定表中搜索包含关键词的记录（全文搜索）
    
    Args:
        table_name: 表名
        keyword: 搜索关键词
        
    Returns:
        List[Dict[str, Any]]: 匹配的记录列表（最多返回 100 条）
        
    Raises:
        ValueError: 表名不存在
        
    Example:
        >>> search_table("客户通讯录", "华为")
        [
            {"客户简称": "华为技术", "品牌名称": "华为", "决策城市": "深圳", ...},
            ...
        ]
    """
    logger.info(f"搜索表: table={table_name}, keyword={keyword}")
    
    if not keyword:
        raise ValueError("搜索关键词不能为空")
    
    conn = get_db_connection()
    try:
        # 验证表是否存在
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        if not cursor.fetchone():
            raise ValueError(f"表不存在: {table_name}")
        
        # 获取字段列表
        cursor = conn.execute(f'PRAGMA table_info("{table_name}")')
        columns_info = cursor.fetchall()
        column_names = [col["name"] for col in columns_info]
        
        # 构建 OR 条件（在所有字段中搜索）
        or_clauses = []
        params = []
        for col in column_names:
            or_clauses.append(f'"{col}" LIKE ?')
            params.append(f"%{keyword}%")
        
        where_sql = " OR ".join(or_clauses)
        
        # 执行搜索（限制返回 100 条）
        sql = f'SELECT * FROM "{table_name}" WHERE {where_sql} LIMIT 100'
        cursor = conn.execute(sql, params)
        
        # 转换为字典列表
        columns = [desc[0] for desc in cursor.description]
        data = []
        for row in cursor.fetchall():
            data.append(dict(zip(columns, row)))
        
        logger.info(f"搜索完成: 找到 {len(data)} 条匹配记录")
        return data
        
    finally:
        conn.close()


# ── 5. 获取客户信息（专用接口）─────────────────────────────────────────────────

def search_clients(
    keyword: Optional[str] = None,
    city: Optional[str] = None,
    industry: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    搜索客户信息（从"客户通讯录"表）
    
    Args:
        keyword: 关键词（匹配客户简称或品牌名称）
        city: 决策城市筛选
        industry: 行业筛选
        limit: 返回数量限制（默认 20，最大 500）
        
    Returns:
        List[Dict[str, Any]]: 客户信息列表
        
    Example:
        >>> search_clients(keyword="华为", city="深圳")
        [
            {"客户简称": "华为技术", "品牌名称": "华为", "决策城市": "深圳", "行业": "通信", ...},
            ...
        ]
    """
    logger.info(f"搜索客户: keyword={keyword}, city={city}, industry={industry}, limit={limit}")
    
    # 参数验证
    if limit < 1 or limit > 500:
        raise ValueError("limit 必须在 1-500 之间")
    
    conn = get_db_connection()
    try:
        # 检查"客户通讯录"表是否存在
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='客户通讯录'"
        )
        if not cursor.fetchone():
            raise ValueError("表不存在: 客户通讯录")
        
        # 构建 WHERE 子句
        where_clauses = []
        params = []
        
        if keyword:
            where_clauses.append('("客户简称" LIKE ? OR "品牌名称" LIKE ?)')
            params.append(f"%{keyword}%")
            params.append(f"%{keyword}%")
        
        if city:
            where_clauses.append('"决策城市" LIKE ?')
            params.append(f"%{city}%")
        
        if industry:
            where_clauses.append('"行业" LIKE ?')
            params.append(f"%{industry}%")
        
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)
        
        # 执行查询
        sql = f'SELECT * FROM "客户通讯录" {where_sql} LIMIT ?'
        cursor = conn.execute(sql, params + [limit])
        
        # 转换为字典列表
        columns = [desc[0] for desc in cursor.description]
        data = []
        for row in cursor.fetchall():
            data.append(dict(zip(columns, row)))
        
        logger.info(f"客户搜索完成: 找到 {len(data)} 条记录")
        return data
        
    finally:
        conn.close()


# ── 6. 获取特定点位数据（按媒体类型）───────────────────────────────────────────

def get_points_by_type(
    point_type: str,
    city: Optional[str] = None,
    district: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    按媒体类型获取点位数据
    
    Args:
        point_type: 点位类型，可选值：
            - "unit_door": 单元门点位
            - "access_door": 门禁点位
            - "dao_zha": 道闸点位
            - "led": 商场LED点位
            - "smart_screen": 智能屏202507
            - "smart_screen_l9": 智能屏L9
        city: 城市筛选
        district: 区域筛选
        limit: 返回数量限制
        
    Returns:
        Dict[str, Any]: 点位数据
        
    Raises:
        ValueError: 不支持的点位类型
    """
    logger.info(f"按类型获取点位: type={point_type}, city={city}, district={district}, limit={limit}")
    
    # 检查点位类型是否支持（使用模块级映射）
    if point_type not in type_to_table:
        raise ValueError(f"不支持的点位类型: {point_type}")
    
    table_name = type_to_table[point_type]
    
    # 构建筛选条件
    filters = {}
    if city:
        filters["city"] = city
    if district:
        filters["district"] = district
    
    # 调用通用查询接口
    return query_table(table_name, filters=filters, page=1, page_size=limit)


# ── 模块测试 ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("数据库访问层（DAO）测试")
    print("=" * 60)
    
    # 测试 1: 获取所有表
    print("\n[测试 1] 获取所有表信息:")
    tables = get_all_tables()
    for t in tables:
        print(f"  - {t['name']}: {t['count']} 条记录")
    
    # 测试 2: 查询表数据
    if tables:
        first_table = tables[0]['name']
        print(f"\n[测试 2] 查询表数据: {first_table}")
        result = query_table(first_table, page=1, page_size=5)
        print(f"  总记录数: {result['total']}")
        print(f"  第 1 页数据（前 5 条）:")
        for row in result['data'][:5]:
            print(f"    {row}")
    
    # 测试 3: 获取统计信息
    if tables:
        print(f"\n[测试 3] 获取统计信息: {first_table}")
        stats = get_table_stats(first_table)
        print(f"  总记录数: {stats['total_count']}")
        if 'city_stats' in stats:
            print(f"  按城市统计（前 5）: {dict(list(stats['city_stats'].items())[:5])}")
    
    # 测试 4: 搜索
    if tables and tables[0]['count'] > 0:
        print(f"\n[测试 4] 搜索测试:")
        results = search_table(first_table, keyword="广州")
        print(f"  在 {first_table} 中搜索 '广州'，找到 {len(results)} 条记录")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
