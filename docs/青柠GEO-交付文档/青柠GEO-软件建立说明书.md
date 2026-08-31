# 青柠GEO 软件建立说明书

> 本说明书面向负责部署与上线青柠GEO 系统的技术人员，覆盖环境准备、源码部署、初始化配置、扩展安装、验收检查与运维建议全流程。

| 项目 | 说明 |
| --- | --- |
| 文档名称 | 青柠GEO 软件建立说明书 |
| 适用版本 | V1.4（2026-08-31） |
| 适用对象 | 实施/运维工程师、交付 PM、代理商技术人员 |
| 技术架构 | Vue 3（前端） + ThinkPHP 8（后端） + MySQL + Redis + 向量数据库（选型见 4.7） |
| 版本体系 | 高级版 / 旗舰版 / 无限版 |
| 部署模式 | 源码部署 / 独立服务器 / 支持代理商多子站 |

> ⚠️ **说明**：本说明书中的目录结构、命令与配置为标准部署流程示例，**具体以实际交付源码包内附带的部署文档为准**；标注【待确认】的内容请对照交付包核实后补充。

> 🔧 **技术栈对齐说明（重要）**：本说明书「技术架构」一栏所述 **Vue 3 + ThinkPHP 8 + MySQL + Redis + 向量库** 为**产品参考 / 目标架构**。本开源仓库（`GEO-platform`）的**实际实现**为 **Vue 3.5（bmn-frontend）+ FastAPI（Python）+ PostgreSQL / SQLite + LangGraph + ChromaDB**，二者后端栈不同。
> - 概念模型（蒸馏词 / EEAT / llms.txt / 六层架构 / A2A）完全一致，可直接对照；
> - 实际可运行的部署步骤见本文 **附录 A：本仓库实际部署（FastAPI + PostgreSQL + ChromaDB）**；
> - 完整映射与差异说明见 **[`技术栈对齐说明.md`](./技术栈对齐说明.md)**。

---

## 1. 系统概述

### 1.1 系统简介

青柠GEO 是一套 GEO（生成式引擎优化）内容营销系统，围绕「蒸馏词 → AI 拓展问题 → 配置画像/模板 → AI 创作文章 → 多平台发布 → 收录检测 → 数据分析」工作流，提供蒸馏词管理、AI 写作（长文章 + 图文内容）、多平台发布与自动托管、提及检测（8 大 AI 平台）、数据报表等能力，支持源码独立部署与代理商 SaaS 子站模式。

### 1.2 系统角色

| 角色 | 说明 |
| --- | --- |
| 管理员 | 拥有所有权限，可管理用户、配置系统 |
| 普通用户 | 使用蒸馏词、创作、发布、检测等核心功能 |
| 代理商 | 管理多个客户，支持品牌白标定制 |
| 子客户 | 由代理商创建，使用分配的功能和配额 |

### 1.3 系统架构

```
┌──────────────────────────────────────────────────────┐
│                      用户浏览器                        │
│        （管理后台 SPA + 浏览器扩展）                     │
└────────────────────────┬─────────────────────────────┘
                         │ HTTPS
┌────────────────────────▼─────────────────────────────┐
│              Nginx（Web 服务器/反向代理）                 │
│   ┌──────────────────┐  ┌────────────────────┐       │
│   │  前端静态资源      │  │  后端 API 服务       │       │
│   │  Vue 3 构建产物   │  │  ThinkPHP 8        │       │
│   └──────────────────┘  └─────────┬──────────┘       │
└───────────────────────────────────┼──────────────────┘
                     ┌──────────────┼──────────────┐
                     │              │              │
              ┌──────▼─────┐ ┌──────▼─────┐ ┌──────▼─────┐ ┌──────▼─────┐
              │   MySQL    │ │   Redis    │ │ 向量数据库  │ │ AI 模型 API │
              │  业务数据库  │ │ 缓存/队列   │ │ Milvus 等  │ │ OpenAI 等  │
              └────────────┘ └────────────┘ └────────────┘ └────────────┘
                                       │
                              ┌────────▼─────────┐
                              │  外部平台接口      │
                              │  AI 平台检测       │
                              │  （豆包/DeepSeek/ │
                              │  文心一言 等 8 家） │
                              │  自媒体平台发布    │
                              │  （百家号/头条号等）│
                              └──────────────────┘
```

> 注：向量数据库用于知识资产链路（企业知识库 → 切片 → Embedding → 向量检索），选型为 Milvus / pgvector / Faiss 三选一，详见 4.7 节【待确认】。

### 1.4 核心模块清单

| 分组 | 模块 | 说明 |
| --- | --- | --- |
| 工作台 | 智能工作台 | AI 可见度报告（可见度/引用率/SoV/情感）、品牌事实库、GEO 周报、归因报告、核心指标卡、今日待办、智能推荐 |
| 蒸馏词 | 蒸馏词管理 | 核心蒸馏词、品牌植入词绑定、AI 拓展问题、提及率统计 |
| 创作 | AI 写作 | 长文章/图文内容、AI 创作/AI 编写/手动创作、审核流 |
| 创作 | 素材中心 | 图片素材、画像管理、创作模板、知识库 |
| 分发 | 发布任务 | 批量/定时发布、发布记录、失败重试 |
| 分发 | 自动托管 | 托管式自动执行发布任务 |
| 分发 | 媒体账号 | 百家号、头条号、知乎等平台 OAuth 授权与分组 |
| 分发 | 提及检测 | 豆包、DeepSeek、腾讯元宝、通义千问、文心一言、Kimi、智谱清言、ChatGPT 等 8 平台收录/提及检测，浏览器扩展配合，官方 API + 账号池混合模式 |
| 分析 | 竞品逆向研究 | 6 维度竞品 GEO 策略拆解（内容策略/SEO 战术/AI 可见性/关键词打法/渠道组合/创意模式），输出可攻击薄弱环节，预计 3-5 分钟/次 |
| 分析 | 多模态分析引擎 | 图像（Logo 检测/OCR/相关性评分）、视频（关键帧/Logo 追踪/竞品口播）、音频（ASR 转写/品牌识别/情感分类）分析可用，跨模态融合（BVI 指数）规划中 |
| 系统 | AI 模型配置 | 多模型接入、多 Key 轮询、Token 消耗统计 |
| 系统 | 知识资产链路 | 企业知识库 → 切片 → Embedding → 向量库（Milvus / pgvector / Faiss），支撑语义检索与创作引用 |
| 系统 | 应用中心 | 扩展能力按需启用 |
| 客户 | 客户列表 / 财务管理 | 多客户管理、充值/消费/利润统计（代理商版） |
| 客户 | 界面设置 / 代理商管理 | Logo/系统名称/品牌色白标、子站开通与管理 |

---

## 2. 运行环境要求

### 2.1 服务器配置建议

| 环境 | 最低配置 | 推荐配置 |
| --- | --- | --- |
| 测试环境 | 2 核 4G，40G 系统盘 | 2 核 8G，50G 系统盘 |
| 生产环境 | 4 核 8G，100G 系统盘 | 8 核 16G，100G+ SSD |
| 操作系统 | Ubuntu 20.04+/22.04、CentOS 7.9+/Rocky Linux 8+ | 同左 |
| 网络 | 需可访问外网（调用 AI 模型 API、各自媒体平台接口、AI 平台检测） | 建议国内服务器 + 备用出海线路（ChatGPT 检测） |

### 2.2 软件环境要求

| 软件 | 版本要求 | 用途 |
| --- | --- | --- |
| PHP | 8.0 及以上（建议 8.1/8.2） | 后端运行环境 |
| PHP 扩展 | fileinfo、openssl、pdo_mysql、redis、curl、mbstring、gd、bcmath、zip | 后端依赖 |
| Composer | 2.x | PHP 依赖管理 |
| MySQL | 5.7+（建议 8.0） | 业务数据库 |
| Redis | 5.0+ | 缓存、队列 |
| 向量数据库 | Milvus 2.x（大规模）/ pgvector（PostgreSQL 扩展）/ Faiss（离线调优、嵌入式）三选一【待确认：以交付包为准】 | 知识库 Embedding 存储与语义检索 |
| GPU（可选） | 显存 ≥ 8G（CLIP / YOLO / Whisper）；≥ 16G（Video-LLaVA） | 多模态分析私有化部署（Phase B 组件，可选；也可走公网 API） |
| Nginx | 1.18+ | Web 服务/反向代理 |
| Node.js | 16+（建议 18+） | 前端构建（仅需构建时） |
| pnpm / npm / yarn | 最新稳定版 | 前端包管理 |

---

## 3. 部署前准备清单

部署启动前，请逐项确认以下准备项：

| 序号 | 准备项 | 说明 | 责任人 | 状态 |
| --- | --- | --- | --- | --- |
| 1 | 服务器与 SSH 权限 | 已开通并完成安全组放行（80/443/22） | 【待指派】 | ☐ |
| 2 | 域名与 SSL 证书 | 后台域名已解析，证书已申请（平台 OAuth 回调多为 HTTPS） | 【待指派】 | ☐ |
| 3 | 源码交付包 | 已获取青柠GEO 源码包及部署文档 | 【待指派】 | ☐ |
| 4 | MySQL / Redis / 向量数据库 | 已安装或使用云数据库实例，向量库选型已确定（见 4.7），连接信息可用 | 【待指派】 | ☐ |
| 5 | AI 模型 API Key | OpenAI / Claude / 文心一言 / 通义千问 / Kimi 等按需准备 | 【待指派】 | ☐ |
| 6 | 自媒体平台开放账号 | 百家号、头条号、知乎、网易号等平台开发者/授权账号按需申请 | 【待指派】 | ☐ |
| 7 | 提及检测平台账号 | 按 8 大 AI 平台检测方式准备对应账号/接口【待确认：具体依赖以交付包为准】 | 【待指派】 | ☐ |
| 8 | 数据库账号 | 建议单独建库建账号，授予目标库权限 | 【待指派】 | ☐ |

---

## 4. 源码部署步骤

### 4.1 获取并解压源码

```bash
# 建议部署目录（示例）
mkdir -p /www/qninggeo && cd /www/qninggeo

# 上传或拉取源码包后解压（以实际交付包为准）
unzip qninggeo-source.zip -d /www/qninggeo
```

### 4.2 典型目录结构（以实际交付源码为准）

```
/www/qninggeo
├── server/                 # 后端 ThinkPHP 8【待确认：以交付包为准】
│   ├── app/                # 应用模块
│   ├── config/             # 配置文件（数据库、缓存等）
│   ├── public/             # Web 入口目录（Nginx 指向此处）
│   ├── runtime/            # 运行时目录（需可写）
│   ├── composer.json
│   └── think               # 命令行入口
├── web/                    # 前端 Vue 3 工程【待确认：以交付包为准】
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── extension/              # 浏览器扩展安装包【待确认：以交付包为准】
└── docs/                   # 交付文档（部署说明、SQL、插件安装包等）
```

### 4.3 后端部署（ThinkPHP 8）

```bash
cd /www/qninggeo/server

# 1. 安装 PHP 依赖
composer install --no-dev --optimize-autoloader

# 2. 配置环境文件（数据库、Redis、JWT 密钥等）
cp .example.env .env
vim .env
```

`.env` 关键配置项（字段名以交付包为准）：

```ini
APP_DEBUG = false          # 生产环境必须关闭调试

[DATABASE]
TYPE = mysql
HOSTNAME = 127.0.0.1
DATABASE = qninggeo       # 数据库名
USERNAME = qning_user     # 数据库账号
PASSWORD = ****            # 数据库密码
CHARSET = utf8mb4

[REDIS]
HOST = 127.0.0.1
PORT = 6379
PASSWORD = ****
```

```bash
# 3. 初始化数据库（二选一，以交付包内说明为准）
#    方式 A：导入交付包内的 SQL 文件
mysql -u qning_user -p qninggeo < docs/qninggeo.sql

#    方式 B：使用系统自带安装向导（浏览器访问 http://你的域名/install）【待确认】

# 4. 设置目录权限
chown -R www:www /www/qninggeo/server
chmod -R 755 /www/qninggeo/server
chmod -R 775 /www/qninggeo/server/runtime   # 运行时目录需可写

# 5. 验证后端可运行（临时测试）
php think version
```

### 4.4 前端构建与部署（Vue 3）

```bash
cd /www/qninggeo/web

# 1. 安装依赖
pnpm install

# 2. 配置后端 API 地址（按交付包配置文件调整）
vim .env.production        # 例如 VITE_API_BASE_URL=https://api.你的域名

# 3. 构建
pnpm build

# 4. 构建产物一般位于 dist/ 目录，部署到 Nginx 静态目录
cp -r dist/* /www/qninggeo/frontend-dist/
```

### 4.5 Nginx 站点配置示例

```nginx
server {
    listen       80;
    server_name  geo.你的域名.com;
    return 301 https://$host$request_uri;
}

server {
    listen       443 ssl http2;
    server_name  geo.你的域名.com;

    ssl_certificate     /etc/nginx/ssl/你的域名.pem;
    ssl_certificate_key /etc/nginx/ssl/你的域名.key;

    # 前端静态资源
    root  /www/qninggeo/frontend-dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;   # SPA 路由
    }

    # 后端 API（ThinkPHP 8，指向 public 目录）
    location /api {
        alias /www/qninggeo/server/public;
        index index.php;
        if (!-e $request_filename) {
            rewrite ^/api/(.*)$ /api/index.php?s=$1 last;
        }
        location ~ \.php$ {
            fastcgi_pass   unix:/tmp/php-cgi.sock;   # 或 127.0.0.1:9000
            fastcgi_index  index.php;
            fastcgi_param  SCRIPT_FILENAME $request_filename;
            include        fastcgi_params;
        }
    }

    # 禁止访问敏感目录/文件
    location ~ ^/(runtime|app|config)/ { deny all; }
    location ~ \.(env|sql|lock|log)$  { deny all; }
}
```

> 【待确认】API 路由前缀、PHP-FPM 连接方式（unix socket 或 TCP 端口）请按实际交付包调整。配置完成后执行 `nginx -t && nginx -s reload`。

### 4.6 队列与定时任务

系统存在批量创作、自动托管发布、批量提及检测、报告生成等异步/周期任务，需配置队列进程与计划任务：

**1）队列守护（推荐 Supervisor）：**

```ini
; /etc/supervisor/conf.d/qninggeo-worker.conf
[program:qninggeo-worker]
command=php /www/qninggeo/server/think queue:work
autostart=true
autorestart=true
user=www
stdout_logfile=/www/qninggeo/server/runtime/worker.log
```

```bash
supervisorctl reread && supervisorctl update && supervisorctl start qninggeo-worker
```

**2）定时任务（crontab，命令以交付包为准）：**

```bash
* * * * * php /www/qninggeo/server/think schedule:run >> /dev/null 2>&1
```

> 说明：自动托管发布、授权过期提醒、GEO 周报生成等周期性能力均依赖上述队列与计划任务，**未配置将导致功能静默失效**，请重点验证。

### 4.7 向量数据库部署（知识资产链路）

系统的知识资产链路（企业知识库 → 切片 → Embedding → 向量检索）依赖向量数据库，三选一【待确认：以实际交付包为准】：

| 方案 | 适用场景 | 部署要点 |
| --- | --- | --- |
| **Milvus 2.x** | 大规模在线检索业务 | 支持 Docker Compose / Kubernetes 独立部署，建议单独容器或主机，配置持久化存储 |
| **Faiss** | 离线调优、嵌入式单机 | 以库形式随应用集成，适合离线分析与调优场景，注意索引文件持久化与备份 |
| **pgvector** | 轻量、与关系库同栈 | 为 PostgreSQL 安装 pgvector 扩展即可；需新增 PostgreSQL 实例（与 MySQL 业务库并存） |

```bash
# 示例：Milvus 单机部署（Docker Compose，以官方文档为准）
cd /www/qninggeo/vectordb
docker compose up -d        # 启动 Milvus + etcd + MinIO
```

部署完成后：

1. 在系统配置中填写向量库连接信息（地址、端口、账号）【待确认：配置位置以交付包为准】；
2. 上传测试文档至「素材中心 → 知识库」，验证切片与 Embedding 入库成功；
3. 在 AI 写作中引用知识库生成文章，验证语义检索命中。

### 4.8 竞品逆向研究与多模态模块（Phase B，可选部署）

竞品逆向研究（6 维度拆解，预计 3-5 分钟/次）与多模态分析引擎（图像/视频/音频）依赖以下重计算组件，按 Phase B 路线图分阶段接入【待确认：以实际交付包为准】：

| 阶段 | 组件 | 部署要求 |
| --- | --- | --- |
| Phase B.1 | CLIP（图文匹配）+ YOLO v8（Logo/物体检测） | GPU 推理环境（建议显存 ≥ 8G）或兼容公网 API |
| Phase B.2 | Whisper large-v3（多语言 ASR） | 支持公网 API 调用或本地 GPU 部署；音频量大时建议 GPU |
| Phase B.3 | Video-LLaVA（视频关键帧语义理解） | 大显存 GPU（建议 ≥ 16G）或专用推理服务 |
| Phase B.4 | 跨模态融合引擎（BVI 品牌可见性指数） | 依赖 B.1~B.3 数据层，规划中，暂不可部署 |

部署建议：

1. **模型接入双模式**：多模态能力支持「公网 API + 私有化部署」双模式，初期建议公网 API 快速启用，数据量大或敏感场景再切换私有化 GPU 部署；
2. **任务队列**：竞品逆向分析与多模态分析均为长耗时任务（分钟级），务必确认 4.6 节队列与定时任务已配置，否则任务会假死；
3. **合规确认**：竞品分析涉及对第三方平台内容的采集，监测混合模式（自建账号池 + 浏览器自动化）须评估平台服务条款合规性后再上线。

---

## 5. 系统初始化配置

### 5.1 管理员与版本授权

1. 使用交付包提供的默认管理员账号登录后台（首次登录后**立即修改密码**）；
   【待确认】默认账号信息见交付包《交付说明》，本说明书不记录明文口令。
2. 核对/激活版本授权：**高级版 / 旗舰版 / 无限版**，确认授权与购买版本一致【待确认：激活方式以交付包为准】；
3. 检查顶部合规提示是否正常展示（系统仅用于合规内容创作与分发，发布前必须人工审核）。

### 5.2 蒸馏词与品牌植入词

进入「蒸馏词」模块：

1. 添加品牌核心蒸馏词（支持手动导入、批量添加、分类标签管理）；
2. 为每个蒸馏词配置**品牌植入词**（AI 创作时自动植入，提及检测时匹配判断）；
3. 执行 AI 拓展问题，验证拓展问题生成正常；
4. 核对热度分析（搜索热度、竞争度）与选题推荐能力【待确认：热度数据来源与配置以交付包为准】；
5. 建议为试点品牌先配置 1~3 个蒸馏词做端到端验证。

### 5.3 AI 模型配置

进入「AI 模型配置」模块：

1. 配置各模型 API Key：OpenAI、Claude、文心一言、通义千问、Kimi 等（按需启用）；
2. 配置多 Key 轮询（负载均衡），避免单 Key 限流；
3. 设置任务类型与默认模型映射；
4. 确认 Token 消耗统计已开启，便于成本管控；
5. 模型接入支持「**公网 API + 私有化部署**」双模式：敏感数据场景可切换私有化模型【待确认：私有化模型接入方式以交付包为准】；
6. 验证方式：在 AI 写作中以测试蒸馏词生成一篇文章。

### 5.4 素材中心初始化（画像/模板/知识库）

| 步骤 | 操作 |
| --- | --- |
| 1 | **画像管理**：创建企业/产品画像（企业信息、产品卖点），设置默认画像 |
| 2 | **创作模板**：核对 9 个系统预设模板，按需自定义输出格式与风格 |
| 3 | **图片素材**：上传品牌配图并建立分类 |
| 4 | **知识库**：上传企业资料/产品文档，供 AI 创作引用为事实依据 |

### 5.5 媒体账号授权（自媒体分发）

1. 在各平台开放平台完成应用创建，将回调域名配置为后台域名；
2. 在后台填入平台 AppKey/AppSecret【待确认：字段位置以系统为准】；
3. OAuth 授权添加百家号、头条号、知乎等账号，按品牌/业务线分组；
4. 开启「授权过期自动提醒」。

### 5.6 提及检测与浏览器扩展

1. 在后台生成/下载浏览器扩展安装包【待确认：以交付包为准】；
2. Chrome 内核浏览器进入「扩展程序 → 开发者模式 → 加载已解压的扩展程序」；
3. 在扩展中登录/绑定当前系统账号；
4. 按需完成 8 大 AI 平台检测通道配置：豆包、DeepSeek、腾讯元宝、通义千问、文心一言、Kimi、智谱清言、ChatGPT【待确认：各平台检测依赖以交付包为准，ChatGPT 通常需海外网络出口】；
5. 选择蒸馏词/问题执行批量检测，验证提及率与报告生成正常。

> **监测方式（混合模式）说明**：各 AI 平台检测通道采用「**官方 API + 自建账号池 + 浏览器自动化**」混合模式——官方 API 成本高、限额、难批量，账号池 + 浏览器自动化为主流做法（浏览器扩展即自动化检测载体）。
> **合规提示**：账号池与自动化访问须遵守各平台服务条款，控制访问频率；正式商用前请完成法务/合规评估，详见第 8 章待确认事项。

### 5.7 网站推送（文章接收器插件）

1. 在后台「网站推送」添加目标站点（支持多站点）；
2. 在目标 CMS（EyouCMS 已支持）安装并启用「文章接收器」插件；
3. 将插件生成的对接密钥填入后台站点配置【待确认：以插件说明为准】；
4. 从创作中心选择文章执行「一键推送」，并在推送记录中核对结果。

### 5.8 代理商模式初始化（如为代理商版）

| 步骤 | 操作 |
| --- | --- |
| 1 | 后台「界面设置」完成主站品牌配置（Logo、系统名称、品牌色） |
| 2 | 「代理商管理/客户列表」为终端客户创建子客户，设置分配的功能与配额 |
| 3 | 配置统一 AI Key 或允许客户自备 Key |
| 4 | 验证子客户数据隔离（不同客户账号互不可见） |
| 5 | 「财务管理」配置客户充值、消费记录、利润统计 |

---

## 6. 上线验收检查清单

部署完成后，请逐项验收：

| 序号 | 检查项 | 验收标准 | 结果 |
| --- | --- | --- | --- |
| 1 | 后台登录与授权 | 域名可访问，管理员可登录，版本授权（高级/旗舰/无限版）正常 | ☐ |
| 2 | 数据库/Redis 连接 | 后台系统状态页显示连接正常 | ☐ |
| 3 | 蒸馏词闭环 | 添加蒸馏词 + 品牌植入词，AI 拓展问题生成正常 | ☐ |
| 4 | AI 写作 | 长文章 + 图文内容均可生成；审核流「待审核→已审核」生效 | ☐ |
| 5 | 批量创作与队列 | 多任务排队执行，Supervisor 状态 running，自动托管可触发 | ☐ |
| 6 | 媒体账号发布 | 测试账号 OAuth 授权成功，定时/批量发布成功，失败可重试 | ☐ |
| 7 | 提及检测 | 浏览器扩展可用，批量检测出提及率，分享报告链接可打开 | ☐ |
| 8 | 工作台数据 | AI 可见度报告、品牌事实库、GEO 周报、指标卡数据正常 | ☐ |
| 9 | 网站推送 | 文章成功推送至目标站点并在 CMS 中正常展示 | ☐ |
| 10 | 数据报表 | 提及率/收录率统计、平台对比、趋势图正常，Excel 可导出 | ☐ |
| 11 | 权限与安全 | APP_DEBUG 已关闭；敏感目录不可访问；JWT 密钥已更换 | ☐ |
| 12 | 备份策略 | 数据库每日自动备份已配置且试恢复成功 | ☐ |
| 13 | 代理商功能（如适用） | 子客户可创建、白标生效、数据隔离与配额验证通过 | ☐ |
| 14 | 知识资产链路 | 知识库上传→切片→Embedding 正常；AI 创作可命中引用知识库；向量库连接稳定 | ☐ |
| 15 | 工作台分析维度 | 可见度、引用率、SoV、情感、归因报告数据正常展示 | ☐ |
| 16 | 竞品逆向研究（如适用） | 输入品牌 + 竞品名称（每行一个），3-5 分钟产出 6 维度分析报告 | ☐ |
| 17 | 多模态分析（如适用） | 图像 Logo 检测/OCR、视频关键帧/语音转写、音频 ASR 品牌识别正常 | ☐ |

---

## 7. 运维与维护建议

### 7.1 日常运维

- **备份**：数据库每日全量备份 + binlog 增量；源码与 `.env` 纳入版本管理（密钥除外）；
- **日志**：关注 `runtime/` 日志与 Supervisor 队列日志，及时清理防磁盘打满；
- **监控**：对域名可用性、MySQL/Redis、磁盘空间配置告警；
- **Key 用量**：定期查看 AI 模型 Token 消耗统计，控制成本；
- **授权状态**：定期检查媒体账号授权有效期与 AI 平台检测通道可用性。

### 7.2 安全加固建议

1. 后台限制 IP 白名单或加二次验证；演示账号仅测试环境使用；
2. 数据库、Redis 不暴露公网，Redis 设置强密码；
3. 全站强制 HTTPS，接口限流防刷；
4. 定期更新 PHP/Nginx 安全补丁；
5. AI API Key、平台密钥等敏感信息加密存储，勿写入前端代码。

### 7.3 常见问题（FAQ）

| 问题 | 排查方向 |
| --- | --- |
| 后台打开报 500 | 检查 `.env` 配置、目录权限、`APP_DEBUG` 临时打开看详细报错 |
| 队列任务不执行 | Supervisor 进程状态、Redis 队列连接、crontab 是否生效 |
| AI 生成失败 | API Key 有效性、账户余额、服务器出网是否被墙/限速 |
| 拓展问题不生成 | AI 模型配置是否完成、蒸馏词状态、队列是否运行 |
| 自媒体授权过期 | 平台回调域名是否 HTTPS 且与配置一致，重新走 OAuth 授权 |
| 提及检测不可用 | 浏览器扩展版本、扩展登录状态、平台检测通道授权（ChatGPT 需海外出口） |
| 自动托管不执行 | 队列/计划任务配置、托管规则设置、媒体账号授权状态 |
| 知识库检索无结果 | 向量库连接配置、Embedding 任务队列、文档切片状态 |
| 竞品逆向分析超时/无结果 | 队列是否运行、AI 模型 API 可用性、竞品名称输入格式 |
| 多模态分析失败或缓慢 | GPU 资源/公网多模态 API 配置、媒体文件大小限制、任务队列状态 |
| 推送网站失败 | 目标站「文章接收器」插件是否启用、密钥是否匹配 |

---

## 8. 待确认事项汇总

以下事项需对照实际交付源码包确认后更新本说明书：

| 序号 | 待确认项 | 建议负责人 |
| --- | --- | --- |
| 1 | 实际目录结构与安装向导是否存在 | 【待指派】 |
| 2 | `.env` 字段名与配置项全集 | 【待指派】 |
| 3 | 数据库初始化方式（SQL 导入 or 安装向导） | 【待指派】 |
| 4 | API 路由前缀与 Nginx 重写规则 | 【待指派】 |
| 5 | 队列/定时任务的具体命令 | 【待指派】 |
| 6 | 版本授权（高级/旗舰/无限版）激活方式 | 【待指派】 |
| 7 | 提及检测 8 大 AI 平台各自的检测依赖与网络要求 | 【待指派】 |
| 8 | 浏览器扩展获取与安装方式 | 【待指派】 |
| 9 | 「文章接收器」插件配置细节 | 【待指派】 |
| 10 | 默认管理员账号交付方式 | 【待指派】 |
| 11 | 向量数据库选型（Milvus / pgvector / Faiss）与连接配置位置 | 【待指派】 |
| 12 | 归因报告、EEAT 内容评分、llms.txt 校验等优化层能力的功能边界与配置项 | 【待指派】 |
| 13 | 多模态组件（CLIP / YOLO / Whisper / Video-LLaVA）采用公网 API 还是私有化 GPU 部署 | 【待指派】 |
| 14 | 监测混合模式（自建账号池 + 浏览器自动化）的平台条款合规评估 | 【待指派】 |
| 15 | 竞品逆向研究 6 维度的数据来源与采集边界 | 【待指派】 |

---

# 附录 A：本仓库实际部署（FastAPI + PostgreSQL + ChromaDB）

> 本附录对应**开源仓库 `GEO-platform`（`d:\Mirofish\GEO\`）的真实运行方式**，与正文第 4 章「ThinkPHP 8 + Composer + Nginx」参考架构不同。概念能力（诊断 / 多模态 / 竞品逆向 / 知识库 / 监测 / 优化）一致，只是后端技术栈由 PHP 换成了 Python（FastAPI）。

## A.1 实际架构与端口

| 层 | 本仓库实际实现 | 说明 |
| --- | --- | --- |
| 前端 | Vue 3.5 + Vite 5 + Element Plus（`bmn-frontend/`） | `npm run dev` 默认 `http://127.0.0.1:5173` |
| 后端 | FastAPI（Python），入口 `backend/run.py` | `uvicorn` 监听 `127.0.0.1:5006` |
| API 前缀 | `/api/v2/*` | auth / tenants / geo(intent,knowledge,content,monitor,diagnosis,multimodal,competitor) |
| 数据库 | SQLAlchemy：**SQLite 默认** / PostgreSQL 可选 | `DATABASE_URL` 切换，启动时 `init_db()` 自动建表 |
| 向量库 | ChromaDB（持久化 `backend/chroma_db`） | 嵌入模型 `paraphrase-multilingual-MiniLM-L12-v2`（或 `BAAI/bge-large-zh-v1.5`） |
| Agent | LangGraph + LangChain（`backend/app/agents/orchestrator.py`） | 诊断 / 多模态 / 竞品逆向统一编排 |
| LLM | Ollama（默认 `qwen2.5:latest`）/ OpenAI / DeepSeek / Qwen / Anthropic | `LLM_PROVIDER` 切换 |

- API 文档（Swagger）：`http://127.0.0.1:5006/docs`
- 健康检查：`GET /api/health`

## A.2 环境要求

- Python 3.11+（建议虚拟环境）
- Node 18+（前端）
- PostgreSQL 15+（**可选**，默认用 SQLite，零安装）
- Redis 7+（**可选**，缓存 / 异步任务）
- Ollama（**可选**，本地 LLM；不装则 `LLM_ENABLED=false` 走规则降级）

## A.3 后端部署（实际可执行步骤）

```bash
cd backend
python -m venv venv
# Windows 激活：
venv\Scripts\activate
# 安装依赖（国内用清华镜像）：
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
# 配置环境变量：
cp .env.example .env        # 按需修改 DATABASE_URL / LLM_PROVIDER / OLLAMA_MODEL
# 启动（监听 5006）：
python run.py
```

启动后访问 `http://127.0.0.1:5006/docs` 查看全部 `/api/v2` 端点。

## A.4 前端部署

```bash
cd bmn-frontend
npm install
npm run dev                 # Vite 开发服务器，默认 http://127.0.0.1:5173
# 生产构建：
npm run build               # 产物输出到 dist/，可托管到 Nginx / CDN
```

## A.5 数据库

- **默认（零安装）**：`DATABASE_URL=sqlite:///./geo.db`，无需任何数据库服务；
- **生产（PostgreSQL）**：`DATABASE_URL=postgresql://user:pass@127.0.0.1:5432/geo`；
- 表结构由 `app.models.init_db()` 在启动时自动创建（SQLAlchemy ORM），无需手动执行 SQL。

## A.6 LLM 与向量库初始化

- `LLM_PROVIDER=ollama`（默认）→ 安装 Ollama 并 `ollama pull qwen2.5:latest`；
- 若用 OpenAI / DeepSeek：`LLM_PROVIDER=openai` 并填 `OPENAI_API_KEY` / `OPENAI_BASE_URL`；
- ChromaDB 在首次运行时自动于 `CHROMA_PERSIST_DIR`（默认 `./chroma_db`）初始化，无需单独部署服务。

## A.7 ⚠️ 已知偏差（与正文 ThinkPHP 章节不一致之处）

| 项 | 正文（参考架构） | 本仓库实际 | 处理 |
| --- | --- | --- | --- |
| 后端语言 | ThinkPHP 8（PHP） | FastAPI（Python） | 本仓库无 PHP 代码，第 4 章 Composer/Nginx 步骤不适用 |
| 数据库 | MySQL | PostgreSQL / SQLite | 用 `DATABASE_URL` 切换 |
| 向量库 | Milvus / Faiss / pgvector | ChromaDB | 已内置，无需独立集群 |
| 根 `docker-compose.yml` | — | **AIAdPlacer/pDOOH 遗留**（引用 `ai_adplacer` 库、端口 5002，且 `backend/Dockerfile` 不存在） | 与本仓库不匹配，需重新生成 GEO 专用编排 |
| 根 `.env.example` | — | **AIAdPlacer 遗留模板**（`ai_adplacer` / `TENCENT_MAP_KEY`） | 需替换为 GEO 配置模板 |

> 上述遗留文件属于历史原因，不影响源码直接运行（A.3 / A.4），但容器化部署前必须清理。

## A.8 与交付文档概念映射

详见 **[`技术栈对齐说明.md`](./技术栈对齐说明.md)** —— 六层架构（采集 / 执行 / 分析 / 知识资产 / 优化 / 展示）到本仓库实际模块（api 路由 / agents / ChromaDB / bmn-frontend）的一一对应表。

---

**青柠GEO 软件建立说明书 —— 完**

> 交付协同提醒：建议将本说明书与《青柠GEO 产品介绍》一并上传项目资料库归档；并将上表「待确认事项」逐条创建为事项、指派给研发/实施负责人跟进闭环。
