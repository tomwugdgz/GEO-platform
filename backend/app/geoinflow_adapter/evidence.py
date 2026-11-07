"""
证据状态机 —— 借鉴 GEOInflow「证据充分性显式化」口径
=================================================================================
上游依据：
  · README.md：「Declared User-Agent strings, matches against official IP ranges,
    and available DNS or trusted edge evidence are stored independently.
    A User-Agent claim alone is insufficient to confirm a source.」
  · README.md：「Crawl logs establish observed access. Indexing, model training,
    answer citations, recommendation rankings, and customer acquisition
    each require their own evidence.」
  · docs/traffic-quality.md：browser / automated / suspected / unknown 四类互不混淆；
    空数据、缺失输入、未知值、估算、不支持能力显示为不同状态。
  · docs/geo-weight.md：Missing input and unusable evidence return null weight；
    证据不完整时不得返回 0。

本模块把上述纪律固化为可复用的 Python 枚举与判定函数，供
geoinflow_routes.py / models/geoinflow_evidence.py 使用，避免把「没有数据」伪装成 0。
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional


class EvidenceState(str, Enum):
    """证据状态。各状态不可互相替代，禁止用 0 / None 隐式折叠。"""

    VERIFIED = "verified"              # 有独立核验证据（如官方范围 + 版本快照）
    OBSERVED = "observed"              # 已观测到访问，但未完成身份核验
    ESTIMATED = "estimated"            # 推断/估算结果，必须保留估算标签
    UNKNOWN = "unknown"                # 缺少识别证据，历史记录不追认
    MISSING_INPUT = "missing_input"     # 缺少必要输入（如未提供内容清单）
    UNSUPPORTED = "unsupported"         # 当前部署不支持该能力
    PROVED_ZERO = "proved_zero"         # 完整观测窗口下确证为 0（≠ 无数据）


# 上游原文的工程化常量：访问日志只建立「观测」，以下结论各自需要独立证据。
SEPARATE_EVIDENCE_REQUIRED = (
    "indexing",              # 收录
    "model_training",        # 模型训练
    "answer_citations",       # 答案引用
    "recommendation_ranking",  # 推荐排名
    "customer_acquisition",  # 获客转化
)

OBSERVATION_ONLY_NOTE = (
    "抓取/访问日志仅建立『观测到的访问』；收录、模型训练、答案引用、"
    "推荐排名与获客转化各自需要独立证据，不得以本观测结果代替。"
)


def classify_identity(
    declared_user_agent: Optional[str] = None,
    official_range_verified: bool = False,
    range_snapshot_version: Optional[str] = None,
    trusted_ingress: bool = False,
    dns_or_edge_evidence: bool = False,
) -> Dict[str, Any]:
    """
    判定一条请求的身份证据状态。

    核心规则（对齐上游）：
      ① 仅凭 UA 声明 → UNKNOWN，不能确认来源；
      ② UA + 官方范围核验 + 已归档范围快照版本 → VERIFIED；
      ③ 有可信入口或 DNS/边缘证据但无官方范围 → OBSERVED；
      ④ 无任何输入 → MISSING_INPUT。

    参数：
        declared_user_agent     : 请求声明的 UA/产品 token
        official_range_verified: 是否命中已核验的官方 IP 范围
        range_snapshot_version : 核验所用范围快照版本（归档证据）
        trusted_ingress         : 是否来自可信入口（公开 payload 自报 IP 不算）
        dns_or_edge_evidence    : 是否存在 DNS / 可信边缘证据
    返回：{state, note, can_claim_identity, limitations}
    """
    if not declared_user_agent and not official_range_verified and not trusted_ingress:
        return {
            "state": EvidenceState.MISSING_INPUT.value,
            "note": "缺少身份输入，无法判定",
            "can_claim_identity": False,
            "limitations": ["未提供 UA 声明或任何观测证据"],
        }

    # ② 完整核验链：UA + 官方范围 + 归档版本，三者齐备才允许声称身份
    if declared_user_agent and official_range_verified and range_snapshot_version:
        return {
            "state": EvidenceState.VERIFIED.value,
            "note": "UA 声明与官方范围快照一致，身份已核验",
            "can_claim_identity": True,
            "limitations": [OBSERVATION_ONLY_NOTE],
        }

    # 独立观测证据（三项互不推导，任一存在即说明「观测」已成立，但仍不等于身份核验）
    has_independent_evidence = (
        official_range_verified or dns_or_edge_evidence or trusted_ingress
    )

    # ① 仅 UA 声明、无任何独立证据 —— 上游明确禁止据此确认来源
    if declared_user_agent and not has_independent_evidence:
        return {
            "state": EvidenceState.UNKNOWN.value,
            "note": "仅有 UA 声明，不足以确认请求来源",
            "can_claim_identity": False,
            "limitations": [
                "UA 声明可被伪造，不构成身份证据",
                "官方 IP 范围未引入本项目（range_status=not_imported）",
                OBSERVATION_ONLY_NOTE,
            ],
        }

    # ③ 有独立观测证据但核验链不完整：记为 observed，仍禁止声称身份
    return {
        "state": EvidenceState.OBSERVED.value,
        "note": "已观测到访问，但身份核验链不完整",
        "can_claim_identity": False,
        "limitations": [
            "缺少官方范围归档快照版本" if official_range_verified else "官方范围未核验",
            OBSERVATION_ONLY_NOTE,
        ],
    }


def evidence_gap_report(
    *,
    has_content_inventory: bool,
    has_crawl_observations: bool,
    has_range_verification: bool,
    has_referral_sessions: bool,
    has_complete_window: bool,
) -> Dict[str, Any]:
    """
    汇总「证据缺口」，供报告输出。
    上游原则：Is there enough evidence for a conclusion? —— 缺口必须显式列出，
    而不是把结论算成 0 或省略。
    """
    gaps: List[str] = []
    if not has_content_inventory:
        gaps.append("未提供内容清单（sitemap/CSV/JSON），无法计算覆盖率与 AI 盲点")
    if not has_crawl_observations:
        gaps.append("无爬取观测记录，覆盖率结论不可用")
    if not has_range_verification:
        gaps.append("未完成官方范围核验，所有身份均为 unknown / observed")
    if not has_referral_sessions:
        gaps.append("无 AI 引荐会话数据，无法评估流量与转化")
    if not has_complete_window:
        gaps.append("观测窗口不完整，量化结果仅作参考，不得发布确定结论")

    return {
        "gap_count": len(gaps),
        "gaps": gaps,
        "conclusion_ready": len(gaps) == 0,
        "separate_evidence_required": list(SEPARATE_EVIDENCE_REQUIRED),
        "note": OBSERVATION_ONLY_NOTE,
    }
