"""
冻结量化策略 —— 借鉴 GEOInflow「GEO Weight」的可证伪量化范式
=================================================================================
上游依据：docs/geo-weight.md（策略 geo-weight-v2.1-bands-evidence-beta）
  · 公式 W = 10 × E_search + 7 × E_user + 3 × E_training
    系数保持 search : user : training = 50 : 35 : 15 的相对重要性；
  · 只统计内容 GET 200/304，按 (站点, 主机, 用途, 厂商, 路径, 本地日期) 去重；
  · 档位为固定整数区间，结果上限 10；确证的观测零单独表示为 0；
  · 缺失输入 / 不可用证据 → 返回 null，不返回 0，不重新分配权重；
  · 策略版本、系数与边界参与哈希，作为缓存键与导出快照的一部分。

本项目的取舍：
  · 借鉴【公式 + 档位 + 冻结策略 + 证据门控】，不复制上游的 PgBoss/快照/租约实现；
  · 策略 ID 改为本仓库命名空间 `mto-evidence-weight-v1`，避免与上游版本混淆；
  · 该权重描述「已观测的 AI 内容访问量」，是 MTO trust_score 的【可解释补充】，
    不等同于机器信任、引用率或成交，不得用于商业承诺。

可验证锚点（上游文档给出的算例）：
  E_search=3000, E_user=400, E_training=8000
  → W = 10*3000 + 7*400 + 3*8000 = 56,800 → 档位 6
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

# ── 冻结策略标识 ────────────────────────────────────────────────────────────
POLICY_ID = "mto-evidence-weight-v1"
UPSTREAM_POLICY_ID = "geo-weight-v2.1-bands-evidence-beta"
WINDOW_DAYS = 30  # 上游：30 个完整日历日

# 用途系数（冻结，修改需同步提升 POLICY_ID 版本）
COEFFICIENTS: Dict[str, int] = {
    "ai_search": 10,
    "user_initiated": 7,
    "ai_training": 3,
}

# 档位下界（含）。上游文档的固定区间，逐条照录。
BANDS: List[Tuple[int, int, Optional[int]]] = [
    (1, 1, 99),
    (2, 100, 499),
    (3, 500, 1999),
    (4, 2000, 9999),
    (5, 10000, 49999),
    (6, 50000, 199999),
    (7, 200000, 999999),
    (8, 1000000, 4999999),
    (9, 5000000, 19999999),
    (10, 20000000, None),  # None 表示无上界
]


def policy_hash() -> str:
    """把策略 ID / 系数 / 档位边界一起哈希，供缓存键与导出快照标识使用。

    上游原则「算法版本、系数与边界参与策略哈希」——任何口径变更都会改变哈希，
    从而避免新旧结果被静默混用。
    """
    payload = {
        "policy_id": POLICY_ID,
        "window_days": WINDOW_DAYS,
        "coefficients": COEFFICIENTS,
        "bands": BANDS,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def weighted_activity(
    e_search: int,
    e_user: int,
    e_training: int,
) -> int:
    """计算加权活动量 W = 10*E_search + 7*E_user + 3*E_training。

    参数应为已在 30 天窗口内去重后的单位数；本函数不负责去重（由调用方/数据层保证）。
    """
    for name, v in (("e_search", e_search), ("e_user", e_user), ("e_training", e_training)):
        if not isinstance(v, int) or v < 0:
            raise ValueError(f"{name} 必须为非负整数，实际为 {v!r}")
    return (
        COEFFICIENTS["ai_search"] * e_search
        + COEFFICIENTS["user_initiated"] * e_user
        + COEFFICIENTS["ai_training"] * e_training
    )


def level_from_activity(w: int) -> int:
    """按固定区间把 W 映射到 1~10 档；W<1 时返回 0（表示确证的观测零）。"""
    if w < 1:
        return 0
    for level, low, high in BANDS:
        if w >= low and (high is None or w <= high):
            return level
    return 10


def weight_from_units(
    e_search: Optional[int],
    e_user: Optional[int],
    e_training: Optional[int],
    *,
    evidence_complete: bool = True,
    proved_zero: bool = False,
) -> Dict[str, Any]:
    """
    带【证据门控】的权重计算（对齐上游「缺失输入返回 null」规则）。

    参数：
        e_* / evidence_complete: 三项单位数与观测窗口是否完整
        proved_zero            : 是否在完整观测下确证为 0
    返回：{level, weighted_units, policy_id, policy_hash, state, limitations}
        · 证据不完整或任一输入缺失 → level=None、weighted_units=None、state=missing_input
        · 完整观测且确证为 0 → level=0、weighted_units=0、state=proved_zero
        · 其余 → 按公式计算，state=observed/estimated
    """
    missing = [k for k, v in (("e_search", e_search), ("e_user", e_user), ("e_training", e_training)) if v is None]
    limitations = [
        "该权重仅描述已观测的 AI 内容访问量，不代表引用、训练收录、推荐排名或获客",
        "系数为 Beta 参数，未经跨行业校准，不构成商业决策依据",
        "官方范围核验未在本项目启用，身份可能为 unknown/observed",
    ]

    if missing or not evidence_complete:
        return {
            "level": None,
            "weighted_units": None,
            "policy_id": POLICY_ID,
            "policy_hash": policy_hash(),
            "state": "missing_input",
            "missing_inputs": missing,
            "limitations": limitations + ["观测窗口不完整或输入缺失，按上游规则返回 null 而非 0"],
        }

    w = weighted_activity(int(e_search), int(e_user), int(e_training))
    if w == 0:
        if not proved_zero:
            return {
                "level": None, "weighted_units": None,
                "policy_id": POLICY_ID, "policy_hash": policy_hash(),
                "state": "missing_input",
                "missing_inputs": [],
                "limitations": limitations + ["W=0 但缺少『完整观测』确证，不得发布观测零"],
            }
        return {
            "level": 0, "weighted_units": 0,
            "policy_id": POLICY_ID, "policy_hash": policy_hash(),
            "state": "proved_zero",
            "missing_inputs": [],
            "limitations": limitations,
        }

    return {
        "level": level_from_activity(w),
        "weighted_units": w,
        "policy_id": POLICY_ID,
        "policy_hash": policy_hash(),
        "state": "estimated" if not evidence_complete else "observed",
        "missing_inputs": [],
        "limitations": limitations,
    }


def describe_policy() -> Dict[str, Any]:
    """返回冻结策略全文（供 /policy 端点与导出快照使用）。"""
    return {
        "policy_id": POLICY_ID,
        "derived_from": UPSTREAM_POLICY_ID,
        "window_days": WINDOW_DAYS,
        "formula": "W = 10*E_search + 7*E_user + 3*E_training",
        "coefficients": COEFFICIENTS,
        "bands": [
            {"level": lv, "min": lo, "max": hi} for lv, lo, hi in BANDS
        ],
        "policy_hash": policy_hash(),
        "rules": [
            "只统计内容 GET 200/304，按(站点,主机,用途,厂商,路径,本地日期)去重",
            "无效 MIME、元数据路径、静态资源与自检请求排除",
            "缺失输入或不可用证据返回 null，不返回 0、不重新分配权重",
            "确证的观测零单独表示为 level=0",
            "策略 ID、系数与边界共同参与哈希，口径变更必须提升版本",
        ],
    }
