"""
AI 爬虫身份目录查询 —— 借鉴 GEOInflow「统一目录发布」结构
=================================================================================
上游依据：
  · docs/crawler-recognition.md：「身份目录维护稳定 ID、名称、厂商、用途与能力。
    HTTP 识别、官方范围核验、来源归因、robots 草稿和远端控制分别声明能力。
    名称表示请求声明的身份，核验状态单独展示。」
  · docs/crawler-directory.md：目录条目表（名称 / 厂商 / 用途分类 / AI 请求 /
    自动范围来源）。
  · README.md：「The catalog records platforms, products, and request identities
    separately. Training, AI search, and user-triggered access describe request
    purposes; AI workbenches and personal agents describe product types.
    These dimensions can overlap.」

本项目实现：从 catalog_data.json 加载静态目录，提供按厂商/用途/AI 资格查询，
以及「UA token → 候选身份」的解析（仅返回候选，不声称核验）。
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

_CATALOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "catalog_data.json")


@lru_cache(maxsize=1)
def load_catalog() -> Dict[str, Any]:
    """加载并缓存身份目录（进程内只读）。"""
    with open(_CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def all_entries() -> List[Dict[str, Any]]:
    """返回全部身份条目。"""
    return list(load_catalog()["entries"])


def find_by_name(name: str) -> Optional[Dict[str, Any]]:
    """按 HTTP 名称精确查找（大小写不敏感）。仅匹配声明名称，不代表身份已核验。"""
    target = name.strip().lower()
    for e in all_entries():
        if e["name"].lower() == target:
            return dict(e)
    return None


def filter_entries(
    *,
    vendor: Optional[str] = None,
    purpose: Optional[str] = None,
    ai_eligible: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    """按厂商 / 用途 / AI 资格筛选目录条目。"""
    out = []
    for e in all_entries():
        if vendor and e["vendor"].lower() != vendor.lower():
            continue
        if purpose and e["purpose"] != purpose:
            continue
        if ai_eligible is not None and e["ai_eligible"] != ai_eligible:
            continue
        out.append(dict(e))
    return out


def summarize() -> Dict[str, Any]:
    """目录摘要：总量、AI 资格数、用途分布、厂商数、核验范围引入状态。"""
    entries = all_entries()
    purposes: Dict[str, int] = {}
    for e in entries:
        purposes[e["purpose"]] = purposes.get(e["purpose"], 0) + 1
    return {
        "schema_version": load_catalog()["schema_version"],
        "entry_count": len(entries),
        "ai_eligible_count": sum(1 for e in entries if e["ai_eligible"]),
        "vendor_count": len({e["vendor"] for e in entries}),
        "purpose_distribution": purposes,
        "range_imported": False,
        "range_status": "not_imported",
        "notice": load_catalog()["notice"],
        "not_imported_notice": load_catalog()["not_imported_notice"],
    }


def parse_declared_ua(user_agent: str) -> Dict[str, Any]:
    """
    从 UA 字符串中提取【声明】的身份候选。

    明确边界：这里只做字符串匹配，返回的是「请求自称是谁」，
    不产生 VERIFIED 状态；身份核验须由 classify_identity() 另行判定。
    """
    if not isinstance(user_agent, str) or not user_agent.strip():
        return {"declared": None, "candidates": [], "note": "未提供 UA"}

    lowered = user_agent.lower()
    candidates = [
        dict(e) for e in all_entries()
        if e["name"].lower() in lowered
    ]
    return {
        "declared": user_agent,
        "candidates": candidates,
        "candidate_count": len(candidates),
        "note": "以下为 UA 声明匹配到的候选身份，不构成身份核验（UA 可伪造）",
    }
