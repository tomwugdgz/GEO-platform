# GeoLook 全模块移植 — 交付说明

## 一、这次做了什么

把 GeoLook 引擎的 **18 个模块**完整接入 GEO 平台（前端 8 个页面 + 后端 32 个接口），
并做了真实数据端到端跑通验证，而不是只做接口对通。

### 后端：`backend/app/api/geolook_routes.py`（35 个路径 / 45 个方法）

| 类别 | 接口 |
|---|---|
| 项目 | `GET /projects`、`POST /projects/init`、`GET /projects/{slug}/status`、`GET /projects/{slug}/overview` |
| 采集体检 | `POST crawl`、`POST audit`、`GET audit-data`、`GET siteaudit` |
| 采样 | `POST sample`、`GET samples` |
| 工单 | `POST plan`、`GET tasks`、`GET gaps` |
| 蓝图渠道 | `POST blueprint`、`GET blueprint`、`GET channels` |
| 资产内容 | `POST generate`、`GET assets`、`POST expand`、`GET questions`、`GET/PUT facts` |
| 竞品 | `GET/POST/PUT competitors` |
| 报告交付 | `POST report`、`GET reports`、`POST deliverables`、`GET deliverables`、`POST deliver` |
| 验收 | `POST verify`、`GET verify` |
| 引擎 | `GET/PUT engines`（10 个 API 引擎 + 7 个人工渠道） |
| 大盘 | `GET benchmark`、`GET analytics` |
| 编排 | `POST bootstrap`、`POST full-cycle`、`POST publish`、`GET/PUT settings` |
| 原始产物 | `GET work`（零改写索引）、`GET work/file`（单文件读取，带越界防护） |

### 前端：新增 8 个页面 + 1 个增强

| 页面 | 路由 | 迁移来源 |
|---|---|---|
| GEO 诊断（项目列表 + 模块直达） | `/geolook` | 增强 |
| 站点审计 | `/geo/siteaudit` | SiteAudit |
| 工单管理 | `/geo/plan` | Plan |
| 竞品分析 | `/geo/competitors` | Competitors |
| 渠道地图 | `/geo/channels` | 渠道/蓝图 |
| 缺口诊断 | `/geo/gaps` | 缺口诊断 |
| 验收闭环 | `/geo/verify` | Verify |
| 引擎配置 | `/settings` | Settings |
| 知识库（事实库编辑器） | `/knowledge` | Facts（增强，原为占位页） |

侧边栏新增「GeoLook 引擎」分组，并在分组顶部显示**当前项目**标识，
所有子页面自动锁定该项目（路由参数 → 本地记忆 → 项目列表第一个）。

## 二、关键决策

1. **存储：`work/<slug>/` 原样保留，零改写**（推荐方案）。
   GeoLook 的产物（geo.json / audit.json / tasks.json / blueprint.json / verify/*.json /
   metrics/ / reports/ / assets/）一律不动，API 只做只读索引与投影。
   另开 `GET /work` + `GET /work/file` 两个只读接口供核对与排查。

2. **引擎 Key：10 个全保留，无 Key 走人工采样表**。
   注册表不写死在 API 里，而是从 `geolook/sample.py` 的 `PROVIDERS` 实时导出（5 分钟缓存），
   避免与上游漂移；导出失败退回静态副本，接口永不 500。
   另列出 7 个纯人工采样渠道（纳米AI、百度AI、豆包App、ChatGPT网页版、Claude网页版、Google AIO、秘塔）。

3. **空态优先，不抛 404**。数据未生成时返回 `{exists: false, ...空数组}` + 引导文案，
   前端渲染友好空态而不是整页报错。只有「项目不存在」才 404。

4. **验收结果双向兼容**：原始报告字段（`results` / `summary` / `changed`）原样透出，
   另投影前端统一口径（`total_tasks` / `passed_tasks` / `details[].status`）。

## 三、顺手修掉的历史问题（与本次移植无关，但会让页面不可用）

| 问题 | 根因 | 处理 |
|---|---|---|
| 7 个新页面/原有页面在 `router/index.js` 里的路由**完全不生效** | 真正的路由内联写在 `main.js`，`router/index.js` 是死文件 | `router/index.js` 改为唯一真源（全懒加载），`main.js` 只挂载；新增页面才能访问 |
| 所有页面 `import api from '@/api/axios'` 报模块不存在 | `src/api/axios.js` 从未创建 | 新建封装（统一超时 + 中文错误文案） |
| 自媒体授权 / AI 写作 / 分发管理 / 监测看板**整页白屏** | 用了 `<el-table>` 却从未 `app.use(ElementPlus)`，插槽 `{ row }` 拿到 undefined | `main.js` 全局注册 Element Plus（含中文 locale）；4 个页面恢复渲染 |
| 首次访问时多页面 422 / 500、列表空白 | 新访客 localStorage 无 `tenant_id`，页面把空租户传给后端 | 启动时自动引导默认租户/品牌；`api/business.js`、`api/geo.js` 统一补 `tenant_id`、清洗 `null`/`undefined` 参数、修复 `/tenants/undefined/brands` |
| 监测看板崩溃（`appearance_rate` of undefined） | mock 返回裸对象、字段名与页面不一致 | mock 改为 `{ data: { appearance_rate, ... } }` |
| 新页面标题在深色主题下不可读 | 页面沿用了浅色卡片配色，文字继承全局浅色 | 统一到应用深色像素主题（`reskin_geolook.py`，102+13 处等价替换） |
| 缺口诊断只有「缺口 1/2/3」没有内容 | 后端投影字段与页面不一致 | 补 `title/description/priority/suggestion`，保留原始字段 |

## 四、验证方式与结果

**真实浏览器（Chromium + Playwright）逐页跑，不是静态检查。**

- 全站 **25 个页面**：25 个零控制台错误、零失败请求
- 真实数据端到端：`crawl → audit → plan → blueprint → competitors → verify` 全流程跑通
  - 站点审计：25 页、均分 36.8、等级分布 A0/B0/C9/D16、四层依赖链、6 条站点问题
  - 工单管理：16 条工单，含依据/动作/验收标准（自动 or 人工判定）
  - 缺口诊断：25 个内容缺口 + 11 个模块缺口，逐条 issue 明细
  - 渠道地图：蓝图生成后 11 个渠道（P0/P1 优先级 + 建设理由）
  - 验收闭环：16 条判定（通过 0 / 未达标 12 / 待人工 4）
  - 引擎配置：10 个引擎全列出，含模型名与「走人工采样表」提示
- 截图存于 `screenshots/`（9 张）

验证脚本（可复跑）：
```bash
# 全站巡检（含控制台错误与失败请求）
CHROME_PATH=<chromium> NODE_PATH=<playwright 模块> node bmn-frontend/_verify_pages.cjs
# 关键页面截图
CHROME_PATH=<chromium> NODE_PATH=<playwright 模块> node bmn-frontend/_shoot.cjs
```

## 五、启动方式

```bash
# 后端（端口 5006）
cd d:/Mirofish/GEO/backend && ./venv/Scripts/python.exe run.py
# 前端（开发，端口 5173，/api 代理到 5006）
cd d:/Mirofish/GEO/bmn-frontend && npm run dev
# 生产构建
cd d:/Mirofish/GEO/bmn-frontend && npm run build
```

## 六、已知事项 / 后续建议

1. **主包体积 1.1MB**（gzip 370KB）——Element Plus 全量引入所致。
   如在意首屏，可改按需引入（`unplugin-vue-components`）或用 `manualChunks` 拆分。
2. **竞品分析目前只有手工添加 + 自动推导两条路径**：页面上「添加竞品」可用；
   想批量自动推导可先跑 `POST /projects/{slug}/bootstrap`（会顺带生成品牌事实与问题库）。
3. **`GET analytics` / `GET benchmark` 依赖采样数据**：未跑 `sample` 前只返回空态，
   建议后续把「采样」按钮也补到页面上（目前需通过接口触发）。
4. 一次性脚本 `_verify_pages.cjs` / `_verify_tenant.cjs` / `_shoot.cjs` 保留在 `bmn-frontend/`，
   作为回归验证工具；如不想入库可从 git 忽略。
