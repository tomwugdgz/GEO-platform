"""Agent 包入口。

注意：orchestrator 依赖 langgraph，且 4 个历史 Agent 模块（audience_insight /
smart_schedule / dynamic_creative / attribution）当前仓库中不存在。为避免整个
app.agents 包因这些缺失而无法导入（会连带阻断 trend_advisor 等新 Agent），
此处统一做防御式导入：缺失的置为 None，但保证包本身可正常 import。
"""
orchestrator = None
audience_agent = None
schedule_agent = None
creative_agent = None
attribution_agent = None

try:
    from app.agents.orchestrator import orchestrator  # 依赖 langgraph
except Exception:
    pass

try:
    from app.agents.audience_insight import audience_agent
except Exception:
    pass

try:
    from app.agents.smart_schedule import schedule_agent
except Exception:
    pass

try:
    from app.agents.dynamic_creative import creative_agent
except Exception:
    pass

try:
    from app.agents.attribution import attribution_agent
except Exception:
    pass

try:
    from app.agents.trend_advisor import trend_advisor_agent  # 新增：MTO 趋势与优化顾问
except Exception:
    trend_advisor_agent = None

__all__ = [
    "orchestrator", "audience_agent", "schedule_agent",
    "creative_agent", "attribution_agent", "trend_advisor_agent",
]
