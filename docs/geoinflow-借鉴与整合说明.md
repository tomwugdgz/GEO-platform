# GEOInflow 参考项目 → MTO 平台：借鉴评估、取舍与整合交付报告

- **参考项目**：`D:\download\geoinflow-main`（GEOInflow / Liekan v1.2.0，build 1.2.0，MIT）
- **承接项目**：`D:\Mirofish\GEO`（MTO 平台；FastAPI + SQLAlchemy 2.0 + PostgreSQL + Vue 3）
- **执行日期**：2026-11-07
- **基线提交**：`c176d6c`

---

## 一、前置假设（明确声明，未擅自脑补）

| 编号 | 假设 | 依据 |
|---|---|---|
| A1 | 「当前正在开发的项目」＝ `D:\Mirofish\GEO` | 本会话连续 4 轮操作对象，且为 origin/gitee/gitcode/cnb 四个远端的同一仓库 |
| A2 | 「独立模块」＝ 项目内新建 `backend/app/geoinflow_adapter/`，归集全部引入资产；业务接入另走现有 API/模型层 | 需求原文「增设一个独立模块，专门归集和整理这些引入内容」 |
| A3 | 本次**不推送远端** | 本次需求未授权对外发布；仅在本地提交，四平台同步待另行授权 |
| A4 | 对既有文件仅做**增量追加**，不覆盖、不重构 | 需求「保持原有功能与代码风格一致」 |

---

## 二、借鉴点评估与取舍说明

### 2.1 动工前：现成方案核验（≥2 个候选）

按用户规则先检索 GitHub / 官方文档，比较候选：

| 候选 | 类型 | 关键能力 | 判定 |
|---|---|---|---|
| **GEOInflow（本次参考）** | 自托管 Next.js 16 + Prisma 7 + PostgreSQL + Redis + pg-boss | 官方范围核验、证据归档、冻结 GEO Weight 策略、证据缺口显式化、零假数据纪律 | ✅ **选为主要借鉴源**：唯一同时具备「MIT 许可 + 可核验证据链 + 冻结量化策略」 |
| `SpeyTech/crawler-log-analyser` | Python CLI，v1.10.2 | nginx 日志解析、爬虫分类、JSON 输出 | ❌ **AGPL-3.0**，与本仓库 MIT 分发存在许可冲突 |
| `Auriti-Labs/geo-optimizer-skill` | Python，GEO Logs | UA 匹配 27 个 bot、日志分析 | ❌ 仅 UA 匹配，**不能证明请求来源** |
| `SEO-max-tech/log-file-analyzer` | Streamlit | UA 分类 + 可选 DNS 核验、地理定位 | ❌ 独立应用，无证据链与冻结策略 |
| `waseemnasir2k26/aeo-crawl-radar` | Python CLI + SQLite | sitemap-gap（哪些页面从未被抓取） | ⚠️ 仅作**覆盖率算法思路旁证**，未引入代码 |
| GeoLook | Python，本仓库已引入 | 站点审计 / 采样 / 工单闭环 | ⚠️ 已是本仓库 GEO 引擎内核，**重复，不再引入** |

> 检索来源：GitHub `ai-crawlers` topic、AI-search-tools 开源替代清单、上游 README/CONTRIBUTING。
> 以上为 2026-11-07 检索所得，**未逐一克隆验证其运行时行为**，仅依据其公开文档与许可声明判断。

### 2.2 三个整合路径的取舍

| 路径 | 做法 | 评估 |
|---|---|---|
| **A** 直接移植上游源码 | 引入 Next.js/Prisma 子服务 | ❌ 与现有 FastAPI/SQLAlchemy/Vue3 形成双栈，运维与数据割裂；`MonitorSnapshot` / `GeoTask` 功能重复 |
| **B** 抽取语言无关设计资产，Python 重写并集中归集 | 身份目录结构 / 证据状态机 / 冻结策略 / 覆盖率算法 / 零假数据纪律 → `geoinflow_adapter/`，经既有 `main.py` + `models` 接入 | ✅ **采用**：零新依赖、不改动既有业务逻辑、可验证、引入物集中 |
| **C** 仅产出借鉴文档 | 不改代码 | ❌ 不满足「实际整合」 |

### 2.3 采纳清单（补足短板）

| # | 借鉴点 | 上游依据 | 补足的本仓库短板 | 落地文件 |
|---|---|---|---|---|
| 1 | **UA 声明 ≠ 身份确认**；声明 / 官方范围 / DNS 边缘证据独立存储 | README.md「A User-Agent claim alone is insufficient to confirm a source」；`docs/traffic-quality.md` | 本仓库无身份核验概念，诊断数据为合成值 | `evidence.py` |
| 2 | **七态证据状态机**：`verified / observed / estimated / unknown / missing_input / unsupported / proved_zero` | `docs/traffic-quality.md` 四类状态；`docs/geo-weight.md` 缺失输入返回 null | 缺失值被伪装成 0 / 随机值 | `evidence.py`、`quality.py` |
| 3 | **观测 ≠ 收录 / 训练 / 引用 / 排名 / 获客** | README.md「Crawl logs establish observed access. Indexing, model training, answer citations… each require their own evidence」 | MTO「机器信任＝可核验证据链」缺显式边界 | `evidence.py`、`contracts.py` |
| 4 | **AI 爬虫身份目录**：稳定 ID / 厂商 / 用途 / AI 资格 / 官方范围来源 | `docs/crawler-directory.md`、`docs/crawler-recognition.md` | 无 AI 爬虫身份体系 | `catalog_data.json`、`catalog.py` |
| 5 | **冻结量化策略**：公式、固定档位、策略哈希、证据门控 | `docs/geo-weight.md`（`geo-weight-v2.1-bands-evidence-beta`） | `trust_score` 为实验性黑盒分，缺可解释口径 | `policy.py` |
| 6 | **内容覆盖率 / AI 盲点**：清单 vs 观测、精确路径匹配 | README「content inventory / AI blind spots」 | 无页面级爬取覆盖分析 | `coverage.py` |
| 7 | **零假数据纪律**：演示数据显式标注、状态不折叠 | `AGENTS.md` 第 11 条「No fake production analytics」 | `services/mock_data.py`、`diagnosis_routes.py` 使用 `random` | `quality.py`（**不改既有模块**） |
| 8 | **统一契约层** | `src/lib/liekan/contracts` 分层约定 | 各端点字段口径不统一 | `contracts.py` |
| 9 | **独立归集模块** | 上游「产品页 / 契约 / 上游适配器分层」组织方式 | 借鉴资产若散落会难以审计 | `geoinflow_adapter/` 整个目录 |

### 2.4 明确不引入（避免重复与冲突）

| 上游能力 | 不引入原因 |
|---|---|
| Next.js 16 / Prisma 7 / TypeScript 全栈、Docker Compose、pg-boss、ClickHouse、rrweb | 与本仓库技术栈不同，引入即双栈 |
| **官方 IP 段 `config/liekan/bot-ranges.json`** | 时效性运行数据，需每小时抓取 + 版本归档 + 人工复核；本项目**未引入、未核验**。目录仅保留 `official_range_url` 与 `range_status=not_imported`，**不据此认定任何请求来源** |
| Umami 浏览器跟踪脚本 | 与既有 `MonitorSnapshot` 采集语义重复，且属不同采集栈 |
| Cloudflare / robots 远端写控制 | 对外写操作，未获授权；需独立 Zone 凭据 |
| AI 对话与模型连接 | 与既有 `llm_client.py` / `rag_kb.py` 重复 |
| 上游 28 个增量 Prisma 迁移、`liekan:upstream:*` 同步脚本 | 绑定 Prisma 迁移体系；本仓库为 SQLAlchemy `create_all`，不可直接套用 |
| 全量 i18n / 地理库 / ZIP 导出 | 超出本次范围；仓库已建立中英 README 双语约定 |
| Kimi / Tencent Hunyuan(HySpider) / ByteDance / Meta 身份条目 | 上游 README 与 geo-weight.md 提及，但**未取得其明确的 HTTP 名称/用途表格行**；按零幻觉原则不编造，标记「待核验」 |

### 2.5 兼容性核查结论

核查现有 18 张表 / 11 个 API 模块 / 13 个 service 文件后确认：
- **无** 爬虫身份、证据状态、覆盖率相关实现 → 不构成重复；
- 既有 `geo_monitor_snapshots`（AI 平台提及率聚合快照）、`geo_metric_snapshots`（指标时序）与新表语义正交；
- 新 API 前缀 `/api/v2/mto/evidence` 与 `/api/v2/geolook`、`/api/v2/trend`、`/api/v2/geo/monitor` 无重叠；
- 新增代码仅用 Python 标准库 + 仓库既有 SQLAlchemy/FastAPI/Pydantic，**未新增任何第三方依赖**；
- **未改动** `services/mock_data.py`、`diagnosis_routes.py`、`monitor_routes.py` 等既有业务文件。

---

## 三、实际整合结果

### 3.1 独立归集模块 `backend/app/geoinflow_adapter/`

| 文件 | 职责 |
|---|---|
| `__init__.py` | 模块说明、来源/许可声明、借鉴边界、对外导出 |
| `README.md` | 归集说明：来源与合规、上游文档映射表、取舍记录、兼容边界、用法、已知限制 |
| `catalog_data.json` | 37 条身份目录（结构源自 `crawler-directory.md`），含 `range_status: not_imported` 与「待核验」说明 |
| `catalog.py` | 目录加载 / 厂商·用途·AI 资格筛选 / UA 声明候选解析（**不声称核验**） |
| `evidence.py` | 七态状态机 `classify_identity()`、`evidence_gap_report()`、观测边界常量 |
| `policy.py` | 冻结策略 `mto-evidence-weight-v1`：公式、10 档区间、策略哈希、证据门控 |
| `coverage.py` | 内容清单 vs 观测 → 覆盖率、AI 盲点；缺清单返回 `missing_input` |
| `quality.py` | 缺失不折叠为 0、演示数据标注、零假数据纪律声明 |
| `contracts.py` | 统一响应信封：`data + evidence_state + policy_version + limitations` |

### 3.2 业务接入层

| 文件 | 内容 |
|---|---|
| `backend/app/models/geoinflow_evidence.py` | 新表 `geo_crawler_observations`（19 张表）：单条爬取观测 + 三类独立核验证据 + 归档范围版本；**不存原始 IP / 完整 UA** |
| `backend/app/api/geoinflow_routes.py` | 前缀 `/api/v2/mto/evidence`，5 个端点：`GET /catalog`、`GET /policy`、`POST /observation`、`GET /observations`、`GET /report` |
| `backend/app/main.py` | 增量追加 1 行 import + 1 行 `include_router` |
| `backend/app/models/__init__.py` | 增量追加 1 行模型注册（使 `init_db()` 自动建表） |

### 3.3 文档与合规

- `THIRD_PARTY_NOTICES.md`：新增「2. GEOInflow」条目（MIT、双版权行、借鉴/未引入清单、合规说明）。
- `README.md` / `README.en.md`：系统架构图 11→12 模块、项目结构 18→19 表、新增归集模块/新路由/新表说明、核心特性新增「MTO 证据充分性」、API 文档新增端点组。
- `llms.txt`：Resources 增加归集模块与证据 API 入口。

### 3.4 关键口径（可复现）

```
身份判定：仅 UA → unknown；UA + 官方范围 + 归档快照版本 → verified；
          有可信入口/DNS 证据但核验链不全 → observed；无输入 → missing_input
冻结公式：W = 10·E_search + 7·E_user + 3·E_training（30 个完整日历日，内容 GET 200/304 去重）
档位    ：1–10 固定区间；确证的观测零单独为 level 0；缺失输入返回 null（不是 0）
覆盖率  ：清单 ∩ 观测 / 清单，精确路径匹配（/cases 与 /cases/ 不同）
```

---

## 四、变更清单

**新增文件（12 个）**

| 路径 | 说明 |
|---|---|
| `backend/app/geoinflow_adapter/__init__.py` | 模块入口 |
| `backend/app/geoinflow_adapter/README.md` | 归集说明 |
| `backend/app/geoinflow_adapter/catalog_data.json` | 身份目录 |
| `backend/app/geoinflow_adapter/catalog.py` | 目录查询 |
| `backend/app/geoinflow_adapter/evidence.py` | 证据状态机 |
| `backend/app/geoinflow_adapter/policy.py` | 冻结策略 |
| `backend/app/geoinflow_adapter/coverage.py` | 覆盖率与盲点 |
| `backend/app/geoinflow_adapter/quality.py` | 零假数据纪律 |
| `backend/app/geoinflow_adapter/contracts.py` | 统一响应契约 |
| `backend/app/api/geoinflow_routes.py` | 5 个证据端点 |
| `backend/app/models/geoinflow_evidence.py` | `geo_crawler_observations` 表 |
| `docs/geoinflow-借鉴与整合说明.md` | 本报告 |

**修改文件（6 个，均为增量追加，未覆盖原有内容）**

| 路径 | 增量 |
|---|---|
| `backend/app/main.py` | +2 行（import + include_router） |
| `backend/app/models/__init__.py` | +3 行（模型注册 + 注释） |
| `README.md` | 架构图 / 项目结构 / 核心特性 / API 四处 |
| `README.en.md` | 同上四处（英文同步） |
| `THIRD_PARTY_NOTICES.md` | +34 行 GEOInflow 合规条目 |
| `llms.txt` | +2 行入口链接 |

**未改动**：所有既有业务模块、`services/mock_data.py`、`diagnosis_routes.py`、`monitor_routes.py`、`trend_routes.py`、`trend_advisor.py`。
**数据库**：新增 `geo_crawler_observations` 一张表（18 → 19），由 `init_db()` 幂等创建。

---

## 五、验证结果

### 5.1 静态验证（`backend\_verify_geoinflow.py`，49 项断言）

| 类别 | 结果 |
|---|---|
| 模块导入 / 表注册（19 张，含新表；旧表回归） | 4/4 PASS |
| 路由注册（5 个新端点 + 3 个原有端点回归） | 8/8 PASS |
| 冻结策略：上游算例 `3000/400/8000 → W=56,800 → level 6`、10 个档位下界、缺失/不完整/确证零、策略哈希 | 16/16 PASS |
| 证据状态机：unknown / verified / missing_input / observed、5 类缺口 | 6/6 PASS |
| 覆盖率：缺清单、1/3 覆盖率、盲点、尾部斜线精确匹配 | 4/4 PASS |
| 身份目录：37 条、范围未引入、稳定 ID、UA 候选、AI 资格筛选 | 5/5 PASS |
| 统一契约 / 零假数据 | 3/3 PASS |
| **合计** | **首轮 48/49 → 修复后 49/49 PASS** |

**首轮 FAIL 及修复（如实记录）**：`可信入口但无核验 → observed` 一项失败。根因为 `classify_identity()` 的 UNKNOWN 分支未把 `trusted_ingress` 计入独立观测证据，导致有可信入口但核验链不完整被误判为 `unknown`。修正为 `has_independent_evidence = official_range_verified or dns_or_edge_evidence or trusted_ingress`，仅为「无任何独立证据」才返回 UNKNOWN。复跑 49/49 PASS。**未修改测试期望以迁就实现。**

### 5.2 HTTP 端到端联调（`uvicorn 127.0.0.1:5006`）

| 请求 | 结果 |
|---|---|
| `GET /api/health` | 200 `ok` |
| `GET /api/v2/trend/snapshots`（原有功能回归） | 200，既有快照数据未受影响 |
| `GET /evidence/catalog` | 200，37 条，`range_imported=false` |
| `GET /evidence/policy` | 200，策略 ID `mto-evidence-weight-v1`，公式一致 |
| `POST /evidence/observation`（仅 UA） | 200 → `unknown`，`can_claim_identity=false` ✅ |
| `POST /evidence/observation`（完整核验链） | 200 → `verified`，`can_claim_identity=true` ✅ |
| `GET /evidence/observations` | 200，2 条记录已落库 |
| `GET /evidence/report`（清单 `/a,/b,/c` + 上游算例） | 200，覆盖率 `0.6667`、盲点 `['/c']`、权重 `level=6 / W=56800`（与上游文档算例一致） |
| `GET /evidence/report`（不提供清单） | 200，覆盖率 `missing_input / None`、权重 `None / missing_input` —— **未把缺失折叠成 0** ✅ |

`report` 的 `evidence_state` 恒为 `missing_input`，原因是本项目**未接入 AI 引荐会话数据**（`has_referral_sessions=False` 如实标注），缺口在响应中逐条列出。这是预期的证据门控行为，不是故障。

### 5.3 清理

- 两个临时验证脚本已删除；
- 联调服务（5006）已停止，未遗留常驻进程。

---

## 六、已知限制与未执行事项

1. **官方 IP 范围未引入**：所有身份核验结果最高只能到 `observed`，除非调用方自行提供 `official_range_verified + range_snapshot_version`（此时为调用方声明，本项目不核验其真实性）。目录中的 `official_range_url` 仅为来源记录，未验证其当前有效性。
2. **量化系数为上游 Beta 参数**，未经跨行业校准；本仓库未用真实生产数据验证。
3. **未接入真实服务器/CDN 日志采集**：当前观测数据须经 `POST /observation` 手工或外部集成上报。
4. **既有合成数据模块保持原状**：零假数据纪律仅约束新增模块及其 API，未按需求改动 `mock_data.py` / `diagnosis_routes.py`。
5. **未推送到 4 个远端**（origin / gitee / gitcode / cnb）：本次需求未授权对外发布；本地提交后待另行授权同步。
6. 上游文档中的 `Kimi`、`HySpider`、`Bytespider` 等身份因缺少明确的 HTTP 名称/用途表格行，未编造收录。
