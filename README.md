---
title: "GEO - 生成式引擎优化平台"
description: "GEO (Generative Engine Optimization) 平台：让品牌在 AI 搜索中获得优先展示。提供品牌 GEO 诊断、多模态诊断、竞品逆向研究、意图洞察、知识库、AI 内容生产、全域监测。FastAPI + Vue3 + LangGraph + ChromaDB。"
keywords: "GEO, 生成式引擎优化, Generative Engine Optimization, AI搜索优化, 品牌诊断, 多模态诊断, 竞品逆向, LLM, A2A, Agent, FastAPI, Vue3, LangChain, RAG"
author: "Tom (duckwolf)"
url: "https://github.com/tomwugdgz/GEO-platform"
topics: "geo, generative-engine-optimization, llm, ai-search, brand-optimization, multimodal, competitor-analysis, fastapi, vue3, langchain, langgraph, rag, chromadb, a2a, agent"
---

# 🚀 GEO - 生成式引擎优化平台

> **让品牌在 AI 搜索中获得优先展示**

GEO（Generative Engine Optimization）是一个面向 AI 搜索时代的企业级品牌优化平台，帮助品牌在 DeepSeek、豆包、通义千问、Kimi 等 8 大 AI 搜索引擎中获得更高的可见度和出镜率。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.5+-4FC08D.svg)](https://vuejs.org/)
[![AI-Friendly](https://img.shields.io/badge/llms.txt-included-ff69b4.svg)](llms.txt)
[![A2A](https://img.shields.io/badge/A2A-ready-9b59b6.svg)](llms.txt)

<!-- AI-READABLE TAGS (for LLM crawlers / A2A agents / search platforms)
@type: SoftwareSourceCode
@application: GenerativeEngineOptimization
@category: AI-Search-Optimization / Brand-Visibility / Multimodal-Diagnostics / Competitor-Reverse-Engineering
@tech: FastAPI, Vue3, LangGraph, ChromaDB, PostgreSQL, Redis, Ollama, OpenAI
@api: REST + OpenAPI (Swagger at /docs), MCP-compatible, Function-Calling-ready
@platforms: DeepSeek, Doubao, Yuanbao, Tongyi, Wenxin, Nami, Kimi, Zhipu
@license: MIT
@author: Tom (duckwolf)
@contact: https://duckwolf.cn
@repo: https://github.com/tomwugdgz/GEO-platform
-->

## 📋 目录

- [AI 可读标签与 A2A 集成](#-ai-可读标签与-a2a-集成)
- [核心特性](#-核心特性)
- [系统架构](#-系统架构)
- [快速开始](#-快速开始)
- [API 文档](#-api-文档)
- [技术栈](#-技术栈)
- [项目结构](#-项目结构)
- [开发指南](#-开发指南)
- [部署](#-部署)
- [路线图](#-路线图)
- [贡献](#-贡献)
- [许可证](#-许可证)
- [📚 交付文档与体系（青柠GEO）](#交付文档与体系青柠geo)

## 📚 交付文档与体系（青柠GEO）

> 本仓库同时收录完整的 **青柠GEO 产品交付文档与 7 阶段 47 份模板体系**（位于 `docs/` 目录）。
> 注意：交付文档描述的是产品**参考架构**（Vue 3 + ThinkPHP 8 + MySQL），而本仓库**实际运行栈**为 **FastAPI + PostgreSQL/SQLite + LangGraph + ChromaDB**；差异说明与概念映射见 [`docs/青柠GEO-交付文档/技术栈对齐说明.md`](docs/青柠GEO-交付文档/技术栈对齐说明.md)。

### 文档地图

- **总索引**：[`docs/README.md`](docs/README.md)
- **产品与交付主文档**：[`青柠GEO-产品介绍.md`](docs/青柠GEO-交付文档/青柠GEO-产品介绍.md) · [`青柠GEO-软件建立说明书.md`](docs/青柠GEO-交付文档/青柠GEO-软件建立说明书.md)（含 **附录 A：本仓库实际 FastAPI 部署**）
- **七阶段模板体系**：`docs/青柠GEO-交付文档/青柠GEO-项目文档模板/`（00 总览 → 07 部署运维，共 47 份产出文件模板）
- **技术栈对齐**：[`技术栈对齐说明.md`](docs/青柠GEO-交付文档/技术栈对齐说明.md)

## 🤖 AI 可读标签与 A2A 集成

本项目原生支持 **AI 爬虫、LLM Agent、A2A (Agent-to-Agent) 协议客户端** 自动发现与对接：

### 📄 `llms.txt`（LLM 首选入口）

仓库根目录提供 [`llms.txt`](llms.txt) — 遵循 [Answer.AI llms.txt 标准](https://llmstxt.org/)，为大型语言模型提供结构化项目摘要。主流 AI 爬虫（Claude、GPT、Gemini、Perplexity）会优先读取此文件理解项目。

### 🏷️ AI 可读元数据标签

README 顶部 YAML frontmatter + HTML 注释标签包含完整的机器可读元数据（`@type`、`@category`、`@tech`、`@api`、`@platforms` 等），便于知识图谱、向量库、Agent 注册中心索引。

### 🔌 A2A / Agent 调用方式

后端暴露标准 REST API（FastAPI，OpenAPI 自动生成），任意 Agent 框架可直接调用：

```python
# Agent 调用示例：触发品牌 GEO 诊断
import httpx

async def diagnose_brand(brand: str, product: str):
    # 1. 启动诊断任务
    r = await httpx.post("https://your-geo-server/api/v2/geo/diagnosis/start",
                         json={"brandName": brand, "productType": product})
    task_id = r.json()["task_id"]
    # 2. 轮询状态
    while True:
        status = await httpx.get(f"https://your-geo-server/api/v2/geo/diagnosis/status/{task_id}")
        if status.json()["stage"] == "completed":
            break
    # 3. 获取结果
    result = await httpx.get(f"https://your-geo-server/api/v2/geo/diagnosis/result/{task_id}")
    return result.json()
```

- **OpenAPI Schema**: 服务运行后访问 `/docs` (Swagger UI) 或 `/openapi.json` 获取完整端点定义
- **MCP 兼容**: 所有端点可经 MCP Server 封装为 Tool，被 Claude Desktop / Cursor 等直接调用
- **Function Calling 就绪**: 端点 JSON Schema 可直接转为 LLM function 定义

## ✨ 核心特性

### 🎯 品牌 GEO 诊断
- **AIVO 四维评分体系**：AI 搜索可见性 × 基建完善度 × 竞争优势 × 舆情健康度
- **8 大 AI 平台覆盖**：DeepSeek、豆包、元宝、通义千问、文心一言、纳米搜索、Kimi、智谱清言
- **4 阶段诊断流水线**：基础调研 → 收录检测 → 舆情分析 → 评分建议
- **实时进度追踪**：WebSocket 推送诊断进度，4 阶段可视化展示

### 🖼️ 多模态诊断
- **图片分析**：品牌 LOGO、产品图、场景图在 AI 搜索中的识别率
- **视频分析**：短视频内容在 AI 答案中的引用情况
- **音频分析**：播客、音频内容的 AI 可索引性评估
- **跨模态关联**：文本-图片-视频-音频的综合 GEO 健康度

### 🔍 竞品逆向研究
- **竞品内容拆解**：分析竞品在 AI 搜索中的出镜策略
- **关键词逆向**：提取竞品高频使用的 GEO 关键词
- **策略逆向**：逆向工程竞品的品牌基建布局
- **威胁等级评估**：量化竞品对品牌的 GEO 威胁程度

### 📊 意图洞察
- **问题聚类**：KMeans 算法对用户提问进行意图分类
- **意图地图**：可视化展示用户意图分布与覆盖度
- **问题类型修正**：根据品牌特性调整不同类型问题的权重

### 📚 品牌知识库
- **RAG 增强检索**：ChromaDB 向量数据库 + BGE-M3 嵌入模型
- **知识单元管理**：品牌故事、产品信息、FAQ、案例的结构化管理
- **多租户隔离**：tenant_id + brand_id 双重隔离机制

### ✍️ AI 内容生产
- **智能写作**：基于品牌知识库的 GEO 优化内容生成
- **多平台适配**：针对小红书、知乎、公众号等平台的内容风格调整
- **SEO/GEO 双优化**：同时优化传统搜索引擎和 AI 搜索引擎

### 📡 全域监测
- **实时追踪**：8 大 AI 平台的品牌出镜率监控
- **趋势分析**：GEO 健康度、内容覆盖度、分发成功率趋势
- **预警机制**：舆情异常、出镜率下降的实时告警

### 🏢 多租户架构
- **租户隔离**：完全的数据隔离和权限控制
- **品牌管理**：单租户多品牌支持
- **灵活计费**：按租户/品牌/功能模块的计费体系

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (Vue 3 + Vite)                   │
│  ┌──────────┬──────────┬──────────┬──────────┐         │
│  │ 品牌诊断 │ 竞品逆向 │ 多模态   │ 监测看板 │         │
│  └──────────┴──────────┴──────────┴──────────┘         │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/WebSocket
┌────────────────────▼────────────────────────────────────┐
│              后端 (FastAPI + Uvicorn)                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │  API 路由层 (10 个模块, 69+ 端点)                 │  │
│  │  ├─ 认证授权    ├─ 租户管理    ├─ 意图洞察       │  │
│  │  ├─ 知识库      ├─ 内容生产    ├─ 监测看板       │  │
│  │  ├─ 品牌诊断    ├─ 多模态诊断  ├─ 竞品逆向       │  │
│  │  └─ 商业工作流                                    │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  业务逻辑层                                        │  │
│  │  ├─ LangGraph Agent 编排                          │  │
│  │  ├─ RAG 检索增强 (ChromaDB + BGE-M3)              │  │
│  │  ├─ 多模态分析 (Image/Video/Audio)                │  │
│  │  └─ 竞品逆向引擎                                   │  │
│  └──────────────────────────────────────────────────┘  │
└────────┬──────────────┬──────────────┬─────────────────┘
         │              │              │
    ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
    │PostgreSQL│   │  Redis  │   │ Ollama  │
    │ (主库)   │   │ (缓存)  │   │ (LLM)   │
    └─────────┘   └─────────┘   └─────────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+ (可选，默认 SQLite)
- Redis 7+ (可选)

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/geo.git
cd geo
```

### 2. 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库和 LLM

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 5006 --reload
```

访问 API 文档：http://localhost:5006/docs

### 3. 前端启动

```bash
cd bmn-frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问前端：http://localhost:5173

### 4. Docker 部署（推荐）

```bash
# 一键启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 📖 API 文档

### 核心 API 端点

#### 品牌 GEO 诊断
```bash
# 启动诊断任务
POST /api/v2/geo/diagnosis/start
{
  "brandName": "品牌名称",
  "productType": "产品类型",
  "website": "https://example.com",
  "platforms": ["deepseek", "doubao", "yuanbao"]
}

# 查询诊断状态
GET /api/v2/geo/diagnosis/status/{task_id}

# 获取诊断结果
GET /api/v2/geo/diagnosis/result/{task_id}

# 获取支持的 AI 平台列表
GET /api/v2/geo/diagnosis/platforms
```

#### 多模态诊断
```bash
# 图片分析
POST /api/v2/geo/multimodal/image/analyze
Content-Type: multipart/form-data
file: <image_file>

# 视频分析
POST /api/v2/geo/multimodal/video/analyze

# 获取多模态能力矩阵
GET /api/v2/geo/multimodal/capabilities
```

#### 竞品逆向
```bash
# 竞品分析
POST /api/v2/geo/competitor/analyze
{
  "brandName": "我的品牌",
  "competitors": ["竞品A", "竞品B", "竞品C"],
  "analysisDepth": "deep"
}

# 获取竞品逆向能力矩阵
GET /api/v2/geo/competitor/capabilities
```

#### 意图洞察
```bash
# 种子问题生成
POST /api/v2/geo/intent/seed
{
  "brandName": "品牌名称",
  "productType": "产品类型"
}

# 查询意图列表
GET /api/v2/geo/intent/queries?tenant_id=xxx
```

#### 知识库管理
```bash
# 批量创建知识单元
POST /api/v2/geo/knowledge/units
{
  "units": [
    {
      "title": "品牌故事",
      "content": "...",
      "category": "brand_story"
    }
  ]
}
```

完整的 API 文档请访问：http://localhost:5006/docs (Swagger UI)

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI 0.109+
- **ORM**: SQLAlchemy 2.0+
- **数据库**: PostgreSQL 15+ / SQLite
- **缓存**: Redis 7+
- **任务队列**: Celery + Redis (可选)
- **AI 框架**: LangChain 0.3+ / LangGraph 0.2+
- **向量数据库**: ChromaDB 0.5+
- **嵌入模型**: Sentence Transformers (BGE-M3)
- **LLM 支持**: Ollama / OpenAI / DeepSeek / Qwen

### 前端
- **框架**: Vue 3.5+ (Composition API)
- **构建工具**: Vite 5+
- **UI 组件**: Element Plus 2.9+
- **路由**: Vue Router 4+
- **HTTP 客户端**: Axios 1.20+
- **样式**: 像素科技风自定义主题

### 基础设施
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **监控**: Prometheus + Grafana (可选)

## 📁 项目结构

```
GEO/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/               # API 路由层 (10 个模块)
│   │   │   ├── auth_routes.py
│   │   │   ├── tenants_routes.py
│   │   │   ├── intent_routes.py
│   │   │   ├── knowledge_routes.py
│   │   │   ├── content_routes.py
│   │   │   ├── monitor_routes.py
│   │   │   ├── diagnosis_routes.py
│   │   │   ├── multimodal_routes.py
│   │   │   ├── competitor_routes.py
│   │   │   └── business_routes.py
│   │   ├── agents/            # LangGraph Agent 编排
│   │   ├── models/            # 数据模型 (17 张表)
│   │   ├── services/          # 业务逻辑层
│   │   │   ├── llm_client.py
│   │   │   ├── rag_kb.py
│   │   │   ├── competitor_monitor.py
│   │   │   └── ...
│   │   ├── core/              # 核心组件
│   │   │   ├── async_db.py
│   │   │   ├── distributed_lock.py
│   │   │   └── exceptions.py
│   │   ├── main.py            # FastAPI 入口
│   │   └── config.py          # 配置管理
│   ├── requirements.txt
│   └── .env.example
│
├── bmn-frontend/              # 前端应用
│   ├── src/
│   │   ├── views/             # 页面视图
│   │   │   ├── BrandDiagnosis.vue
│   │   │   ├── geo/
│   │   │   │   ├── StoryPage.vue
│   │   │   │   ├── Dashboard.vue
│   │   │   │   ├── WorkflowView.vue
│   │   │   │   └── ...
│   │   │   └── ...
│   │   ├── styles/            # 样式文件
│   │   │   └── pixel.css      # 像素科技风主题
│   │   ├── App.vue
│   │   ├── main.js
│   │   └── router/
│   ├── package.json
│   └── vite.config.js
│
├── docker-compose.yml         # Docker 编排
├── .env.example               # 环境变量示例
└── README.md
```

## 💡 开发指南

### 添加新的 API 路由

1. 在 `backend/app/api/` 创建新的路由文件：

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/example")
async def example_endpoint():
    return {"message": "Hello GEO"}
```

2. 在 `backend/app/main.py` 注册路由：

```python
from app.api.example_routes import router as example_router

app.include_router(example_router, prefix="/api/v2/geo/example", tags=["示例模块"])
```

3. 重启后端服务，访问 http://localhost:5006/docs 查看新端点

### 前端像素科技风主题

项目采用自定义像素科技风主题，核心样式定义在 `bmn-frontend/src/styles/pixel.css`：

- **主背景**: `#030617` (深空黑)
- **霓虹色**: 
  - 青色 `#00f0ff`
  - 绿色 `#39ff14`
  - 粉色 `#ff2e97`
  - 紫色 `#b537f2`
  - 黄色 `#fff200`
- **字体**: JetBrains Mono + VT323 + Press Start 2P

### 多租户数据隔离

所有业务表都包含 `tenant_id` 和 `brand_id` 字段，查询时必须带上这两个参数：

```python
@router.get("/items")
async def get_items(tenant_id: str, brand_id: str):
    items = db.query(Item).filter(
        Item.tenant_id == tenant_id,
        Item.brand_id == brand_id
    ).all()
    return items
```

## 🚢 部署

### 生产环境部署

1. **配置环境变量**

```bash
cp .env.example .env
# 编辑 .env，设置：
# - DATABASE_URL (PostgreSQL)
# - REDIS_URL
# - LLM_PROVIDER (ollama/openai/dashscope)
# - OPENAI_API_KEY (如使用 OpenAI)
```

2. **启动服务**

```bash
# 使用 Docker Compose
docker-compose up -d

# 或手动启动
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 5006

cd bmn-frontend
npm run build
# 使用 Nginx 部署 dist 目录
```

3. **Nginx 配置示例**

```nginx
server {
    listen 80;
    server_name geo.example.com;

    location / {
        root /path/to/bmn-frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:5006;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://localhost:5006;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }
}
```

### 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接字符串 | `postgresql://...` |
| `REDIS_URL` | Redis 连接字符串 | `redis://127.0.0.1:6379/1` |
| `LLM_PROVIDER` | LLM 提供商 | `ollama` |
| `OLLAMA_BASE_URL` | Ollama 服务地址 | `http://127.0.0.1:11434` |
| `GEO_CHAT_MODEL` | 聊天模型 | `qwen3.5:9b` |
| `OPENAI_API_KEY` | OpenAI API Key | - |
| `OPENAI_BASE_URL` | OpenAI API Base URL | `https://api.openai.com/v1` |

## 🗺️ 路线图

### v1.0 (当前)
- ✅ 品牌 GEO 诊断（AIVO 四维评分）
- ✅ 多模态诊断框架（图片/视频/音频）
- ✅ 竞品逆向研究
- ✅ 意图洞察与知识库
- ✅ AI 内容生产
- ✅ 全域监测看板
- ✅ 多租户架构

### v1.1 (计划中)
- [ ] 真实 AI 平台 API 对接（DeepSeek、豆包等）
- [ ] 多模态分析深度集成（CLIP、Whisper）
- [ ] 竞品逆向自动化（爬虫 + NLP）
- [ ] WebSocket 实时推送优化
- [ ] 移动端适配

### v2.0 (规划中)
- [ ] SaaS 化部署（多租户计费）
- [ ] 插件市场（第三方数据源接入）
- [ ] AI Agent 自主优化（自动调整 GEO 策略）
- [ ] 跨平台数据同步（小程序、App）

## 🤝 贡献

欢迎贡献代码！请遵循以下流程：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 开发规范

- **后端**: 遵循 PEP 8，使用 Black 格式化
- **前端**: 遵循 Vue 3 Composition API 规范
- **提交信息**: 使用语义化提交信息 (feat/fix/docs/style/refactor/test/chore)

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的 Web 框架
- [Vue 3](https://vuejs.org/) - 渐进式 JavaScript 框架
- [LangChain](https://langchain.com/) - LLM 应用开发框架
- [ChromaDB](https://www.trychroma.com/) - 开源向量数据库
- [Element Plus](https://element-plus.org/) - Vue 3 组件库

## 📧 联系方式

- **项目作者**: Tom (duckwolf)
- **个人网站**: [duckwolf.cn](https://duckwolf.cn)
- **GitHub**: [@tomwugdgz](https://github.com/tomwugdgz)
- **仓库**: [github.com/tomwugdgz/GEO-platform](https://github.com/tomwugdgz/GEO-platform)
- **Issue/反馈**: [GitHub Issues](https://github.com/tomwugdgz/GEO-platform/issues)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star 支持！⭐**

[Star](https://github.com/tomwugdgz/GEO-platform) · [Fork](https://github.com/tomwugdgz/GEO-platform/fork) · [Issue](https://github.com/tomwugdgz/GEO-platform/issues)

</div>
