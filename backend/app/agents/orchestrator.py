"""
统一编排Agent（规划→执行→反思循环）
基于 LangGraph 实现有状态工作流，串联四大 Agent + 优化模块

状态图：
    plan → audience_insight → smart_schedule → dynamic_creative → attribution → reflect → [loop]
    
反思后条件分支：
    - iteration < 2 → reflect → smart_schedule（重优化排期）
    - iteration >= 2 → END
"""
import json
import logging
from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, END

from app.agents.audience_insight import audience_agent
from app.agents.smart_schedule import schedule_agent
from app.agents.dynamic_creative import creative_agent
from app.agents.attribution import attribution_agent
from app.services.scheduling_optimizer import SchedulingOptimizer
from app.services.competitor_monitor import CompetitorMonitorService as CompetitorMonitor
from app.services.llm_client import llm_client

logger = logging.getLogger(__name__)


# ─── 状态定义 ──────────────────────────────────────────────────

class CampaignState(TypedDict):
    """工作流全局状态"""
    # 输入
    query: dict                          # 用户原始输入
    # Agent 输出
    audience_report: dict                # 人群洞察
    schedule_plan: dict                  # 排期方案
    creative_plan: dict                  # 创意方案
    attribution_report: dict             # 归因报告
    optimization_report: dict            # 排期优化结果
    competitor_report: dict              # 竞品监控
    # 工作流控制
    iteration: int                       # 反思迭代次数
    feedback: str                        # 反思反馈
    plan: str                            # 初始规划
    errors: List[str]                    # 错误日志
    status: str                          # running / completed / failed


# ─── 编排器 ─────────────────────────────────────────────────────

class OrchestratorAgent:
    """
    统一编排 Agent — 规划→执行→反思循环

    工作流：
        plan → 人群洞察 → 智能排期 → 动态创意 → 效果归因 → 反思
            ↑                                                     │
            └──────────── iteration < 2 时回环 ──────────────────┘

    新增节点：
        - optimize_schedule: AI 排期优化（基于历史 ROI）
        - monitor_competitor: 竞品监控报告
    """

    def __init__(self, max_iterations: int = 2):
        self.max_iterations = max_iterations
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建 LangGraph 有状态工作流"""
        workflow = StateGraph(CampaignState)

        # ── 添加节点 ──
        workflow.add_node("plan", self._plan)
        workflow.add_node("audience_insight", self._run_audience)
        workflow.add_node("smart_schedule", self._run_schedule)
        workflow.add_node("optimize_schedule", self._run_optimization)
        workflow.add_node("dynamic_creative", self._run_creative)
        workflow.add_node("monitor_competitor", self._run_competitor)
        workflow.add_node("attribution", self._run_attribution)
        workflow.add_node("reflect", self._reflect)

        # ── 添加边 ──
        workflow.set_entry_point("plan")
        workflow.add_edge("plan", "audience_insight")
        workflow.add_edge("audience_insight", "smart_schedule")
        workflow.add_edge("smart_schedule", "optimize_schedule")
        workflow.add_edge("optimize_schedule", "dynamic_creative")
        workflow.add_edge("dynamic_creative", "monitor_competitor")
        workflow.add_edge("monitor_competitor", "attribution")

        # 归因后条件分支：反思 or 结束
        workflow.add_conditional_edges(
            "attribution",
            self._should_iterate,
            {"reflect": "reflect", "end": END},
        )
        workflow.add_edge("reflect", "smart_schedule")  # 回环

        return workflow.compile()

    # ── 节点实现 ──────────────────────────────────────────────

    async def execute(self, query: dict) -> dict:
        """
        执行完整工作流

        Args:
            query: 用户输入，包含 city, industry, budget, objective 等

        Returns:
            格式化后的全链路结果
        """
        initial_state = CampaignState(
            query=query,
            audience_report={},
            schedule_plan={},
            creative_plan={},
            attribution_report={},
            optimization_report={},
            competitor_report={},
            iteration=0,
            feedback="",
            plan="",
            errors=[],
            status="running",
        )

        try:
            logger.info("🚀 编排工作流启动 — %s", query.get("objective", "unknown"))
            result = await self.graph.ainvoke(initial_state)
            result["status"] = "completed"
            return self._format_result(result)
        except Exception as e:
            logger.error("工作流执行失败: %s", e, exc_info=True)
            initial_state["status"] = "failed"
            initial_state["errors"].append(str(e))
            return {
                "error": str(e),
                "message": "工作流执行失败，请检查配置",
                "status": "failed",
                "state": initial_state,
            }

    # ── 各节点 ───────────────────────────────────────────────

    async def _plan(self, state: CampaignState) -> CampaignState:
        """规划阶段 — 解读用户需求"""
        query = state["query"]
        state["plan"] = (
            f"投放方案规划:\n"
            f"- 城市: {query.get('city', '广州')}\n"
            f"- 行业: {query.get('industry', 'retail')}\n"
            f"- 预算: ¥{query.get('budget', 50000):,.0f}\n"
            f"- 目标: {query.get('objective', '提升品牌认知度')}\n"
            f"- 投放周期: {query.get('days', 14)} 天\n"
        )
        return state

    async def _run_audience(self, state: CampaignState) -> CampaignState:
        """人群洞察 Agent"""
        query = state["query"]
        try:
            report = await audience_agent.analyze(
                city=query.get("city", "广州"),
                industry=query.get("industry", "retail"),
            )
            state["audience_report"] = report
        except Exception as e:
            state["errors"].append(f"人群洞察失败: {e}")
            state["audience_report"] = {"clusters": [], "insights": ["洞察数据暂不可用"]}
        return state

    async def _run_schedule(self, state: CampaignState) -> CampaignState:
        """智能排期 Agent"""
        query = state["query"]
        try:
            plan = await schedule_agent.generate_schedule(
                audience_report=state["audience_report"],
                budget=query.get("budget", 50000),
                target_audience=query.get("target_audience", {}),
            )
            state["schedule_plan"] = plan
        except Exception as e:
            state["errors"].append(f"智能排期失败: {e}")
            state["schedule_plan"] = {"schedule": [], "budget_allocation": {}}
        return state

    async def _run_optimization(self, state: CampaignState) -> CampaignState:
        """
        AI 排期优化 — 基于 SchedulingOptimizer 贪心算法优化
        
        对 schedule_plan 中的排期进行二次优化：
        - 按性价比排序重排
        - 周末/工作日差异化加权
        - 预算分配优化
        """
        query = state["query"]
        try:
            optimizer = SchedulingOptimizer()
            # 从排期方案提取信息，生成优化版
            opt_result = optimizer.generate_schedule(
                db=None,  # 模拟模式
                budget=query.get("budget", 50000),
                days=query.get("days", 14),
            )
            state["optimization_report"] = {
                "optimized_slots": opt_result.get("slots", []),
                "total_cost": opt_result.get("total_cost", 0),
                "total_impressions": opt_result.get("total_impressions", 0),
                "avg_cpm": opt_result.get("avg_cpm", 0),
                "remaining_budget": opt_result.get("remaining_budget", 0),
                "optimization_note": "基于贪心算法 + 周末加权优化",
            }
        except Exception as e:
            state["errors"].append(f"排期优化失败: {e}")
            state["optimization_report"] = {"optimization_note": f"优化失败: {e}"}
        return state

    async def _run_creative(self, state: CampaignState) -> CampaignState:
        """动态创意 Agent"""
        query = state["query"]
        try:
            plan = await creative_agent.generate_creatives(
                audience_report=state["audience_report"],
                schedule_plan=state["schedule_plan"],
                industry=query.get("industry", "retail"),
                product_info=query.get("product_info", ""),
            )
            state["creative_plan"] = plan
        except Exception as e:
            state["errors"].append(f"动态创意失败: {e}")
            state["creative_plan"] = {"creatives": [], "dco_mapping": {}}
        return state

    async def _run_competitor(self, state: CampaignState) -> CampaignState:
        """
        竞品监控 Agent — 基于 CompetitorMonitor
        """
        query = state["query"]
        try:
            monitor = CompetitorMonitor()
            report = await monitor.generate_report(
                competitor_name=query.get("competitor_name", ""),
                media_type=query.get("media_type", ""),
            )
            state["competitor_report"] = report
        except Exception as e:
            state["errors"].append(f"竞品监控失败: {e}")
            state["competitor_report"] = {
                "competitor_name": query.get("competitor_name", ""),
                "market_distribution": {},
                "suggestions": ["竞品数据暂不可用"],
            }
        return state

    async def _run_attribution(self, state: CampaignState) -> CampaignState:
        """效果归因 Agent"""
        try:
            report = await attribution_agent.analyze_attribution(db=None, campaign_id=None)
            state["attribution_report"] = report
        except Exception as e:
            state["errors"].append(f"效果归因失败: {e}")
            state["attribution_report"] = {
                "attribution": {"total_conversions": 0},
                "cross_device_match_rate": 0,
            }
        return state

    async def _reflect(self, state: CampaignState) -> CampaignState:
        """
        反思阶段 — 基于归因报告提出优化建议

        使用 LLM 分析投放效果，输出：
        1. 需要调整的投放区域
        2. 预算重新分配建议
        3. 创意优化方向
        4. 排期调整建议
        """
        try:
            report = state.get("attribution_report", {})
            opt = state.get("optimization_report", {})

            feedback_prompt = f"""
            分析以下投放方案的效果数据，提出优化建议：
            
            - 总转化: {report.get('attribution', {}).get('total_conversions', 0)}
            - 跨端匹配率: {report.get('cross_device_match_rate', 0)}
            - 总预算: ¥{state['query'].get('budget', 0):,.0f}
            - 优化后花费: ¥{opt.get('total_cost', 0):,.0f}
            - CPM: ¥{opt.get('avg_cpm', 0):.2f}
            - 剩余预算: ¥{opt.get('remaining_budget', 0):,.0f}
            
            请给出：
            1. 需要调整的投放区域
            2. 预算重新分配建议
            3. 创意优化方向
            4. 排期调整建议
            """
            feedback = await llm_client.chat(
                feedback_prompt,
                system_prompt="你是专业的广告投放优化师，擅长 pDOOH 投放策略优化。"
            )

            state["feedback"] = feedback
            state["iteration"] += 1
        except Exception as e:
            state["errors"].append(f"反思阶段失败: {e}")
            state["feedback"] = f"反思失败: {e}"
            state["iteration"] += 1
        return state

    def _should_iterate(self, state: CampaignState) -> str:
        """条件分支：是否继续迭代"""
        if state.get("iteration", 0) >= self.max_iterations:
            return "end"
        return "reflect"

    def _format_result(self, state: CampaignState) -> dict:
        """格式化输出 — 提取关键指标"""
        schedule = state.get("schedule_plan", {})
        creative = state.get("creative_plan", {})
        attribution = state.get("attribution_report", {})
        opt = state.get("optimization_report", {})
        competitor = state.get("competitor_report", {})

        return {
            "workflow": "AIAdPlacer CPS 2.0 Agent Orchestration",
            "status": state.get("status", "completed"),
            "iterations": state.get("iteration", 0),
            "errors": state.get("errors", []),

            "plan": state.get("plan", ""),

            # 人群洞察
            "audience_insight": {
                "clusters": attribution.get("audience_report", {}).get("clusters",
                    state.get("audience_report", {}).get("clusters", [])),
                "insights": state.get("audience_report", {}).get("insights", []),
                "recommended_areas": state.get("audience_report", {}).get("recommended_areas", []),
                "cluster_count": len(state.get("audience_report", {}).get("clusters", [])),
            },

            # 智能排期
            "smart_schedule": {
                "schedule_count": len(schedule.get("schedule", [])),
                "budget_allocation": schedule.get("budget_allocation", {}),
                "expected_ctr": schedule.get("expected_ctr", 0),
                "expected_cvr": schedule.get("expected_cvr", 0),
                "gantt_data": schedule.get("gantt_data", []),
            },

            # 排期优化
            "optimization": {
                "optimized_slots": len(opt.get("optimized_slots", [])),
                "total_cost": opt.get("total_cost", 0),
                "total_impressions": opt.get("total_impressions", 0),
                "avg_cpm": opt.get("avg_cpm", 0),
                "remaining_budget": opt.get("remaining_budget", 0),
                "note": opt.get("optimization_note", ""),
            },

            # 动态创意
            "dynamic_creative": {
                "creative_count": len(creative.get("creatives", [])),
                "dco_mappings": len(creative.get("dco_mapping", {})),
            },

            # 竞品监控
            "competitor_monitor": {
                "name": competitor.get("competitor_name", ""),
                "market_distribution": competitor.get("market_distribution", {}),
                "suggestions_count": len(competitor.get("suggestions", [])),
            },

            # 效果归因
            "attribution": {
                "total_conversions": attribution.get("attribution", {}).get("total_conversions", 0),
                "cross_device_match_rate": attribution.get("cross_device_match_rate", 0),
                "suggestions_count": len(attribution.get("suggestions", [])),
                "geo_analysis": attribution.get("geo_analysis", {}),
            },

            # 反思反馈
            "feedback": state.get("feedback", ""),
        }


# ─── 全局实例 ────────────────────────────────────────────────────

orchestrator = OrchestratorAgent(max_iterations=2)
