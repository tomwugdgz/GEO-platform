# GeoLook 0.2.0 → 你的 GEO 平台 · 移植对照表（动工前确认稿）

> 依据：`D:\download\geolook-0.2.0\geolook-0.2.0`（参考程序）
> 目标：`d:\Mirofish\GEO`（你的 GEO 平台）
> 决策（已由 Tom 确认）：**Windows 兼容层 ✔ 已加载 · 架构=方案②（算法移植，保留你的架构）· 保留你所有页面 + 把 GeoLook 全部页面插到合适位置 · 底层算法配置全部以 GeoLook 为准**

---

## 0. 阶段一已完成：Windows 兼容层（已实测跑通）

### 0.1 阻断问题
`scripts/geolib.py:8` → `import fcntl`。`fcntl` 是 POSIX 专有模块，Windows CPython 不提供。
实测报错：`缺少依赖：fcntl。`（任何命令都无法启动）

### 0.2 已实施的兼容层（3 个文件改动 + 1 个新文件）

| 文件 | 改动 | 说明 |
|---|---|---|
| `scripts/_win_fcntl.py` | **新增**（~150 行） | `msvcrt.locking` 实现 `fcntl.flock`；三级降级：msvcrt 文件锁 → 进程内线程锁 → no-op |
| `scripts/geolib.py` | 改 import + 控制台 UTF-8 | `try: import fcntl / except: from _win_fcntl import fcntl_shim`；`stdout/stderr.reconfigure(utf-8)` 防中文控制台 GBK 崩溃 |
| `scripts/jobs.py` | 新增 `_kill_tree()` / `_is_alive()` | Windows 无 `killpg`/`getpgid`；改用 `taskkill /T /F` 杀进程树 + `OpenProcess`/`GetExitCodeProcess` 探活 |
| `scripts/dashboard.py` | 新增 `_harden_env_permissions()` | Windows chmod 无 POSIX 语义；改用 `icacls /inheritance:r` 收紧 `.env` ACL |
| `tests/test_jobs.py`、`tests/test_model_config.py` | 平台分支断言 | 原断言硬编码 POSIX 行为，加 `os.name == "nt"` 分支 |

### 0.3 实测结果（全部在你的 Windows 上真实执行）

| 验证项 | 结果 |
|---|---|
| 依赖安装 | `requests 2.34.2` / `bs4 4.15.0` / `lxml` ✔（独立 venv） |
| 单元测试 | **116 passed / 0 failed**（修复前 114 passed / 2 failed） |
| `init` 建项目 | ✔ 生成 `work/<slug>/geo.json` |
| `crawl` 抓取 | ✔ python.org 6/6 页 200 |
| `audit` 六维体检 | ✔ 均分 35.6，4 层依赖链 + block_gap 正常输出 |
| `plan` 工单 | ✔ 生成 13 条工单 |
| `blueprint` 蓝图 | ✔ 0/8 渠道覆盖 |
| `generate` 资产 | ✔ 生成 12 项资产 |
| `report` 报告 | ✔ 生成 `report.html` |
| `deliverables` 三份交付物 | ✔ |
| `deliver` 交付包 | ✔ |
| `ui` 看板服务 | ✔ HTTP 200，端口 8770 |

**结论：GeoLook 0.2.0 算法内核在 Windows 上已完整跑通。**

---

## 1. GeoLook 模块清单（18 个核心模块 · ~7,300 行）

| 模块 | 行数 | 职责 | 你现有对应物 | 移植动作 |
|---|---|---|---|---|
| `geolib.py` | 430 | 路径/配置/HTTP/**robots RFC9309 解析**/正文抽取/语言判定 | 无 | **新增**（基础设施层） |
| `audit.py` | 490 | 六维评分 + 四层依赖链 + block_gap | `diagnosis_routes.py`(506行) | **替换算法** |
| `sample.py` | 914 | 17 引擎采样 / 人工采样表 / 样本库 | `monitor_routes.py`(385行) | **替换 + 扩引擎** |
| `analytics.py` | 506 | 指标口径层（提及率/排名/引用份额） | 部分在 `monitor_routes.py` | **替换口径** |
| `tasks.py` | 462 | 工单系统（P0/P1/P2 + 风险等级 + 验收标准） | 无 | **新增** |
| `generate.py` | 538 | 资产生成（llms.txt/JSON-LD/片段/大纲/归因）+ 编造风险 lint | `content_routes.py`(256行) | **替换 + 扩充** |
| `report.py` | 411 | 报告（Markdown + 自包含 HTML + 环比 delta） | 无 | **新增** |
| `deliverables.py` | 339 | 三份正式交付物（诊断/优化/执行） | 无 | **新增** |
| `deliver.py` | 392 | 客户交付包打包 | 无 | **新增** |
| `crawl.py` | 327 | 站点抓取（robots/sitemap/llms.txt + 正文） | 无 | **新增** |
| `bootstrap.py` | 334 | 从官网自动推导品牌事实/竞品/问题库 | 部分在 `intent_routes.py` | **替换** |
| `publish.py` | 352 | 发布渠道（GitHub/WP/微信/Webhook/X/Reddit） | 无 | **新增** |
| `expand.py` | 299 | 拓词（百度下拉 + Google suggest） | `intent_routes.py`(231行) | **替换** |
| `verify.py` | 287 | 验收闭环（重抓 + 自动判定工单） | 无 | **新增** |
| `blueprint.py` | 284 | 建设蓝图（19 渠道加权） | 无 | **新增** |
| `jobs.py` | 244 | 后台任务（子进程 + 实时日志） | `tasks/` | **替换** |
| `dashboard.py` | 708 | stdlib http.server + 30+ API | FastAPI（你的） | **只移植算法，不移植服务** |
| `benchmark.py` | 100 | 行业大盘对照 | 无 | **新增** |
| `ui.html` | 298KB | 13 页面单页前端 | Vue 3 SPA（你的） | **只参考结构，不替换你的 UI** |

**参考数据**（`references/`）：`method.md`（方法论 + 实证数据）、`cn-platforms.md`、`global-platforms.md`、`cn-source-ranking.md`（19 渠道权重）、`content-patterns.md`、`attribution.md`、`sources.md` — **全部需要纳入知识库**。

---

## 2. 核心算法：必须 1:1 复刻的部分

### 2.1 六维评分权重（总分 100）— `audit.py:score_page`

| 维度 | 满分 | 评分细则 |
|---|---|---|
| **可抓取性** | 15 | status=200→7分；非2xx/3xx→3分；meta/X-Robots noindex→0分；canonical存在→2分；字数≥120→3分 |
| **内容长度** | 15 | band 分段：≥1500词→100%；≥1000→85%；≥600→60%；≥300→35%；≥120→15% |
| **结构规范** | 20 | H1唯一→4分；H2数量(≥8→6分)；段落数(≥40→5分)；列表密度(≥0.35→5分) |
| **可抽取块** | 25 | 定义6 + 数字事实6 + 对比5 + 操作步骤5 + FAQ3（**GEO 核心杠杆**）|
| **权威信号** | 15 | 日期4 + 作者2 + 外链4 + JSON-LD类型5 |
| **对题性** | 10 | 目标问题词覆盖率 band（≥40%→100%）；**r=0.432 最强预测因子** |

另含 **段落级可引（quotable）** 判定：段落 ≥60 词 **且** 含 数字/定义/步骤 之一。

**评级**：A≥80 · B≥65 · C≥45 · D<45

### 2.2 四层依赖链（Access → Orientation → Understanding → Quotability）
每层依赖上层，Access 失败则下游全部不可见，**修复顺序由系统计算**。

### 2.3 robots.txt 解析（RFC 9309 语义）
上游注释明确点出三个最易误判处，必须保留：
1. 多个 `User-agent` 行**共享同一组规则**
2. 具体 UA 组存在时**通配符组整组失效**（specificity 优先于顺序）
3. 规则按**最长路径匹配**定胜负，同长时 **Allow 胜出**；支持 `*` 与 `$`

### 2.4 WAF/CDN 差异探测
用**真实 AI 爬虫 UA** 探测：robots 可能放行 GPTBot 但 CDN 返 403 —— 浏览器看不出来。

### 2.5 实证基准（`references/method.md`）
- 高影响力页面均 **1,943 词**，低分仅 170 词（**11.4×**）
- 数字 **+61.6%** / 定义 **+57.3%** / 对比 **+55.3%** / how-to **+41.2%** 引用概率提升
- 纯 Q&A 排版 **−5.7%**
- 品牌自有站点仅占中文引用 **1.37%**
- 语料规模：602 prompts / 21,143 citations / 187,818 去重中文引用

---

## 3. 页面映射方案（你的页面全保留 + GeoLook 页面插入）

### 3.1 你的现有页面（13 个，全部保留）
`Story` / `Workflow` / `Dashboard` / `IntentMap` / `KnowledgeEditor` / `ContentList` / `MonitorBoard` / `Gallery` / `Keywords` / `Social` / `Writing` / `Distribution` / `Monitoring`

### 3.2 GeoLook 13 个页面 → 插入位置

| GeoLook 页面 | 插入到你的 | 路由 | 说明 |
|---|---|---|---|
| Overview | **Dashboard**（增强） | `/dashboard` | 首页概览 + 健康分 |
| Engines | **Monitoring**（增强） | `/monitoring` | 17 引擎性能 |
| Competitors | **BrandDiagnosis 域** | `/geo/competitors` | 竞品表 + 引用份额 |
| Questions | **QuestionCreation**（增强） | `/intent` | 7 类问题库 + 意图组卡 |
| SiteAudit | **新增** | `/geo/siteaudit` | 六维体检 + 四层链 |
| Gaps | **新增** | `/geo/gaps` | 缺口诊断 |
| Channels | **新增** | `/geo/channels` | 19 渠道地图 |
| Facts | **KnowledgeEditor**（增强） | `/knowledge` | 品牌事实库（唯一真源）|
| Plan | **新增** | `/geo/plan` | 工单（P0/P1/P2 + 风险）|
| Workbench | **Writing**（增强） | `/writing` | 内容工作台 + lint |
| Assets | **Distribution**（增强） | `/distribution` | llms.txt/JSON-LD/片段 |
| Verify | **新增** | `/geo/verify` | 验收 + 环比 |
| Settings | **新增** | `/settings` | 引擎 Key / 模型 / 发布渠道 |

---

## 4. 三个候选实现路径（请你选一个）

| 方案 | 做法 | 优势 | 劣势 | 工期估算 |
|---|---|---|---|---|
| **A. 原生模块 + 适配层**（推荐） | 把 GeoLook `scripts/` 作为 `backend/geolook/` 内嵌，FastAPI 写一层适配器调用 | 算法**零改写**，GeoLook 升级可 `git pull` 跟进；风险最低；你现有的 FastAPI 多租户/LangGraph 全保留 | 需要一层 `work/` ↔ PostgreSQL 的映射（数据双写） | 中等 |
| **B. 重写为 FastAPI 原生** | 把 18 个模块逐个改写成 FastAPI service + SQLAlchemy model | 架构统一，无文件存储 | 7,300 行改写，**偏离上游就再也合不回来**；回归风险高 | 大 |
| **C. 子进程桥接** | 你的 FastAPI 以 subprocess 调 `geo.py` CLI，解析 JSON 输出 | 隔离最彻底，几乎零改动 | 无事务、无并发控制、日志割裂；多租户需手工传参 | 小但技术债大 |

**我的建议：方案 A。** 理由：
1. 你的硬约束是"底层逻辑算法配置**全部按照 GeoLook**"——只有方案 A 做到**零改写**（B 会引入改写偏差，C 会引入解析偏差）
2. 你的软约束是"界面配置等可以优化为原来的"——方案 A 保留你的 Vue + FastAPI 全部架构
3. GeoLook 是纯函数式算法模块（输入 JSON → 输出 JSON），**天然适合内嵌**，不需要改写成 ORM
4. 上游仍在迭代（0.2.0），方案 A 可无损跟进升级

---

## 5. 需要你确认的 4 个问题

1. **选哪个方案？** A（推荐）/ B / C
2. **数据存储怎么放？**
   - (a) GeoLook 的 `work/<slug>/` 文件存储**原样保留**，PostgreSQL 只存多租户元数据（**推荐**，零改写）
   - (b) 全部迁进 PostgreSQL（需改写 GeoLook 存储层，违背"零改写"）
   - (c) 双写（复杂度最高）
3. **17 个引擎 Key 你有哪些？** 影响"能否自动采样"：
   - 国内：智谱 GLM / 火山 ARK(豆包) / DeepSeek / 月之暗面 Kimi / MiniMax
   - 海外：Gemini / OpenAI / Anthropic / xAI / Perplexity
   - 可只填部分；无 Key 走人工采样表（GeoLook 原生支持，不影响跑通）
4. **移植范围**：全部 18 个模块，还是先做 MVP（crawl + audit + plan + generate + report，即"诊断→方案→资产"闭环）？

---

## 6. 我做的假设（明确告知，未脑补）

- 假设"我这个系统"= `d:\Mirofish\GEO`（FastAPI 端口 5006 + `bmn-frontend` Vue3）
- 假设"配置"指 GeoLook 的 `.env` 引擎 Key、`geo.json` 项目配置、模型覆盖项
- 假设"输出/输入"指 GeoLook 的 `work/<slug>/` 目录结构（evidence/samples/metrics/reports/history/content/assets/deliverables）
- **未假设**存储方案与方案选型 —— 这两项决定架构，必须你定
