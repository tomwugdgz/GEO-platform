"""
MTO 趋势与优化顾问服务
=================================================================================
输入：一段时间累积的 MTO / GEO 指标快照（MetricSnapshot 列表，按时间排序）
处理：
  ① 统计判别（数据驱动）：对各关键指标做线性回归，得到斜率 + 下一期预测；
  ② AI 判别（Laya 决策引擎）：把近期状态写成「人话战报」喂给 Laya，
     由它在若干【可执行】优化方向中选出最优（LAYA 本地 GPU / JEV 远程 auto 切换）。
输出：趋势方向 + 统计预测 + 选定优化方向 + 置信度 + 攻击性分数 + 战败报。

设计要点（对齐 laya_bridge 实战范式）：
  · state 必须写成人话战报，不喂 JSON 字段表（否则 Laya 读不懂）；
  · 候选方案只生成真正能执行的，且至少 2 个、最多 ~5 个；
  · 不生成零输出 / 纯「按兵不动」方案（会诱发摆烂）；
  · Laya 不可用时（未安装 / 网络不通）自动降级为「最弱指标优先」启发式选择。
"""
from __future__ import annotations

import os
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Laya 决策引擎接入（本地 LAYA / 远程 JEV = bocha-jev-v1，auto 自动切换）
# ─────────────────────────────────────────────────────────────────────────────
# laya_bridge 安装在 D:\laya_bridge，并通过 .pth 挂到 laya_cuda_venv 与系统 python。
# GEO 后端使用自己的 venv，故此处兜底把该目录加入 sys.path，使其可被 import。
_LAYA_BRIDGE_DIR = r"D:\laya_bridge"
_laya = None
_laya_import_error: Optional[str] = None
try:
    import laya_bridge  # type: ignore
    _laya = laya_bridge
except Exception as _e1:  # 找不到时兜底加路径再试
    try:
        if os.path.isdir(_LAYA_BRIDGE_DIR) and _LAYA_BRIDGE_DIR not in sys.path:
            sys.path.insert(0, _LAYA_BRIDGE_DIR)
        import laya_bridge  # type: ignore
        _laya = laya_bridge
    except Exception as _e2:
        _laya_import_error = f"{type(_e2).__name__}: {_e2}"


# ─────────────────────────────────────────────────────────────────────────────
# 关键指标（用于统计趋势 + 战败报 + 候选方向生成）
# ─────────────────────────────────────────────────────────────────────────────
# (快照字段名, 中文名, 越低越需要优化的方向描述)
_TREND_FIELDS = [
    ("aivo_total", "AIVO综合分"),
    ("aivo_ai_visibility", "AI可见性"),
    ("mention_rate", "AI平台平均提及率"),
    ("aivo_sentiment", "舆情健康度(诊断)"),
    ("sentiment_health", "舆情健康度(监测)"),
    ("aivo_advantage", "竞争优势"),
    ("aivo_infrastructure", "基建完善度"),
    ("trust_score", "MTO信任分"),
    ("evidence_completeness", "证据链完整性"),
]


def _opt_direction(field_cn: str) -> str:
    """给定指标中文名，返回对应的可执行优化方向文案。"""
    return {
        "AIVO综合分": "整体提升品牌GEO综合表现：补齐最弱子项并持续累积内容资产",
        "AI可见性": "优先提升AI平台可见性：批量铺设问答/对比类内容，争夺推荐位",
        "AI平台平均提及率": "提升AI平台提及率：增加权威媒体与自媒体覆盖，强化被引用概率",
        "舆情健康度(诊断)": "强化舆情健康：及时响应负面提及，沉淀正向口碑内容",
        "舆情健康度(监测)": "强化舆情健康：监控各平台出镜与负向信号，快速处置",
        "竞争优势": "强化差异化竞争优势：突出核心卖点与场景化价值",
        "基建完善度": "稳固基建：优化官网TDK与移动端，扩充自媒体矩阵",
        "MTO信任分": "补强MTO信任分：把检测报告/资质/成分结构化并接入可核验证据",
        "证据链完整性": "完善证据链完整性：建立主张→证据→溯源的三段式映射",
    }.get(field_cn, f"优化「{field_cn}」")


# ─────────────────────────────────────────────────────────────────────────────
# 数据规整
# ─────────────────────────────────────────────────────────────────────────────
def snapshot_to_metrics(snap) -> Dict[str, Any]:
    """把 ORM 快照（或 dict）规整为统一指标字典。"""
    if isinstance(snap, dict):
        d = dict(snap)
    else:
        d = {
            "id": str(getattr(snap, "id", "")),
            "tenant_id": str(getattr(snap, "tenant_id", "")) if getattr(snap, "tenant_id", None) else None,
            "brand_id": str(getattr(snap, "brand_id", "")) if getattr(snap, "brand_id", None) else None,
            "period_label": getattr(snap, "period_label", None),
            "source": getattr(snap, "source", "manual"),
            "snapshot_at": getattr(snap, "snapshot_at", None),
        }
        for f, _ in _TREND_FIELDS:
            d[f] = getattr(snap, f, None)
        extra = getattr(snap, "metrics", None) or {}
        if isinstance(extra, dict):
            d.update(extra)
    return d


def _sort_and_prepare(snapshots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按 snapshot_at 升序排列（保证时序方向正确）。"""
    def _ts(s):
        t = s.get("snapshot_at")
        if hasattr(t, "timestamp"):
            return t.timestamp()
        if isinstance(t, str):
            try:
                from datetime import datetime
                return datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()
            except Exception:
                return 0.0
        return 0.0
    return sorted(snapshots, key=_ts)


# ─────────────────────────────────────────────────────────────────────────────
# ① 统计判别（数据驱动）
# ─────────────────────────────────────────────────────────────────────────────
def compute_statistical_trend(snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    对各关键指标做一元线性回归，得到斜率(slope)、最新值、下一期预测。
    综合趋势方向由 aivo_total / trust_score / mention_rate 加权判定。
    """
    snaps = _sort_and_prepare(snapshots)
    n = len(snaps)
    if n < 2:
        return {"ok": False, "error": "快照不足 2 期，无法做统计趋势", "n": n}

    x = np.arange(n, dtype=float)
    per_field: Dict[str, Any] = {}
    for f, cn in _TREND_FIELDS:
        ys = [s.get(f) for s in snaps]
        ys = [y for y in ys if isinstance(y, (int, float))]
        if len(ys) >= 2:
            slope, intercept = np.polyfit(x[:len(ys)], np.array(ys, dtype=float), 1)
            last = float(ys[-1])
            per_field[f] = {
                "cn": cn,
                "slope": round(float(slope), 4),
                "latest": round(last, 2),
                "forecast_next": round(float(intercept + slope * n), 2),
                "n": len(ys),
            }

    # 综合方向：优先看 AIVO 综合分，其次信任分，其次提及率
    composite = None
    for key in ("aivo_total", "trust_score", "mention_rate"):
        if key in per_field:
            composite = per_field[key]["slope"]
            break
    if composite is None and per_field:
        composite = float(np.mean([v["slope"] for v in per_field.values()]))

    if composite is None:
        direction = "unknown"
    elif composite > 0.3:
        direction = "up"
    elif composite < -0.3:
        direction = "down"
    else:
        direction = "flat"

    return {
        "ok": True,
        "n": n,
        "period_first": snaps[0].get("period_label") or str(snaps[0].get("snapshot_at")),
        "period_last": snaps[-1].get("period_label") or str(snaps[-1].get("snapshot_at")),
        "composite_slope": round(composite, 4) if composite is not None else None,
        "direction": direction,
        "fields": per_field,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ② 人话战报（喂给 Laya 的 state）
# ─────────────────────────────────────────────────────────────────────────────
def build_state_report(snapshots: List[Dict[str, Any]]) -> str:
    """把近期快照写成一段人话战报（不喂 JSON 字段表，符合 Laya 实战范式）。"""
    snaps = _sort_and_prepare(snapshots)
    n = len(snaps)
    latest = snaps[-1]
    prev = snaps[-2] if n >= 2 else None

    lines = [f"这是 MTO / GEO 品牌资产的第 {n} 次累积评估。"]
    # 最新一期关键数值
    vals = "，".join(
        f"{cn} {latest.get(f)}" for f, cn in _TREND_FIELDS if isinstance(latest.get(f), (int, float))
    )
    lines.append(f"最近一期（{latest.get('period_label') or latest.get('snapshot_at')}）：{vals}。")
    # 环比变化
    if prev is not None:
        deltas = []
        for f, cn in _TREND_FIELDS:
            a, b = prev.get(f), latest.get(f)
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                d = round(b - a, 2)
                arrow = "上升" if d > 0 else ("下降" if d < 0 else "持平")
                deltas.append(f"{cn}{arrow}{abs(d)}")
        if deltas:
            lines.append("相较上一期：" + "，".join(deltas) + "。")
    # 统计趋势结论
    stat = compute_statistical_trend(snaps)
    if stat.get("ok"):
        lines.append(
            f"统计回归显示综合斜率 {stat.get('composite_slope')}，整体趋势"
            f"{'向上' if stat.get('direction') == 'up' else '向下' if stat.get('direction') == 'down' else '走平'}。"
        )
    # 约束
    lines.append(
        "你是指挥官。现在要决定下一步优化重心：必须选一个真正能执行、能带来正收益的方向，"
        "不要选零产出的方案。"
    )
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# ③ 候选优化方向（数据驱动，只生成可执行项）
# ─────────────────────────────────────────────────────────────────────────────
def build_candidates(snapshots: List[Dict[str, Any]]) -> List[str]:
    """根据数据动态生成可执行优化方向（不生成零输出 / 纯待机方案）。"""
    snaps = _sort_and_prepare(snapshots)
    if not snaps:
        return ["先累积至少 2 期指标快照再判别方向"]
    latest = snaps[-1]
    prev = snaps[-2] if len(snaps) >= 2 else None

    # 评分：当前值低 或 近期下降 的指标，权重更高（更该优先优化）
    scored = []
    for f, cn in _TREND_FIELDS:
        v = latest.get(f)
        if not isinstance(v, (int, float)):
            continue
        drop = 0.0
        if prev is not None and isinstance(prev.get(f), (int, float)):
            drop = float(prev.get(f)) - v  # 正=下降
        # 归一化缺口（相对 100 分制；未达 100 的缺口越大越该补）
        gap = max(0.0, 100.0 - v)
        priority = gap + max(0.0, drop) * 5.0
        scored.append((priority, f, cn))

    scored.sort(reverse=True)
    # 取前 4 个最该优化的方向 + 1 个「扩大优势」兜底（保证 ≥2 且非全待机）
    candidates: List[str] = []
    for _, f, cn in scored[:4]:
        candidates.append(_opt_direction(cn))

    # 若整体健康向上，补一条「扩大优势并持续监测」可执行项
    if candidates:
        candidates.append("扩大现有优势：在表现最好的渠道/内容上加码投入，并持续累积监测数据")
    # 去重保序
    seen, uniq = set(), []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq[:5] if uniq else ["先累积至少 2 期指标快照再判别方向"]


# ─────────────────────────────────────────────────────────────────────────────
# ④ 调用 Laya 决策引擎（LAYA 本地 / JEV 远程）
# ─────────────────────────────────────────────────────────────────────────────
def _call_laya(state_report: str, candidates: List[str], backend: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    调用 Laya。返回 (result_dict, error)。
    result_dict: { idx, text, score, conf, ms, backend_used }
    """
    if _laya is None:
        return None, f"laya_bridge 不可用: {_laya_import_error}"
    try:
        b, note = _laya.probe(backend)
        idx, text, score, conf, ms = _laya.ask(state_report, candidates, backend=backend)
        return {
            "idx": int(idx),
            "text": str(text),
            "aggression": float(score),
            "confidence": float(conf),
            "ms": float(ms),
            "backend_used": b,
            "backend_note": note,
        }, None
    except Exception as e:
        return None, f"Laya 调用失败: {type(e).__name__}: {e}"


def _heuristic_select(candidates: List[str], snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Laya 不可用时的兜底：选最弱指标对应的方向（取第一个候选）。"""
    snaps = _sort_and_prepare(snapshots)
    latest = snaps[-1] if snaps else {}
    worst = None
    worst_val = 1e9
    for f, cn in _TREND_FIELDS:
        v = latest.get(f)
        if isinstance(v, (int, float)) and v < worst_val:
            worst_val, worst = v, cn
    idx = 0
    if worst and candidates:
        # 候选首项通常对应最弱项（build_candidates 已按优先级排序）
        idx = 0
    return {
        "idx": idx,
        "text": candidates[idx] if candidates else "数据不足",
        "aggression": 0.5,
        "confidence": 0.3,
        "ms": 0.0,
        "backend_used": "heuristic",
        "backend_note": f"Laya 不可用，按最弱指标({worst or '未知'}={worst_val})启发式选择",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────────────────────────────────────
def predict_trend(snapshots: List[Dict[str, Any]], backend: str = "auto") -> Dict[str, Any]:
    """
    MTO 趋势与优化顾问主入口。

    参数：
        snapshots: 指标快照列表（ORM 或 dict 均可，需含 snapshot_at 时序）
        backend : "local"(LAYA 本地GPU) / "remote"(JEV 远程) / "auto"(默认，有CUDA走本地否则远程)
    返回：结构化判别结果。
    """
    snaps = [snapshot_to_metrics(s) for s in snapshots]
    if len(snaps) < 2:
        return {
            "ok": False,
            "error": "累积数据不足（至少需要 2 期快照）",
            "suggestion": "先通过 /api/v2/trend/snapshot 累积多期 MTO/GEO 指标",
            "snapshots_count": len(snaps),
        }

    state_report = build_state_report(snaps)
    candidates = build_candidates(snaps)
    stat = compute_statistical_trend(snaps)

    laya_res, laya_err = _call_laya(state_report, candidates, backend)
    if laya_res is None:
        laya_res = _heuristic_select(candidates, snaps)
        laya_res["fallback_reason"] = laya_err

    return {
        "ok": True,
        "backend": laya_res.get("backend_used"),
        "backend_note": laya_res.get("backend_note"),
        "snapshots_count": len(snaps),
        "statistical_trend": {
            "direction": stat.get("direction"),
            "composite_slope": stat.get("composite_slope"),
            "period_first": stat.get("period_first"),
            "period_last": stat.get("period_last"),
            "fields": stat.get("fields", {}),
        },
        "selected_direction": laya_res.get("text"),
        "selected_index": laya_res.get("idx"),
        "all_candidates": candidates,
        "aggression": laya_res.get("aggression"),     # 0~1：偏保守/偏进攻
        "confidence": laya_res.get("confidence"),     # 0~1：置信度
        "latency_ms": laya_res.get("ms"),
        "state_report": state_report,
    }
