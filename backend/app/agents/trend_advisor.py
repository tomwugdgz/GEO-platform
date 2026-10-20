"""
MTO 趋势与优化顾问 Agent
=================================================================================
作为「智能体能力」接入平台：既可直接被 API 调用，也可作为 LangGraph 编排节点，
消费累积的 MTO/GEO 指标快照，判别未来趋势并推荐优化方向。

底层调用 app.services.trend_advisor（统计趋势 + Laya 决策引擎 LAYA/JEV）。
"""
from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional

from app.services import trend_advisor as svc

logger = logging.getLogger(__name__)


class TrendAdvisorAgent:
    """
    MTO 趋势与优化顾问 Agent。

    analyze_trend(snapshots, backend="auto")：
      snapshots 为指标快照列表（dict 或 ORM 均可，需含 snapshot_at 时序）。
      backend 可选 local / remote / auto（默认 auto：有 CUDA 走本地 LAYA，否则远程 JEV）。
    """

    async def analyze_trend(
        self,
        snapshots: List[Dict[str, Any]],
        backend: str = "auto",
    ) -> Dict[str, Any]:
        if not snapshots or len(snapshots) < 2:
            return {
                "ok": False,
                "error": "累积数据不足（至少需要 2 期快照）",
                "suggestion": "先通过 /api/v2/trend/snapshot 累积多期 MTO/GEO 指标",
            }
        try:
            return svc.predict_trend(snapshots, backend=backend)
        except Exception as e:
            logger.error("趋势顾问 Agent 失败: %s", e, exc_info=True)
            return {"ok": False, "error": str(e)}


# 全局实例（与 orchestrator 中其它 agent 的暴露方式一致）
trend_advisor_agent = TrendAdvisorAgent()
