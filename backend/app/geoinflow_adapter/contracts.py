"""
统一响应契约 —— 借鉴 GEOInflow「产品页消费 contracts」的工程组织
=================================================================================
上游依据：README.md「Product pages live in src/components/liekan,
data contracts in src/lib/liekan/contracts」；AGENTS.md 第 8 条
「Product pages consume Liekan contracts」。

本项目把同一思想落到最小范围：所有新增证据类 API 统一走一个响应信封，
保证 data / evidence_state / policy_version / limitations 四要素不缺位，
避免各端点各自发明字段口径。
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.geoinflow_adapter.policy import POLICY_ID

POLICY_VERSION = POLICY_ID


def build_response(
    data: Dict[str, Any],
    *,
    evidence_state: str,
    policy_version: str = POLICY_VERSION,
    limitations: Optional[List[str]] = None,
    is_demo: bool = False,
) -> Dict[str, Any]:
    """
    构造统一响应信封。

    参数：
        data            : 业务数据（不得包含被折叠成 0 的缺失值）
        evidence_state  : EvidenceState 枚举值之一，必填
        policy_version  : 冻结策略版本，默认当前策略
        limitations     : 该结果的适用限制
        is_demo         : 是否为演示/合成数据
    """
    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy_version": policy_version,
        "evidence_state": evidence_state,
        "is_demo": is_demo,
        "data": data,
        "limitations": list(limitations or []),
        "boundary": (
            "本结果仅描述已观测到的访问与证据充分性；"
            "不构成收录、引用、排名、获客或商业效果的证明。"
        ),
    }
