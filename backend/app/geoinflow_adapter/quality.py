"""
零假数据纪律 —— 借鉴 GEOInflow「No fake production analytics」
=================================================================================
上游依据：
  · AGENTS.md 第 11 条：「No fake production analytics. Empty, missing input,
    estimated and unsupported states are distinct. Demonstration data is
    explicitly named and isolated.」
  · README.md：「Empty data, missing integrations, unknown values, estimates,
    and unsupported capabilities are shown as distinct states.
    Demo websites are explicitly labeled.」

本模块提供一组轻量封装，让新模块的输出【强制携带证据状态】，
避免把缺失值折叠成 0 / None / 空数组。

注意：本模块【不改动】仓库既有的 services/mock_data.py 与 diagnosis_routes.py，
以保持原有功能与代码风格不变；仅约束新增的 geoinflow_adapter 及其 API 输出。
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.geoinflow_adapter.evidence import EvidenceState


def state_of(value: Any, *, unsupported: bool = False) -> str:
    """判定一个值的证据状态，用于把「没有数据」与「数据为 0」区分开。"""
    if unsupported:
        return EvidenceState.UNSUPPORTED.value
    if value is None:
        return EvidenceState.MISSING_INPUT.value
    return EvidenceState.OBSERVED.value


def guard_missing(value: Any, *, field: str, unsupported: bool = False) -> Dict[str, Any]:
    """把任意值包装成 {value, state, note}，缺失时 value 保持 None 而非 0。"""
    st = state_of(value, unsupported=unsupported)
    notes = {
        EvidenceState.MISSING_INPUT.value: f"缺少 {field} 输入，未以 0 代替",
        EvidenceState.UNSUPPORTED.value: f"当前部署不支持 {field}",
        EvidenceState.OBSERVED.value: f"{field} 为已观测值",
    }
    return {"value": value, "state": st, "note": notes[st]}


def mark_demo(payload: Dict[str, Any], *, label: str = "演示数据") -> Dict[str, Any]:
    """显式标注演示数据，防止合成数据被当作真实观测（上游要求 demo 明确命名并隔离）。"""
    out = dict(payload)
    out["is_demo"] = True
    out["demo_label"] = label
    out["limitations"] = list(out.get("limitations", [])) + [
        f"本结果标记为「{label}」，为合成/示例数据，不得用于任何真实结论或商业决策"
    ]
    return out


def never_fake_banner() -> Dict[str, Any]:
    """返回该模块遵循的数据纪律声明（供 /api/v2/mto/evidence/policy 输出）。"""
    return {
        "rule": "no_fake_production_analytics",
        "states_are_distinct": [
            EvidenceState.MISSING_INPUT.value,
            EvidenceState.UNKNOWN.value,
            EvidenceState.ESTIMATED.value,
            EvidenceState.OBSERVED.value,
            EvidenceState.VERIFIED.value,
            EvidenceState.PROVED_ZERO.value,
            EvidenceState.UNSUPPORTED.value,
        ],
        "prohibitions": [
            "禁止用 0 代替缺失输入",
            "禁止用估算值冒充观测值",
            "禁止把 UA 声明当作身份核验",
            "演示数据必须显式标注并隔离",
        ],
        "scope": "仅约束 geoinflow_adapter 及其 API；既有模块保持原状",
    }
