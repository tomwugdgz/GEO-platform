"""
内容覆盖率 / AI 盲点 —— 借鉴 GEOInflow「内容清单 vs 观测日志」思路
=================================================================================
上游依据：
  · README.md：「Import a content inventory to measure observed crawl coverage
    and AI blind spots against a known set of pages.」
  · GitHub 旁证：waseemnasir2k26/aeo-crawl-radar 的 sitemap-gap report
    （仅借鉴思路，未引入任何代码）。

关键纪律：没有内容清单时返回 missing_input，不返回 0% 覆盖率；
覆盖率是「观测到的访问」而非「被收录/被引用」。
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


def _normalize(paths: Iterable[str]) -> List[str]:
    """规范化路径并去重：去除查询串与片段，保留大小写与尾部斜线（不做模糊匹配）。"""
    out: List[str] = []
    seen = set()
    for raw in paths:
        if not isinstance(raw, str):
            continue
        p = raw.split("?", 1)[0].split("#", 1)[0].strip()
        if not p:
            continue
        if not p.startswith("/"):
            p = "/" + p
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def compute_coverage(
    inventory_paths: Optional[Iterable[str]],
    observed_paths: Optional[Iterable[str]],
    *,
    exact_match: bool = True,
) -> Dict[str, Any]:
    """
    计算内容清单的观测覆盖率与 AI 盲点。

    参数：
        inventory_paths : 导入的内容清单（sitemap / CSV / JSON）
        observed_paths  : 已观测到爬取的路径集合
        exact_match     : 上游口径为精确路径匹配（保留尾部斜线），默认 True
    返回：{state, inventory_size, observed_size, covered_count, coverage_rate,
           blind_spots, limitations}
    """
    limitations = [
        "覆盖率仅表示『观测到的访问』，不证明收录、索引、训练或答案引用",
        "路径按精确匹配，/cases 与 /cases/ 视为不同路径",
    ]

    if inventory_paths is None:
        return {
            "state": "missing_input",
            "inventory_size": None,
            "observed_size": None,
            "covered_count": None,
            "coverage_rate": None,
            "blind_spots": [],
            "limitations": limitations + ["未提供内容清单，覆盖率不可计算（不返回 0%）"],
        }

    inventory = _normalize(inventory_paths)
    if not inventory:
        return {
            "state": "missing_input",
            "inventory_size": 0,
            "observed_size": None,
            "covered_count": None,
            "coverage_rate": None,
            "blind_spots": [],
            "limitations": limitations + ["内容清单为空，覆盖率不可计算"],
        }

    observed = set(_normalize(observed_paths or []))
    inv_set = set(inventory)
    covered = sorted(inv_set & observed)
    blind = sorted(inv_set - observed)

    return {
        "state": "observed",
        "inventory_size": len(inv_set),
        "observed_size": len(observed),
        "covered_count": len(covered),
        "coverage_rate": round(len(covered) / len(inv_set), 4),
        "covered_paths": covered,
        "blind_spots": blind,
        "limitations": limitations
        + ([] if observed else ["无爬取观测记录；盲点列表等于全量清单，不代表真实未抓取"]),
    }
