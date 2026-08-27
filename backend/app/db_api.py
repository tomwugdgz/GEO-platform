"""
数据库 RESTful API 接口

提供统一的数据库访问 API，支持：
- 获取所有表名和记录数
- 查询指定表的数据（支持分页/筛选）
- 获取表统计信息
- 全文搜索

作者: 寇豆码（Kou）
日期: 2026-03-04
优化: 齐活林（Qi）- 2026-06-20 重写为 FastAPI Router
"""

import os
import json
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from app.db_dao import (
    get_all_tables,
    query_table,
    get_table_stats,
    search_table,
    search_clients as dao_search_clients,
    get_points_by_type,
)
from app.common import (
    setup_logging,
    PDOOHError,
    ValidationError,
    format_error_response,
)

# ── 日志 ────────────────────────────────────────────────────────────────────────
logger = setup_logging(__name__)

# ── 创建 Router ─────────────────────────────────────────────────────────────────
db_api_router = APIRouter(
    prefix="/api/v2/db",
    tags=["数据库访问"],
)


# ── Pydantic 模型 ────────────────────────────────────────────────────────────────

class QueryTableRequest(BaseModel):
    """查询表数据请求"""
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    business_district: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    page: int = 1
    page_size: int = 20
    
    @validator('page')
    def page_must_be_positive(cls, v):
        if v < 1:
            raise ValueError('page 必须 >= 1')
        return v
    
    @validator('page_size')
    def page_size_must_be_valid(cls, v):
        if v < 1 or v > 100:
            raise ValueError('page_size 必须在 1-100 之间')
        return v


# ── 1. 获取所有表 ────────────────────────────────────────────────────────────

@db_api_router.get("/tables")
async def get_tables():
    """
    获取所有表名和记录数
    
    Endpoint: GET /api/v2/db/tables
    
    Returns:
        JSON response:
            {
                "success": true,
                "data": [
                    {"name": "单元门点位", "count": 8114, "columns": [...]},
                    ...
                ],
                "total_tables": 7
            }
        
    Example:
        GET /api/v2/db/tables
    """
    try:
        tables = get_all_tables()
        
        return JSONResponse(
            content={
                "success": True,
                "data": tables,
                "total_tables": len(tables)
            },
            status_code=200
        )
        
    except FileNotFoundError as e:
        logger.error(f"获取表列表失败: 数据库文件不存在 - {str(e)}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "code": "DATABASE_NOT_FOUND"
            },
            status_code=404
        )
        
    except Exception as e:
        logger.error(f"获取表列表失败: {str(e)}", exc_info=True)
        return JSONResponse(
            content={
                "success": False,
                "error": "服务器内部错误",
                "code": "INTERNAL_ERROR"
            },
            status_code=500
        )


# ── 2. 查询表数据 ────────────────────────────────────────────────────────────

@db_api_router.get("/{table_name}")
async def query_table_data(
    table_name: str,
    province: Optional[str] = Query(None, description="省份筛选"),
    city: Optional[str] = Query(None, description="城市筛选"),
    district: Optional[str] = Query(None, description="区域筛选"),
    business_district: Optional[str] = Query(None, description="商圈筛选"),
    min_price: Optional[float] = Query(None, description="最低价格"),
    max_price: Optional[float] = Query(None, description="最高价格"),
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(20, description="每页数量", ge=1, le=100),
):
    """
    查询指定表的数据（支持分页/筛选）
    
    Endpoint: GET /api/v2/db/<table_name>?province=xxx&city=xxx&page=1&page_size=20
    
    Args:
        table_name: 表名（URL 路径参数）
        province: 省份筛选（查询参数）
        city: 城市筛选
        district: 区域筛选
        business_district: 商圈筛选
        min_price: 最低价格
        max_price: 最高价格
        page: 页码（默认 1）
        page_size: 每页数量（默认 20，最大 100）
        
    Returns:
        JSON response:
            {
                "success": true,
                "data": [...],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        
    Example:
        GET /api/v2/db/单元门点位?city=广州&page=1&page_size=20
    """
    try:
        # 构建筛选条件
        filters = {}
        if province:
            filters["省份"] = province
        if city:
            filters["城市"] = city
        if district:
            filters["区域"] = district
        if business_district:
            filters["商圈"] = business_district
        if min_price is not None:
            filters["min_price"] = min_price
        if max_price is not None:
            filters["max_price"] = max_price
        
        # 调用 DAO 层查询
        result = query_table(table_name, filters=filters, page=page, page_size=page_size)
        
        return JSONResponse(
            content={
                "success": True,
                **result
            },
            status_code=200
        )
        
    except ValueError as e:
        # 表不存在或参数错误
        logger.warning(f"查询表数据失败: {str(e)}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "code": "VALIDATION_ERROR"
            },
            status_code=400
        )
        
    except FileNotFoundError as e:
        logger.error(f"查询表数据失败: 数据库文件不存在 - {str(e)}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "code": "DATABASE_NOT_FOUND"
            },
            status_code=404
        )
        
    except Exception as e:
        logger.error(f"查询表数据失败: {str(e)}", exc_info=True)
        return JSONResponse(
            content={
                "success": False,
                "error": "服务器内部错误",
                "code": "INTERNAL_ERROR"
            },
            status_code=500
        )


# ── 3. 获取表统计信息 ────────────────────────────────────────────────────────

@db_api_router.get("/stats/{table_name}")
async def get_table_statistics(table_name: str):
    """
    获取表统计信息
    
    Endpoint: GET /api/v2/db/stats/<table_name>
    
    Args:
        table_name: 表名（URL 路径参数）
        
    Returns:
        JSON response:
            {
                "success": true,
                "data": {
                    "total_records": 8114,
                    "by_city": [{"city": "广州", "count": 1000}, ...],
                    "has_coordinates": 5000,
                    "null_coordinates": 3114
                }
            }
        
    Example:
        GET /api/v2/db/stats/单元门点位
    """
    try:
        stats = get_table_stats(table_name)
        
        return JSONResponse(
            content={
                "success": True,
                "data": stats
            },
            status_code=200
        )
        
    except ValueError as e:
        # 表不存在
        logger.warning(f"获取表统计失败: {str(e)}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "code": "TABLE_NOT_FOUND"
            },
            status_code=404
        )
        
    except FileNotFoundError as e:
        logger.error(f"获取表统计失败: 数据库文件不存在 - {str(e)}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "code": "DATABASE_NOT_FOUND"
            },
            status_code=404
        )
        
    except Exception as e:
        logger.error(f"获取表统计失败: {str(e)}", exc_info=True)
        return JSONResponse(
            content={
                "success": False,
                "error": "服务器内部错误",
                "code": "INTERNAL_ERROR"
            },
            status_code=500
        )


# ── 4. 全文搜索 ────────────────────────────────────────────────────────────────

@db_api_router.get("/search/{table_name}")
async def search_table_data(
    table_name: str,
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(100, description="返回数量限制", ge=1, le=500),
):
    """
    全文搜索
    
    Endpoint: GET /api/v2/db/search/<table_name>?q=xxx&limit=100
    
    Args:
        table_name: 表名（URL 路径参数）
        q: 搜索关键词（查询参数，必需）
        limit: 返回数量限制（默认 100，最大 500）
        
    Returns:
        JSON response:
            {
                "success": true,
                "data": [...],
                "total": 50
            }
        
    Example:
        GET /api/v2/db/search/单元门点位?q=广州&limit=50
    """
    try:
        results = search_table(table_name, keyword=q, limit=limit)
        
        return JSONResponse(
            content={
                "success": True,
                "data": results,
                "total": len(results)
            },
            status_code=200
        )
        
    except ValueError as e:
        # 表不存在或参数错误
        logger.warning(f"搜索表数据失败: {str(e)}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "code": "VALIDATION_ERROR"
            },
            status_code=400
        )
        
    except FileNotFoundError as e:
        logger.error(f"搜索表数据失败: 数据库文件不存在 - {str(e)}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "code": "DATABASE_NOT_FOUND"
            },
            status_code=404
        )
        
    except Exception as e:
        logger.error(f"搜索表数据失败: {str(e)}", exc_info=True)
        return JSONResponse(
            content={
                "success": False,
                "error": "服务器内部错误",
                "code": "INTERNAL_ERROR"
            },
            status_code=500
        )


# ── 5. 搜索客户信息 ────────────────────────────────────────────────────────────

@db_api_router.get("/clients/search")
async def search_clients(
    keyword: str = Query(..., description="关键词（匹配客户简称或品牌名称）"),
    city: Optional[str] = Query(None, description="决策城市筛选"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    limit: int = Query(20, description="返回数量限制", ge=1, le=500),
):
    """
    搜索客户信息（从"客户通讯录"表）
    
    Endpoint: GET /api/v2/db/clients/search?keyword=xxx&city=xxx&limit=10
    
    Args:
        keyword: 关键词（查询参数，必需）
        city: 决策城市筛选
        industry: 行业筛选
        limit: 返回数量限制（默认 20，最大 500）
        
    Returns:
        JSON response:
            {
                "success": true,
                "data": [
                    {"客户简称": "华为技术", "品牌名称": "华为", "决策城市": "深圳", ...},
                    ...
                ],
                "total": 10
            }
        
    Example:
        GET /api/v2/db/clients/search?keyword=华为&limit=10
    """
    try:
        results = dao_search_clients(keyword=keyword, city=city, industry=industry, limit=limit)
        
        return JSONResponse(
            content={
                "success": True,
                "data": results,
                "total": len(results)
            },
            status_code=200
        )
        
    except ValueError as e:
        # 参数错误
        logger.warning(f"搜索客户失败: {str(e)}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "code": "VALIDATION_ERROR"
            },
            status_code=400
        )
        
    except FileNotFoundError as e:
        logger.error(f"搜索客户失败: 数据库文件不存在 - {str(e)}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "code": "DATABASE_NOT_FOUND"
            },
            status_code=404
        )
        
    except Exception as e:
        logger.error(f"搜索客户失败: {str(e)}", exc_info=True)
        return JSONResponse(
            content={
                "success": False,
                "error": "服务器内部错误",
                "code": "INTERNAL_ERROR"
            },
            status_code=500
        )


# ── 6. 按媒体类型获取点位 ────────────────────────────────────────────────────

@db_api_router.get("/points/{point_type}")
async def get_points_by_media_type(
    point_type: str,
    city: Optional[str] = Query(None, description="城市筛选"),
    district: Optional[str] = Query(None, description="区域筛选"),
    limit: int = Query(50, description="返回数量限制", ge=1, le=500),
):
    """
    按媒体类型获取点位数据
    
    Endpoint: GET /api/v2/db/points/<point_type>?city=xxx&limit=50
    
    Args:
        point_type: 点位类型（URL 路径参数），可选值：
            - "unit_door": 单元门点位
            - "access_door": 门禁点位
            - "dao_zha": 道闸点位
            - "led": 商场LED点位
            - "smart_screen": 智能屏202507
            - "smart_screen_l9": 智能屏L9
        city: 城市筛选
        district: 区域筛选
        limit: 返回数量限制（默认 50，最大 500）
        
    Returns:
        JSON response:
            {
                "success": true,
                "data": [...],
                "total": 100
            }
        
    Example:
        GET /api/v2/db/points/unit_door?city=广州&limit=50
    """
    try:
        result = get_points_by_type(point_type=point_type, city=city, district=district, limit=limit)
        
        return JSONResponse(
            content={
                "success": True,
                **result
            },
            status_code=200
        )
        
    except ValueError as e:
        # 不支持的点位类型
        logger.warning(f"按类型获取点位失败: {str(e)}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "code": "INVALID_POINT_TYPE"
            },
            status_code=400
        )
        
    except FileNotFoundError as e:
        logger.error(f"按类型获取点位失败: 数据库文件不存在 - {str(e)}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "code": "DATABASE_NOT_FOUND"
            },
            status_code=404
        )
        
    except Exception as e:
        logger.error(f"按类型获取点位失败: {str(e)}", exc_info=True)
        return JSONResponse(
            content={
                "success": False,
                "error": "服务器内部错误",
                "code": "INTERNAL_ERROR"
            },
            status_code=500
        )


# ── 7. API 文档 ────────────────────────────────────────────────────────────────

@db_api_router.get("/docs")
async def get_api_docs():
    """
    获取 API 文档
    
    Endpoint: GET /api/v2/db/docs
    
    Returns:
        JSON response with API documentation
        
    Example:
        GET /api/v2/db/docs
    """
    docs = {
        "title": "pDOOH 数据库访问 API",
        "version": "1.0.0",
        "description": "提供统一的数据库访问接口，支持点位数据查询、统计、搜索等功能",
        "endpoints": [
            {
                "path": "/api/v2/db/tables",
                "method": "GET",
                "description": "获取所有表名和记录数"
            },
            {
                "path": "/api/v2/db/{table_name}",
                "method": "GET",
                "description": "查询指定表的数据（支持分页/筛选）"
            },
            {
                "path": "/api/v2/db/stats/{table_name}",
                "method": "GET",
                "description": "获取表统计信息"
            },
            {
                "path": "/api/v2/db/search/{table_name}",
                "method": "GET",
                "description": "全文搜索"
            },
            {
                "path": "/api/v2/db/clients/search",
                "method": "GET",
                "description": "搜索客户信息"
            },
            {
                "path": "/api/v2/db/points/{point_type}",
                "method": "GET",
                "description": "按媒体类型获取点位"
            }
        ]
    }
    
    return JSONResponse(
        content=docs,
        status_code=200
    )


# ── 模块测试 ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 简单测试
    import uvicorn
    from fastapi import FastAPI
    
    test_app = FastAPI(title="数据库 API 测试")
    test_app.include_router(db_api_router)
    
    print("启动测试服务器: http://127.0.0.1:9000")
    print("API 文档: http://127.0.0.1:9000/docs")
    uvicorn.run(test_app, host="127.0.0.1", port=9000)
