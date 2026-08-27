"""
MCP Server — pDOOH A2A MCP 服务器
端口: 5002
功能: 提供 22 个 MCP 工具，涵盖点位查询、投放管理、ROI 计算等功能

优化点：
1. 性能优化：添加缓存机制（functools.lru_cache + 自定义 TTL 缓存）
2. 稳定性优化：添加重试逻辑、降级逻辑、健康检查
3. 代码质量：添加类型提示、文档字符串、遵循 Google 风格规范
4. 错误处理：统一异常类、标准化错误响应格式
"""

import os
import sys
import json
import time
import asyncio
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta
from functools import lru_cache

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

# ── 导入公共模块 ────────────────────────────────────────────────────────────────
from app.common import (
    setup_logging,
    PDOOHError,
    ValidationError,
    monitor_performance,
    monitor_performance_async,
    cached,
    retry_async,
    validate_params,
    generate_request_id,
    format_error_response,
)

# ── 导入数据库访问层 ────────────────────────────────────────────────────────────
from app.db_dao import (
    get_all_tables,
    query_table,
    get_table_stats,
    search_table,
    search_clients as dao_search_clients,
    get_points_by_type,
)

# ── 日志 ────────────────────────────────────────────────────────────────────────
logger = setup_logging("mcp_server", log_file="logs/mcp_server.log")
logger.info("MCP Server 启动中...")

router = APIRouter(prefix="/api/v2/mcp/pdooh", tags=["MCP Server"])

# ── 配置 ────────────────────────────────────────────────────────────────────────
MCP_SERVICE_URL = os.getenv("MCP_SERVICE_URL", "http://47.253.159.62:5002")
TIMEOUT = 30.0  # HTTP 请求超时时间（秒）

# ── 内存缓存 ────────────────────────────────────────────────────────────────────
_cache = {}
_cache_times = {}

def get_from_cache(key: str, ttl: int = 300) -> Optional[Any]:
    """
    从内存缓存获取数据
    
    Args:
        key: 缓存键
        ttl: 过期时间（秒，默认 300 秒 = 5 分钟）
        
    Returns:
        缓存的数据，如果不存在或已过期则返回 None
    """
    if key not in _cache:
        return None
    
    # 检查是否过期
    if time.time() - _cache_times[key] > ttl:
        del _cache[key]
        del _cache_times[key]
        return None
    
    return _cache[key]

def set_to_cache(key: str, value: Any) -> None:
    """
    设置内存缓存
    
    Args:
        key: 缓存键
        value: 缓存值
    """
    _cache[key] = value
    _cache_times[key] = time.time()

# ── HTTP 客户端 ─────────────────────────────────────────────────────────────────
@retry_async(max_attempts=3, delay=1.0, exceptions=(httpx.TimeoutException, httpx.ConnectError))
async def call_mcp_service(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    调用 MCP 服务（带重试）
    
    Args:
        tool_name: 工具名称
        arguments: 工具参数
        
    Returns:
        Dict[str, Any]: MCP 服务响应
        
    Raises:
        httpx.TimeoutException: 请求超时
        httpx.ConnectError: 连接错误
        HTTPException: MCP 服务返回错误
    """
    cache_key = f"{tool_name}:{json.dumps(arguments, sort_keys=True)}"
    cached_result = get_from_cache(cache_key)
    if cached_result:
        logger.info(f"缓存命中: {tool_name}")
        return cached_result
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(
            f"{MCP_SERVICE_URL}/tools/call",
            json={"name": tool_name, "arguments": arguments}
        )
        response.raise_for_status()
        result = response.json()
        
        # 缓存成功响应（TTL 5 分钟）
        set_to_cache(cache_key, result, ttl=300)
        
        return result

# ── 请求/响应模型 ──────────────────────────────────────────────────────────────

class ToolCallRequest(BaseModel):
    """MCP 工具调用请求"""
    name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(default={}, description="工具参数")

class ToolCallResponse(BaseModel):
    """MCP 工具调用响应"""
    content: List[Dict[str, str]]

# ── 1.1 核心投放工具 ────────────────────────────────────────────────────────────

@router.post("/tools/call", response_model=Dict[str, Any])
@monitor_performance_async(logger=logger)
async def call_tool(request: ToolCallRequest):
    """
    统一工具调用入口
    
    Args:
        request: 工具调用请求
        
    Returns:
        Dict[str, Any]: 工具调用结果
        
    Raises:
        HTTPException: 工具调用失败
    """
    request_id = generate_request_id("mcp")
    logger.info(f"收到工具调用请求 [{request_id}]: tool={request.name}, arguments={request.arguments}")
    
    try:
        # 参数验证
        if not request.name:
            raise ValidationError(message="工具名称不能为空", details={"name": request.name})
        
        # 调用对应的工具函数
        tool_handlers = {
            # 1.1 核心投放工具
            "pdooh_query_screens": query_screens,
            "pdooh_get_screen_audience": get_screen_audience,
            "pdooh_create_campaign": create_campaign,
            "pdooh_query_campaigns": query_campaigns,
            "pdooh_submit_creative": submit_creative,
            "pdooh_query_report": query_report,
            "pdooh_compliance_check": compliance_check,
            
            # 1.2 本地数据库工具
            "pdooh_query_local_screens": query_local_screens,
            "pdooh_query_local_stats": query_local_stats,
            "pdooh_search_local_community": search_local_community,
            "pdooh_audience_insight": audience_insight,
            
            # 1.3 点位查询工具
            "pdooh_query_access_points": query_access_points,
            "pdooh_query_smart_frames": query_smart_frames,
            "pdooh_query_daocha_points": query_daocha_points,
            "pdooh_query_led_points": query_led_points,
            "pdooh_query_elevator_frames": query_elevator_frames,
            "pdooh_query_smart_screen_2025": query_smart_screen_2025,
            "pdooh_query_shadow_points": query_shadow_points,
            
            # 1.4 资源统计工具
            "pdooh_query_city_resources": query_city_resources,
            "pdooh_query_city_summary": query_city_summary,
            "pdooh_query_customers": query_customers,
            
            # 1.5 ROI 计算工具
            "pdooh_calc_roi": calc_roi,
            
            # 1.6 新增：本地数据库直接查询工具（qinlin_local.db）
            "pdooh_query_pdooh_points": query_pdooh_points,
            "pdooh_get_point_stats": get_point_stats,
            "pdooh_search_clients": search_clients_mcp,
        }
        
        if request.name not in tool_handlers:
            raise HTTPException(status_code=404, detail=f"未知工具: {request.name}")
        
        # 调用工具处理函数
        handler = tool_handlers[request.name]
        result = await handler(**request.arguments)
        
        logger.info(f"工具调用请求处理完成 [{request_id}]: tool={request.name}")
        return result
        
    except ValidationError as e:
        logger.warning(f"参数验证失败 [{request_id}]: {e.message}, details={e.details}")
        return JSONResponse(status_code=400, content=format_error_response(e, request_id=request_id))
    except Exception as e:
        logger.error(f"工具调用失败 [{request_id}]: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content=format_error_response(e, request_id=request_id))

# ── 工具处理函数 ──────────────────────────────────────────────────────────────

@cached(ttl=300, maxsize=100)
@monitor_performance_async(logger=logger)
async def query_screens(
    city: str = None,
    district: str = None,
    min_house_price: float = None,
    tags: List[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    查询智能屏
    
    Args:
        city: 城市名称
        district: 区县名称
        min_house_price: 最低房价（万元/㎡）
        tags: 标签列表（如 ["母婴", "美妆"]）
        limit: 返回数量限制
        
    Returns:
        Dict[str, Any]: 智能屏列表
    """
    logger.info(f"查询智能屏: city={city}, district={district}, limit={limit}")
    
    # 参数验证
    if limit <= 0 or limit > 1000:
        raise ValidationError(message="limit 必须在 1-1000 之间", details={"limit": limit})
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_query_screens", {
        "city": city,
        "district": district,
        "min_house_price": min_house_price,
        "tags": tags,
        "limit": limit
    })
    
    return result

@cached(ttl=300, maxsize=100)
@monitor_performance_async(logger=logger)
async def get_screen_audience(screen_id: int) -> Dict[str, Any]:
    """
    获取屏人群画像
    
    Args:
        screen_id: 屏幕 ID
        
    Returns:
        Dict[str, Any]: 人群画像数据
    """
    logger.info(f"获取屏人群画像: screen_id={screen_id}")
    
    # 参数验证
    if screen_id <= 0:
        raise ValidationError(message="screen_id 必须大于 0", details={"screen_id": screen_id})
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_get_screen_audience", {
        "screen_id": screen_id
    })
    
    return result

@monitor_performance_async(logger=logger)
async def create_campaign(
    name: str,
    screen_ids: List[int],
    start_date: str,
    end_date: str,
    budget: float,
    creative_text: str
) -> Dict[str, Any]:
    """
    创建投放计划
    
    Args:
        name: 投放计划名称
        screen_ids: 屏幕 ID 列表
        start_date: 开始日期（YYYY-MM-DD）
        end_date: 结束日期（YYYY-MM-DD）
        budget: 预算（元）
        creative_text: 创意文案
        
    Returns:
        Dict[str, Any]: 创建的投放计划信息
    """
    logger.info(f"创建投放计划: name={name}, budget={budget}")
    
    # 参数验证
    if not name:
        raise ValidationError(message="投放计划名称不能为空", details={"name": name})
    if not screen_ids or len(screen_ids) == 0:
        raise ValidationError(message="屏幕 ID 列表不能为空", details={"screen_ids": screen_ids})
    if budget <= 0:
        raise ValidationError(message="预算必须大于 0", details={"budget": budget})
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_create_campaign", {
        "name": name,
        "screen_ids": screen_ids,
        "start_date": start_date,
        "end_date": end_date,
        "budget": budget,
        "creative_text": creative_text
    })
    
    return result

@cached(ttl=60, maxsize=50)
@monitor_performance_async(logger=logger)
async def query_campaigns(status: str = None) -> Dict[str, Any]:
    """
    查询投放计划
    
    Args:
        status: 投放状态（如 "running"、"paused"、"completed"）
        
    Returns:
        Dict[str, Any]: 投放计划列表
    """
    logger.info(f"查询投放计划: status={status}")
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_query_campaigns", {
        "status": status
    })
    
    return result

@monitor_performance_async(logger=logger)
async def submit_creative(campaign_id: int, content: str, ai_generated: bool = False) -> Dict[str, Any]:
    """
    提交创意
    
    Args:
        campaign_id: 投放计划 ID
        content: 创意内容
        ai_generated: 是否由 AI 生成
        
    Returns:
        Dict[str, Any]: 提交结果
    """
    logger.info(f"提交创意: campaign_id={campaign_id}, ai_generated={ai_generated}")
    
    # 参数验证
    if campaign_id <= 0:
        raise ValidationError(message="campaign_id 必须大于 0", details={"campaign_id": campaign_id})
    if not content:
        raise ValidationError(message="创意内容不能为空", details={"content": content})
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_submit_creative", {
        "campaign_id": campaign_id,
        "content": content,
        "ai_generated": ai_generated
    })
    
    return result

@cached(ttl=300, maxsize=50)
@monitor_performance_async(logger=logger)
async def query_report(campaign_id: int) -> Dict[str, Any]:
    """
    查询投放报告
    
    Args:
        campaign_id: 投放计划 ID
        
    Returns:
        Dict[str, Any]: 投放报告数据
    """
    logger.info(f"查询投放报告: campaign_id={campaign_id}")
    
    # 参数验证
    if campaign_id <= 0:
        raise ValidationError(message="campaign_id 必须大于 0", details={"campaign_id": campaign_id})
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_query_report", {
        "campaign_id": campaign_id
    })
    
    return result

@monitor_performance_async(logger=logger)
async def compliance_check(content: str, industry: str = None) -> Dict[str, Any]:
    """
    合规审核
    
    Args:
        content: 待审核内容
        industry: 行业类型（如 "医疗"、"食品"）
        
    Returns:
        Dict[str, Any]: 审核结果
    """
    logger.info(f"合规审核: content={content[:50]}..., industry={industry}")
    
    # 参数验证
    if not content:
        raise ValidationError(message="审核内容不能为空", details={"content": content})
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_compliance_check", {
        "content": content,
        "industry": industry
    })
    
    return result

# ── 1.2 本地数据库工具 ─────────────────────────────────────────────────────────

@cached(ttl=600, maxsize=100)
@monitor_performance_async(logger=logger)
async def query_local_screens(
    city: str = None,
    district: str = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    查询本地屏幕
    
    Args:
        city: 城市名称
        district: 区县名称
        limit: 返回数量限制
        
    Returns:
        Dict[str, Any]: 本地屏幕列表
    """
    logger.info(f"查询本地屏幕: city={city}, district={district}, limit={limit}")
    
    # 参数验证
    if limit <= 0 or limit > 1000:
        raise ValidationError(message="limit 必须在 1-1000 之间", details={"limit": limit})
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_query_local_screens", {
        "city": city,
        "district": district,
        "limit": limit
    })
    
    return result

@cached(ttl=600, maxsize=50)
@monitor_performance_async(logger=logger)
async def query_local_stats(city: str = None) -> Dict[str, Any]:
    """
    查询本地统计
    
    Args:
        city: 城市名称
        
    Returns:
        Dict[str, Any]: 统计数据
    """
    logger.info(f"查询本地统计: city={city}")
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_query_local_stats", {
        "city": city
    })
    
    return result

@cached(ttl=600, maxsize=50)
@monitor_performance_async(logger=logger)
async def search_local_community(keyword: str) -> Dict[str, Any]:
    """
    搜索楼盘
    
    Args:
        keyword: 搜索关键词（如 "华港花园"）
        
    Returns:
        Dict[str, Any]: 匹配的楼盘列表
    """
    logger.info(f"搜索楼盘: keyword={keyword}")
    
    # 参数验证
    if not keyword:
        raise ValidationError(message="搜索关键词不能为空", details={"keyword": keyword})
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_search_local_community", {
        "keyword": keyword
    })
    
    return result

@monitor_performance_async(logger=logger)
async def audience_insight(
    product_desc: str,
    target_city: str = None,
    budget_hint: float = None
) -> Dict[str, Any]:
    """
    AI 人群洞察
    
    Args:
        product_desc: 产品描述
        target_city: 目标城市
        budget_hint: 预算提示（元）
        
    Returns:
        Dict[str, Any]: 人群洞察结果
    """
    logger.info(f"AI 人群洞察: product_desc={product_desc}, target_city={target_city}")
    
    # 参数验证
    if not product_desc:
        raise ValidationError(message="产品描述不能为空", details={"product_desc": product_desc})
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_audience_insight", {
        "product_desc": product_desc,
        "target_city": target_city,
        "budget_hint": budget_hint
    })
    
    return result

# ── 1.3 点位查询工具 ───────────────────────────────────────────────────────────

@cached(ttl=300, maxsize=100)
@monitor_performance_async(logger=logger)
async def query_access_points(
    city: str = None,
    district: str = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    查询门禁点位
    
    Args:
        city: 城市名称
        district: 区县名称
        limit: 返回数量限制
        
    Returns:
        Dict[str, Any]: 门禁点位列表
    """
    logger.info(f"查询门禁点位: city={city}, district={district}, limit={limit}")
    
    # 参数验证
    if limit <= 0 or limit > 1000:
        raise ValidationError(message="limit 必须在 1-1000 之间", details={"limit": limit})
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_query_access_points", {
        "city": city,
        "district": district,
        "limit": limit
    })
    
    return result

@cached(ttl=300, maxsize=100)
@monitor_performance_async(logger=logger)
async def query_smart_frames(
    city: str = None,
    district: str = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    查询单元门点位
    
    Args:
        city: 城市名称
        district: 区县名称
        limit: 返回数量限制
        
    Returns:
        Dict[str, Any]: 单元门点位列表
    """
    logger.info(f"查询单元门点位: city={city}, district={district}, limit={limit}")
    
    # 参数验证
    if limit <= 0 or limit > 1000:
        raise ValidationError(message="limit 必须在 1-1000 之间", details={"limit": limit})
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_query_smart_frames", {
        "city": city,
        "district": district,
        "limit": limit
    })
    
    return result

@cached(ttl=300, maxsize=100)
@monitor_performance_async(logger=logger)
async def query_daocha_points(city: str = None, limit: int = 50) -> Dict[str, Any]:
    """
    查询道闸点位
    
    Args:
        city: 城市名称
        limit: 返回数量限制
        
    Returns:
        Dict[str, Any]: 道闸点位列表
    """
    logger.info(f"查询道闸点位: city={city}, limit={limit}")
    
    # 参数验证
    if limit <= 0 or limit > 1000:
        raise ValidationError(message="limit 必须在 1-1000 之间", details={"limit": limit})
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_query_daocha_points", {
        "city": city,
        "limit": limit
    })
    
    return result

@cached(ttl=300, maxsize=100)
@monitor_performance_async(logger=logger)
async def query_led_points(city: str = None, limit: int = 50) -> Dict[str, Any]:
    """
    查询 LED 点位
    
    Args:
        city: 城市名称
        limit: 返回数量限制
        
    Returns:
        Dict[str, Any]: LED 点位列表
    """
    logger.info(f"查询 LED 点位: city={city}, limit={limit}")
    
    # 参数验证
    if limit <= 0 or limit > 1000:
        raise ValidationError(message="limit 必须在 1-1000 之间", details={"limit": limit})
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_query_led_points", {
        "city": city,
        "limit": limit
    })
    
    return result

@cached(ttl=300, maxsize=100)
@monitor_performance_async(logger=logger)
async def query_elevator_frames(city: str = None, limit: int = 50) -> Dict[str, Any]:
    """
    查询电梯框架
    
    Args:
        city: 城市名称
        limit: 返回数量限制
        
    Returns:
        Dict[str, Any]: 电梯框架列表
    """
    logger.info(f"查询电梯框架: city={city}, limit={limit}")
    
    # 参数验证
    if limit <= 0 or limit > 1000:
        raise ValidationError(message="limit 必须在 1-1000 之间", details={"limit": limit})
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_query_elevator_frames", {
        "city": city,
        "limit": limit
    })
    
    return result

@cached(ttl=300, maxsize=100)
@monitor_performance_async(logger=logger)
async def query_smart_screen_2025(city: str = None, limit: int = 50) -> Dict[str, Any]:
    """
    查询智能屏 2025 数据
    
    Args:
        city: 城市名称
        limit: 返回数量限制
        
    Returns:
        Dict[str, Any]: 智能屏 2025 数据列表
    """
    logger.info(f"查询智能屏 2025 数据: city={city}, limit={limit}")
    
    # 参数验证
    if limit <= 0 or limit > 1000:
        raise ValidationError(message="limit 必须在 1-1000 之间", details={"limit": limit})
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_query_smart_screen_2025", {
        "city": city,
        "limit": limit
    })
    
    return result

@cached(ttl=300, maxsize=100)
@monitor_performance_async(logger=logger)
async def query_shadow_points(city: str = None, limit: int = 50) -> Dict[str, Any]:
    """
    查询投影屏点位
    
    Args:
        city: 城市名称
        limit: 返回数量限制
        
    Returns:
        Dict[str, Any]: 投影屏点位列表
    """
    logger.info(f"查询投影屏点位: city={city}, limit={limit}")
    
    # 参数验证
    if limit <= 0 or limit > 1000:
        raise ValidationError(message="limit 必须在 1-1000 之间", details={"limit": limit})
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_query_shadow_points", {
        "city": city,
        "limit": limit
    })
    
    return result

# ── 1.4 资源统计工具 ───────────────────────────────────────────────────────────

@cached(ttl=600, maxsize=50)
@monitor_performance_async(logger=logger)
async def query_city_resources(city: str) -> Dict[str, Any]:
    """
    查询城市资源统计
    
    Args:
        city: 城市名称
        
    Returns:
        Dict[str, Any]: 城市资源统计数据
    """
    logger.info(f"查询城市资源统计: city={city}")
    
    # 参数验证
    if not city:
        raise ValidationError(message="城市名称不能为空", details={"city": city})
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_query_city_resources", {
        "city": city
    })
    
    return result

@cached(ttl=600, maxsize=10)
@monitor_performance_async(logger=logger)
async def query_city_summary() -> Dict[str, Any]:
    """
    查询全国城市汇总
    
    Returns:
        Dict[str, Any]: 全国城市汇总数据
    """
    logger.info("查询全国城市汇总")
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_query_city_summary", {})
    
    return result

@cached(ttl=300, maxsize=50)
@monitor_performance_async(logger=logger)
async def query_customers(
    brand: str = None,
    contact: str = None,
    industry: str = None,
    city: str = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    查询客户资料
    
    Args:
        brand: 品牌名称
        contact: 联系人
        industry: 行业类型
        city: 城市名称
        limit: 返回数量限制
        
    Returns:
        Dict[str, Any]: 客户资料列表
    """
    logger.info(f"查询客户资料: brand={brand}, industry={industry}, city={city}, limit={limit}")
    
    # 参数验证
    if limit <= 0 or limit > 1000:
        raise ValidationError(message="limit 必须在 1-1000 之间", details={"limit": limit})
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_query_customers", {
        "brand": brand,
        "contact": contact,
        "industry": industry,
        "city": city,
        "limit": limit
    })
    
    return result

# ── 1.5 ROI 计算工具 ────────────────────────────────────────────────────────────

@cached(ttl=300, maxsize=50)
@monitor_performance_async(logger=logger)
async def calc_roi(
    frames: int,
    weeks: int,
    category: str = "通用",
    media_type: str = "unit_door",
    price_type: str = "exchange"
) -> Dict[str, Any]:
    """
    计算社区营销 ROI
    
    Args:
        frames: 投放框数
        weeks: 投放周期（周）
        category: 品类（如 "日化用品"、"食品饮料"）
        media_type: 媒体类型（unit_door/access_door）
        price_type: 价格类型（exchange/cash）
        
    Returns:
        Dict[str, Any]: ROI 计算结果（三场景）
        
    Raises:
        ValidationError: 参数验证失败
    """
    logger.info(f"计算社区营销 ROI: frames={frames}, weeks={weeks}, category={category}")
    
    # 参数验证
    if frames <= 0:
        raise ValidationError(message="投放框数必须大于 0", details={"frames": frames})
    if weeks <= 0 or weeks > 52:
        raise ValidationError(message="投放周期必须在 1-52 周之间", details={"weeks": weeks})
    if category not in ["日化用品", "食品饮料", "母婴用品", "美妆护肤", "家电数码", "汽车用品", "医药保健", "餐饮连锁", "通用"]:
        raise ValidationError(message="未知的品类", details={"category": category})
    if media_type not in ["unit_door", "access_door"]:
        raise ValidationError(message="未知的媒体类型", details={"media_type": media_type})
    if price_type not in ["exchange", "cash"]:
        raise ValidationError(message="未知的价格类型", details={"price_type": price_type})
    
    # 调用 MCP 服务
    result = await call_mcp_service("pdooh_calc_roi", {
        "frames": frames,
        "weeks": weeks,
        "category": category,
        "media_type": media_type,
        "price_type": price_type
    })
    
    return result
    

# ── 1.6 本地数据库新工具（直接查询 qinlin_local.db）────────────────────────

@cached(ttl=300, maxsize=100)
@monitor_performance_async(logger=logger)
async def query_pdooh_points(
    table_name: str,
    filters: Optional[Dict[str, Any]] = None,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """
    查询 pDOOH 点位数据（直接查询本地数据库）
    
    Args:
        table_name: 表名（如 "单元门点位"、"门禁点位"、"道闸点位" 等）
        filters: 筛选条件字典，支持：
            - province: 省份（模糊匹配）
            - city: 城市（模糊匹配）
            - district: 区域/行政区（模糊匹配）
            - business_district: 商圈（模糊匹配）
            - min_price: 最低价格
            - max_price: 最高价格
        page: 页码（从 1 开始，默认 1）
        page_size: 每页记录数（默认 20，最大 1000）
        
    Returns:
        Dict[str, Any]: 包含数据和分页信息
    """
    logger.info(f"查询 pDOOH 点位: table={table_name}, filters={filters}, page={page}")
    
    try:
        # 参数验证
        if not table_name:
            raise ValidationError(message="表名不能为空", details={"table_name": table_name})
        
        if page < 1:
            raise ValidationError(message="page 必须大于等于 1", details={"page": page})
        
        if page_size < 1 or page_size > 1000:
            raise ValidationError(message="page_size 必须在 1-1000 之间", details={"page_size": page_size})
        
        # 调用数据库访问层
        from app.db_dao import query_table
        result = query_table(
            table_name=table_name,
            filters=filters or {},
            page=page,
            page_size=page_size
        )
        
        logger.info(f"查询成功: 返回 {len(result['data'])} 条记录，总计 {result['total']} 条")
        
        return {
            "success": True,
            "data": result["data"],
            "pagination": {
                "total": result["total"],
                "page": result["page"],
                "page_size": result["page_size"],
                "total_pages": result["total_pages"]
            }
        }
        
    except ValueError as e:
        logger.warning(f"参数验证失败: {str(e)}")
        raise ValidationError(message=str(e), details={"table_name": table_name})
    except FileNotFoundError as e:
        logger.error(f"数据库文件不存在: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"查询失败: {str(e)}", exc_info=True)
        raise


@cached(ttl=600, maxsize=50)
@monitor_performance_async(logger=logger)
async def get_point_stats(
    table_name: str,
    group_by: str = "city"
) -> Dict[str, Any]:
    """
    获取点位统计数据（直接查询本地数据库）
    
    Args:
        table_name: 表名（如 "单元门点位"、"门禁点位" 等）
        group_by: 分组字段（默认 "city"，可选值："city"、"province"、"business_district"）
        
    Returns:
        Dict[str, Any]: 统计信息
    """
    logger.info(f"获取点位统计: table={table_name}, group_by={group_by}")
    
    try:
        # 参数验证
        if not table_name:
            raise ValidationError(message="表名不能为空", details={"table_name": table_name})
        
        if group_by not in ["city", "province", "business_district"]:
            raise ValidationError(
                message="group_by 必须是 city/province/business_district 之一",
                details={"group_by": group_by}
            )
        
        # 调用数据库访问层
        from app.db_dao import get_table_stats
        stats = get_table_stats(table_name)
        
        # 根据 group_by 返回对应的统计
        result_data = {
            "total_count": stats["total_count"],
            "has_coordinates": stats.get("has_coordinates", 0),
            "null_coordinates": stats.get("null_coordinates", 0)
        }
        
        if group_by == "city" and "city_stats" in stats:
            result_data["group_stats"] = stats["city_stats"]
            result_data["group_by"] = "city"
        elif group_by == "province" and "province_stats" in stats:
            result_data["group_stats"] = stats["province_stats"]
            result_data["group_by"] = "province"
        elif group_by == "business_district" and "商圈" in stats:
            result_data["group_stats"] = stats.get("business_district_stats", {})
            result_data["group_by"] = "business_district"
        
        logger.info(f"统计信息获取成功: {table_name}")
        
        return {
            "success": True,
            "data": result_data
        }
        
    except ValueError as e:
        logger.warning(f"参数验证失败: {str(e)}")
        raise ValidationError(message=str(e), details={"table_name": table_name})
    except FileNotFoundError as e:
        logger.error(f"数据库文件不存在: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}", exc_info=True)
        raise


@cached(ttl=300, maxsize=100)
@monitor_performance_async(logger=logger)
async def search_clients_mcp(
    keyword: str,
    city: Optional[str] = None,
    industry: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    搜索客户信息（从"客户通讯录"表）
    
    Args:
        keyword: 搜索关键词（匹配客户简称或品牌名称）
        city: 决策城市筛选（可选）
        industry: 行业筛选（可选）
        limit: 返回数量限制（默认 20，最大 500）
        
    Returns:
        Dict[str, Any]: 匹配的客户列表
    """
    logger.info(f"搜索客户: keyword={keyword}, city={city}, industry={industry}, limit={limit}")
    
    try:
        # 参数验证
        if not keyword:
            raise ValidationError(message="搜索关键词不能为空", details={"keyword": keyword})
        
        if limit < 1 or limit > 500:
            raise ValidationError(message="limit 必须在 1-500 之间", details={"limit": limit})
        
        # 调用数据库访问层
        from app.db_dao import search_clients as dao_search_clients
        results = dao_search_clients(
            keyword=keyword,
            city=city,
            industry=industry,
            limit=limit
        )
        
        logger.info(f"搜索完成: 找到 {len(results)} 条匹配记录")
        
        return {
            "success": True,
            "data": results,
            "total": len(results)
        }
        
    except ValueError as e:
        logger.warning(f"参数验证失败: {str(e)}")
        raise ValidationError(message=str(e), details={"keyword": keyword})
    except FileNotFoundError as e:
        logger.error(f"数据库文件不存在: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"搜索失败: {str(e)}", exc_info=True)
        raise


# ── 健康检查 ────────────────────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    """健康检查"""
    logger.info("收到健康检查请求")
    return {
        "service": "pDOOH A2A MCP Server",
        "status": "ok",
        "tools_count": 25,  # 22 + 3 新增工具
        "mcp_endpoint": "/api/v2/mcp/pdooh/tools/call",
        "skill_endpoint": "/api/v2/mcp/pdooh/skill.yaml",
        "reference": "XX科技5V数据模型",
        "new_tools": [
            "pdooh_query_pdooh_points",
            "pdooh_get_point_stats",
            "pdooh_search_clients"
        ]
    }

# ── Skill YAML 端点 ────────────────────────────────────────────────────────────

@router.get("/skill.yaml")
async def get_skill_yaml():
    """获取 Skill YAML 定义"""
    logger.info("收到 Skill YAML 请求")
    
    skill_yaml = """
name: pDOOH MCP Server
description: pDOOH 户外广告 AI 原生投放系统 MCP 服务器，提供 25 个工具（含 3 个新增数据库查询工具）
version: 2.1.0
tools:
  - name: pdooh_query_screens
    description: 查询智能屏
    parameters:
      - name: city
        type: string
        required: false
        description: 城市名称
      - name: district
        type: string
        required: false
        description: 区县名称
      - name: min_house_price
        type: number
        required: false
        description: 最低房价（万元/㎡）
      - name: tags
        type: array
        required: false
        description: 标签列表
      - name: limit
        type: integer
        required: false
        description: 返回数量限制（默认 20）
  - name: pdooh_get_screen_audience
    description: 获取屏人群画像
    parameters:
      - name: screen_id
        type: integer
        required: true
        description: 屏幕 ID
  - name: pdooh_create_campaign
    description: 创建投放计划
    parameters:
      - name: name
        type: string
        required: true
        description: 投放计划名称
      - name: screen_ids
        type: array
        required: true
        description: 屏幕 ID 列表
      - name: start_date
        type: string
        required: true
        description: 开始日期（YYYY-MM-DD）
      - name: end_date
        type: string
        required: true
        description: 结束日期（YYYY-MM-DD）
      - name: budget
        type: number
        required: true
        description: 预算（元）
      - name: creative_text
        type: string
        required: true
        description: 创意文案
  - name: pdooh_query_campaigns
    description: 查询投放计划
    parameters:
      - name: status
        type: string
        required: false
        description: 投放状态（running/paused/completed）
  - name: pdooh_submit_creative
    description: 提交创意
    parameters:
      - name: campaign_id
        type: integer
        required: true
        description: 投放计划 ID
      - name: content
        type: string
        required: true
        description: 创意内容
      - name: ai_generated
        type: boolean
        required: false
        description: 是否由 AI 生成（默认 false）
  - name: pdooh_query_report
    description: 查询投放报告
    parameters:
      - name: campaign_id
        type: integer
        required: true
        description: 投放计划 ID
  - name: pdooh_compliance_check
    description: 合规审核
    parameters:
      - name: content
        type: string
        required: true
        description: 待审核内容
      - name: industry
        type: string
        required: false
        description: 行业类型
  - name: pdooh_query_local_screens
    description: 查询本地屏幕
    parameters:
      - name: city
        type: string
        required: false
        description: 城市名称
      - name: district
        type: string
        required: false
        description: 区县名称
      - name: limit
        type: integer
        required: false
        description: 返回数量限制（默认 20）
  - name: pdooh_query_local_stats
    description: 查询本地统计
    parameters:
      - name: city
        type: string
        required: false
        description: 城市名称
  - name: pdooh_search_local_community
    description: 搜索楼盘
    parameters:
      - name: keyword
        type: string
        required: true
        description: 搜索关键词
  - name: pdooh_audience_insight
    description: AI 人群洞察
    parameters:
      - name: product_desc
        type: string
        required: true
        description: 产品描述
      - name: target_city
        type: string
        required: false
        description: 目标城市
      - name: budget_hint
        type: number
        required: false
        description: 预算提示（元）
  - name: pdooh_query_access_points
    description: 查询门禁点位
    parameters:
      - name: city
        type: string
        required: false
        description: 城市名称
      - name: district
        type: string
        required: false
        description: 区县名称
      - name: limit
        type: integer
        required: false
        description: 返回数量限制（默认 50）
  - name: pdooh_query_smart_frames
    description: 查询单元门点位
    parameters:
      - name: city
        type: string
        required: false
        description: 城市名称
      - name: district
        type: string
        required: false
        description: 区县名称
      - name: limit
        type: integer
        required: false
        description: 返回数量限制（默认 50）
  - name: pdooh_query_daocha_points
    description: 查询道闸点位
    parameters:
      - name: city
        type: string
        required: false
        description: 城市名称
      - name: limit
        type: integer
        required: false
        description: 返回数量限制（默认 50）
  - name: pdooh_query_led_points
    description: 查询 LED 点位
    parameters:
      - name: city
        type: string
        required: false
        description: 城市名称
      - name: limit
        type: integer
        required: false
        description: 返回数量限制（默认 50）
  - name: pdooh_query_elevator_frames
    description: 查询电梯框架
    parameters:
      - name: city
        type: string
        required: false
        description: 城市名称
      - name: limit
        type: integer
        required: false
        description: 返回数量限制（默认 50）
  - name: pdooh_query_smart_screen_2025
    description: 查询智能屏 2025 数据
    parameters:
      - name: city
        type: string
        required: false
        description: 城市名称
      - name: limit
        type: integer
        required: false
        description: 返回数量限制（默认 50）
  - name: pdooh_query_shadow_points
    description: 查询投影屏点位
    parameters:
      - name: city
        type: string
        required: false
        description: 城市名称
      - name: limit
        type: integer
        required: false
        description: 返回数量限制（默认 50）
  - name: pdooh_query_city_resources
    description: 查询城市资源统计
    parameters:
      - name: city
        type: string
        required: true
        description: 城市名称
  - name: pdooh_query_city_summary
    description: 查询全国城市汇总
    parameters: []
  - name: pdooh_query_customers
    description: 查询客户资料
    parameters:
      - name: brand
        type: string
        required: false
        description: 品牌名称
      - name: contact
        type: string
        required: false
        description: 联系人
      - name: industry
        type: string
        required: false
        description: 行业类型
      - name: city
        type: string
        required: false
        description: 城市名称
      - name: limit
        type: integer
        required: false
        description: 返回数量限制（默认 20）
  - name: pdooh_calc_roi
    description: 计算社区营销 ROI
    parameters:
      - name: frames
        type: integer
        required: true
        description: 投放框数
      - name: weeks
        type: integer
        required: true
        description: 投放周期（周）
      - name: category
        type: string
        required: false
        description: 品类（默认 通用）
      - name: media_type
        type: string
        required: false
        description: 媒体类型（默认 unit_door）
      - name: price_type
        type: string
        required: false
        description: 价格类型（默认 exchange）
  - name: pdooh_query_pdooh_points
    description: 查询 pDOOH 点位数据（直接查询本地数据库 qinlin_local.db）
    parameters:
      - name: table_name
        type: string
        required: true
        description: 表名（如 "单元门点位"、"门禁点位"、"道闸点位" 等）
      - name: filters
        type: object
        required: false
        description: 筛选条件（province/city/district/business_district/min_price/max_price）
      - name: page
        type: integer
        required: false
        description: 页码（默认 1）
      - name: page_size
        type: integer
        required: false
        description: 每页记录数（默认 20，最大 1000）
  - name: pdooh_get_point_stats
    description: 获取点位统计数据（按城市/省份/商圈分组）
    parameters:
      - name: table_name
        type: string
        required: true
        description: 表名（如 "单元门点位"、"门禁点位" 等）
      - name: group_by
        type: string
        required: false
        description: 分组字段（city/province/business_district，默认 city）
  - name: pdooh_search_clients
    description: 搜索客户信息（从"客户通讯录"表）
    parameters:
      - name: keyword
        type: string
        required: true
        description: 搜索关键词（匹配客户简称或品牌名称）
      - name: city
        type: string
        required: false
        description: 决策城市筛选
      - name: industry
        type: string
        required: false
        description: 行业筛选
      - name: limit
        type: integer
        required: false
        description: 返回数量限制（默认 20，最大 500）
"""
    
    return JSONResponse(content=skill_yaml, media_type="application/x-yaml")
