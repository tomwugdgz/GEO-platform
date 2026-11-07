# 第三方组件与开源许可声明 / Third-Party Notices

本文件列出「青柠GEO」（GEO-platform）仓库中**引入、复制或改编**的第三方开源组件及其许可条款。
本仓库自身采用 MIT 许可证（见 [`LICENSE`](LICENSE)）。

---

## 一、被直接引入源码的第三方组件（重要）

### 1. GeoLook —— GEO 引擎内核

| 项目 | 说明 |
|---|---|
| 上游项目 | [aigclink/geolook](https://github.com/aigclink/geolook) |
| 上游官网 | https://geolook.cc |
| 版权持有者 | Copyright (c) 2026 GeoLook contributors |
| 许可协议 | **MIT License** |
| 引入位置 | [`backend/geolook/`](backend/geolook/)（含其 `LICENSE` 副本） |
| 引入方式 | 源码整体引入 + 局部适配（**未修改上游核心算法**） |

**引入的内容：**

- `geo.py` —— 上游 GEO 自动化管线 CLI 入口
- `audit.py` / `crawl.py` / `sample.py` / `blueprint.py` / `tasks.py` / `verify.py` /
  `generate.py` / `report.py` / `publish.py` / `deliver.py` / `deliverables.py` /
  `analytics.py` / `benchmark.py` / `dashboard.py` / `expand.py` / `bootstrap.py` /
  `geolib.py` / `jobs.py` —— 上游各功能模块
- `references/` —— 上游 GEO 方法论参考文献（`method.md`、`attribution.md`、
  `cn-platforms.md`、`cn-source-ranking.md`、`content-patterns.md`、
  `global-platforms.md`、`sources.md`）
- `ui.html` / `service.sh` —— 上游单文件界面与启动脚本

**本项目所做的适配（属于 MIT 许可明确允许的修改权）：**

| 文件 | 变更 |
|---|---|
| `_win_fcntl.py` | **本项目新增**：Windows 平台 `fcntl` 兼容层（上游仅支持类 Unix） |
| `backend/app/api/geolook_routes.py` | **本项目新增**：将上游 CLI 能力封装为 REST 接口（前缀 `/api/v2/geolook`） |
| `backend/geolook/work/` | 运行时产出目录，**不入库**（见 `.gitignore`） |

**MIT 合规说明：** MIT 许可证要求「上述版权声明和许可声明应包含在本软件的所有副本或实质性部分中」。
本项目已在该目录内保留完整的上游 `LICENSE`（版权行：`Copyright (c) 2026 GeoLook contributors`），
以履行该义务。

---

### 2. GEOInflow —— 证据链与量化策略的**设计借鉴**（未复制源码）

| 项目 | 说明 |
|---|---|
| 上游项目 | GEOInflow（产品展示名）／Liekan（技术标识），v1.2.0 / build 1.2.0 |
| 联合发布 | 猎看科技 · 北京日报社智源GEO |
| 上游官网/来源 | 本地参考副本 `D:\download\geoinflow-main`（非本仓库分发内容） |
| 版权持有者 | Copyright (c) 2022 Umami Software, Inc. `<hello@umami.is>`；Copyright (c) 2026 Liekan contributors |
| 许可协议 | **MIT License** |
| 引入位置 | [`backend/app/geoinflow_adapter/`](backend/app/geoinflow_adapter/)（含其 `README.md`） |
| 引入方式 | **仅借鉴语言无关的设计资产**（数据结构 / 状态口径 / 冻结策略 / 工程纪律），用 Python 重写；**未复制任何 TypeScript / Prisma / Next.js 源码** |

**借鉴的具体内容：**

| 上游文档 | 借鉴内容 | 本仓库落地 |
|---|---|---|
| `docs/crawler-directory.md`、`docs/crawler-recognition.md` | AI 爬虫身份目录结构（稳定 ID / 厂商 / 用途 / AI 资格 / 官方范围来源） | `geoinflow_adapter/catalog_data.json`、`catalog.py` |
| `README.md`、`docs/traffic-quality.md` | 「UA 声明 ≠ 身份确认」；声明 / 官方范围 / DNS 边缘证据独立存储；空 / 缺失 / 估算 / 不支持 分状态 | `geoinflow_adapter/evidence.py`、`quality.py` |
| `docs/geo-weight.md` | 冻结量化公式 `W = 10·E_search + 7·E_user + 3·E_training`、固定档位、策略哈希、证据门控（缺失返回 null） | `geoinflow_adapter/policy.py` |
| `README.md`（content inventory / AI blind spots） | 内容清单 vs 观测日志的覆盖率与盲点算法 | `geoinflow_adapter/coverage.py` |
| `src/lib/liekan/contracts` 分层约定、`AGENTS.md` 工程纪律 | 统一响应契约、增量不可变迁移、演示数据显式标注 | `geoinflow_adapter/contracts.py`、`README.md` |

**明确未引入（取舍）：** 官方 IP 段 `config/liekan/bot-ranges.json`（时效性运行数据，未核验）、
Umami 跟踪脚本、ClickHouse、pg-boss、rrweb 录制、Cloudflare/robots 远端写控制、
上游 28 个 Prisma 迁移与 i18n/地理库。

**MIT 合规说明：** 本节保留上游完整版权行与许可名称；上游 `LICENSE` 全文
（含 Umami 与 Liekan 两行版权）见参考副本 `D:\download\geoinflow-main\LICENSE`。
本仓库未分发上游源码，故不复制其 `LICENSE` 文件，但保留上述版权声明以履行通知义务。
所有借鉴产物的来源、边界与已知限制集中记录于
[`backend/app/geoinflow_adapter/README.md`](backend/app/geoinflow_adapter/README.md)。

---

## 二、运行时依赖（未复制源码，仅通过包管理器引用）

以下依赖以**声明式依赖**方式引入，其源码不属于本仓库的分发内容，各自遵循其原始许可：

### 后端（Python）

| 组件 | 许可 | 用途 |
|---|---|---|
| [FastAPI](https://github.com/fastapi/fastapi) | MIT | Web 框架 |
| [Uvicorn](https://github.com/encode/uvicorn) | BSD-3-Clause | ASGI 服务器 |
| [Pydantic](https://github.com/pydantic/pydantic) | MIT | 数据校验 |
| [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) | MIT | ORM |
| [LangChain](https://github.com/langchain-ai/langchain) / [LangGraph](https://github.com/langchain-ai/langgraph) | MIT | LLM 应用与编排框架 |
| [ChromaDB](https://github.com/chroma-core/chroma) | Apache-2.0 | 向量数据库 |
| [sentence-transformers](https://github.com/UKPLab/sentence-transformers) | Apache-2.0 | 中文向量嵌入 |

### 前端（Node.js）

| 组件 | 许可 | 用途 |
|---|---|---|
| [Vue 3](https://github.com/vuejs/core) | MIT | 前端框架 |
| [Vue Router](https://github.com/vuejs/router) | MIT | 路由 |
| [Element Plus](https://github.com/element-plus/element-plus) | MIT | UI 组件库 |
| [Axios](https://github.com/axios/axios) | MIT | HTTP 客户端 |
| [Vite](https://github.com/vitejs/vite) | MIT | 构建工具 |

> 完整的传递依赖树请以 `backend/requirements.txt` 与 `bmn-frontend/package.json` 为准；
> 可用 `pip-licenses`、`license-checker` 等工具生成完整清单。

---

## 三、第三方服务与数据

本项目的部分功能需要调用**第三方 AI 服务与搜索引擎**（如智谱 GLM、火山方舟、DeepSeek、
Kimi、MiniMax、Gemini、OpenAI、Anthropic、xAI、Perplexity 等）。

- 相关 API Key 由**使用者自行申请并配置**，本仓库不包含任何可直接使用的密钥；
- 使用时须遵守各服务提供方的服务条款、配额与调用限制；
- 站点抓取（`crawl`）功能产生的内容归原网站所有，仅供**个人研究分析**使用；
  使用者应自行确认符合目标站点的 `robots.txt` 与使用条款，不得用于批量转载或再分发。

---

## 四、权利主张与删除请求 / Takedown

本项目为**个人非商业性质的学习与研究项目**，无意侵犯任何主体的合法权益。

如您是某作品的著作权人、商标权人或其授权代理人，并认为本仓库中的任何内容侵犯了您的权利，
请通过以下方式联系，我们将在**核实后第一时间删除相关内容或下架整个仓库**：

- 邮箱：[duckwolf@qq.com](mailto:duckwolf@qq.com)
- GitHub Issue：[提交 Issue](https://github.com/tomwugdgz/GEO-platform/issues)

为便于快速处理，请在联系时提供：

1. 您的身份与权利证明（著作权登记、商标注册证等）；
2. 涉嫌侵权内容在本仓库中的**具体位置**（文件路径或链接）；
3. 您的联系方式。

我们承诺：**不进行任何抗辩、不要求任何补偿、不设置任何前置条件**，收到有效通知即行处理。

---

*本文件随项目持续更新。最后更新：2026-09-10*
