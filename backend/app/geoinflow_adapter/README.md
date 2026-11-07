# geoinflow_adapter — 借鉴资产归集模块

> 本目录是 **MTO/GEO 平台内专门归集「从 GEOInflow 引入内容」的独立模块**，
> 与既有业务模块解耦：所有借鉴资产集中在此，业务接入仅经由
> `app/api/geoinflow_routes.py` 与 `app/models/geoinflow_evidence.py`。

## 1. 来源与合规

| 项 | 内容 |
|---|---|
| 上游项目 | GEOInflow（产品名）／Liekan（技术标识），v1.2.0 / build 1.2.0 |
| 联合发布 | 猎看科技 · 北京日报社智源GEO |
| 许可 | **MIT** |
| 版权 | Copyright (c) 2022 Umami Software, Inc. `<hello@umami.is>`；Copyright (c) 2026 Liekan contributors |
| 上游血统 | Umami 的 MIT 衍生项目 |
| 引入日期 | 2026-11-07 |
| 合规登记 | 仓库根目录 [`THIRD_PARTY_NOTICES.md`](../../../../THIRD_PARTY_NOTICES.md) 第一章 |

**引入方式**：仅借鉴**数据结构 / 状态口径 / 冻结策略 / 工程纪律**，
用 Python 重写；**未复制任何 TypeScript 源码**，未引入上游运行时依赖。
MIT 要求的版权与许可声明已在 `THIRD_PARTY_NOTICES.md` 与 `LICENSE` 层面保留。

## 2. 归集清单与上游映射

| 本模块文件 | 借鉴自上游 | 作用 |
|---|---|---|
| `catalog_data.json` | `docs/crawler-directory.md` 目录结构；`docs/crawler-recognition.md` | AI 爬虫身份目录：稳定 ID / 厂商 / 用途 / AI 资格 / 官方范围 URL |
| `catalog.py` | `src/lib/liekan/crawlers`、统一目录发布约定 | 目录查询、UA 声明候选解析（不声称核验） |
| `evidence.py` | `docs/ai-crawler-analytics.md`、`docs/traffic-quality.md`、`docs/geo-weight.md` | 证据状态机：UA 声明 ≠ 身份确认；缺口显式化；观测 ≠ 收录/引用 |
| `policy.py` | `docs/geo-weight.md`（`geo-weight-v2.1-bands-evidence-beta`） | 冻结量化策略：公式、档位、策略哈希、证据门控 |
| `coverage.py` | README「content inventory / AI blind spots」；旁证 `aeo-crawl-radar` sitemap-gap | 内容清单 vs 观测 → 覆盖率与 AI 盲点 |
| `quality.py` | `AGENTS.md` 第 11 条「No fake production analytics」 | 空 / 缺失 / 估算 / 不支持 分状态；演示数据显式标注 |
| `contracts.py` | `src/lib/liekan/contracts` 分层约定 | 统一响应信封（data + evidence_state + policy_version + limitations） |

## 3. 借鉴但不引入（取舍记录）

| 上游能力 | 不引入原因 |
|---|---|
| Next.js 16 / Prisma 7 / TypeScript 全栈 | 与本仓库 FastAPI + SQLAlchemy + Vue3 双栈冲突，运维与数据割裂 |
| 官方 IP 段 `config/liekan/bot-ranges.json` | 时效性运行数据，需每小时抓取 + 版本归档；本项目未接入、未核验，不得据此认定来源。目录只保留 `official_range_url` 与 `range_status=not_imported` |
| Umami 浏览器跟踪脚本 / ClickHouse / pg-boss / rrweb 录制 | 与本仓库 `MonitorSnapshot` / `GeoTask` 重复，且属不同采集栈 |
| Cloudflare / robots 远端写控制 | 对外写操作，未获授权；且需独立 Zone 凭据 |
| AI 对话与模型连接 | 与既有 `llm_client.py` / `rag_kb.py` 重复 |
| 全量 28 个增量 SQL 迁移与 `liekan:upstream:*` 同步脚本 | 迁移体系绑定 Prisma；本仓库采用 SQLAlchemy `create_all`，不可直接套用 |
| 全量 i18n / 地理库 / 导出 ZIP | 超出本次范围；仓库已有中英 README 双语约定 |

## 4. 与现有系统的兼容边界

- **不改动** `services/mock_data.py`、`diagnosis_routes.py`、`monitor_routes.py` 等既有业务文件；
  新增模块强制「零假数据」，既有模块保持原状，互不干扰。
- **不新增第三方依赖**：仅用 Python 标准库 + 仓库既有 SQLAlchemy / FastAPI / Pydantic。
- **不与现有表重复**：新增表 `geo_crawler_observations` 与既有
  `geo_monitor_snapshots`（AI 平台提及率快照）、`geo_metric_snapshots`（指标时序快照）
  语义不同——本表存「单条爬取观测 + 核验证据链」。
- **API 前缀隔离**：`/api/v2/mto/evidence`，不与 `/api/v2/geolook`、
  `/api/v2/trend`、`/api/v2/geo/monitor` 冲突。

## 5. 使用

```python
from app.geoinflow_adapter.evidence import classify_identity, EvidenceState
from app.geoinflow_adapter.policy import weight_from_units, describe_policy
from app.geoinflow_adapter.coverage import compute_coverage
from app.geoinflow_adapter.catalog import summarize, parse_declared_ua

# UA 声明不足以确认来源
classify_identity(declared_user_agent="GPTBot")["state"]        # -> "unknown"
# 完整核验链才允许声称身份
classify_identity("GPTBot", True, "range-snapshot-2026-11")["state"]  # -> "verified"
# 冻结策略（上游算例：3000/400/8000 -> W=56800 -> level 6）
weight_from_units(3000, 400, 8000)["level"]                   # -> 6
# 缺清单时返回 missing_input，不返回 0%
compute_coverage(None, ["/a"])["state"]                        # -> "missing_input"
```

## 6. 已知限制（如实声明）

1. 官方 IP 范围未引入，**所有身份核验结果最高只能到 `observed`**；
   目录中的 `official_range_url` 仅为来源记录，未验证其当前有效性。
2. 量化系数为上游 Beta 参数，未经跨行业校准；本仓库未做真实数据验证。
3. 内容覆盖率需要调用方导入内容清单；未导入时结论不可用。
4. 本模块不产生收录、引用、排名或转化结论。
