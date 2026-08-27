"""
Agent API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Optional
from uuid import UUID

from app.agents.orchestrator import orchestrator
from app.agents.audience_insight import audience_agent
from app.agents.smart_schedule import schedule_agent
from app.agents.dynamic_creative import creative_agent
from app.agents.attribution import attribution_agent
from app.services.rag_kb import rag_kb

router = APIRouter()


@router.post("/agents/execute")
async def execute_agent_workflow(query: dict = Body(...)):
    """执行CPS 2.0完整工作流"""
    result = await orchestrator.execute(query)
    return result


@router.get("/agents/audience-insight")
async def get_audience_insight(
    city: str = Query("广州", description="目标城市"),
    industry: str = Query("retail", description="行业类型")
):
    """人群洞察分析"""
    result = await audience_agent.analyze(city=city, industry=industry)
    return result


@router.post("/agents/schedule")
async def generate_schedule(query: dict = Body(...)):
    """智能排期"""
    result = await schedule_agent.generate_schedule(
        audience_report=query.get("audience_report"),
        budget=query.get("budget", 50000),
        target_audience=query.get("target_audience", {}),
    )
    return result


@router.post("/agents/creative")
async def generate_creatives(query: dict = Body(...)):
    """动态创意生成"""
    result = await creative_agent.generate_creatives(
        audience_report=query.get("audience_report"),
        schedule_plan=query.get("schedule_plan"),
        industry=query.get("industry", "retail"),
        product_info=query.get("product_info", ""),
    )
    return result


@router.get("/agents/attribution")
async def get_attribution(
    campaign_id: Optional[str] = Query(None, description="投放计划ID")
):
    """效果归因分析（增强版）"""
    result = await attribution_agent.analyze_attribution(
        db=None,
        campaign_id=campaign_id,
    )
    return result


@router.get("/rag/knowledge")
async def search_knowledge(
    query: str = Query(..., description="搜索关键词"),
    n_results: int = Query(5, ge=1, le=20, description="返回结果数量")
):
    """RAG知识库检索"""
    result = await rag_kb.query(query, n_results=n_results)
    return result


@router.post("/rag/add")
async def add_knowledge(
    collection_name: str = Body(...),
    doc_id: str = Body(...),
    content: str = Body(...),
    metadata: dict = Body({})
):
    """添加知识库文档"""
    try:
        rag_kb.add_document(collection_name, doc_id, content, metadata)
        return {"message": "文档添加成功", "doc_id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
