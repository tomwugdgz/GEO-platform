"""
GEOInflow 借鉴资产归集模块
=================================================================================
本模块集中归集从 GEOInflow（Liekan / Umami MIT 衍生项目）借鉴的**语言无关设计资产**，
并用本仓库既有技术栈（Python / SQLAlchemy / FastAPI）重新实现。

来源与许可：
    GEOInflow v1.2.0，MIT License
    Copyright (c) 2022 Umami Software, Inc. <hello@umami.is>
    Copyright (c) 2026 Liekan contributors
    完整声明见仓库根目录 THIRD_PARTY_NOTICES.md。

借鉴边界（重要）：
    · 仅借鉴【数据结构 / 状态口径 / 冻结策略 / 工程纪律】，未复制 TypeScript 源码；
    · 官方 IP 段（bot-ranges.json）属时效性运行数据，本项目【未引入】，
      只保留「来源 URL + 核验状态」的接口约定，不做真实性声明；
    · 远端爬虫控制（Cloudflare / robots 写操作）、Umami 浏览器跟踪、
      ClickHouse、pg-boss 队列等与现有栈冲突或超出范围的部分【未引入】。

模块清单：
    catalog_data.json  身份目录（结构源自 crawler-directory.md）
    catalog.py         身份目录查询与用途分类
    evidence.py        证据状态机（UA 声明 ≠ 身份确认；缺口显式化）
    policy.py          冻结 GEO Weight 策略（公式 + 档位 + 策略哈希）
    coverage.py        内容清单 vs 观察日志 → 覆盖率 / AI 盲点
    quality.py         零假数据纪律（空 / 缺失 / 估算 / 不支持 分状态）
    contracts.py       统一响应契约（data + evidence_state + policy_version）

对应上游文档：docs/ai-crawler-analytics.md、docs/crawler-recognition.md、
docs/crawler-directory.md、docs/geo-weight.md、docs/traffic-quality.md、AGENTS.md。
"""
from app.geoinflow_adapter.contracts import POLICY_VERSION, build_response
from app.geoinflow_adapter.evidence import EvidenceState
from app.geoinflow_adapter.policy import weight_from_units, weighted_activity

__all__ = [
    "EvidenceState",
    "POLICY_VERSION",
    "build_response",
    "weight_from_units",
    "weighted_activity",
]
