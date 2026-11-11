"""
A2A Agent Card 发现端点（A2A v1.0 · RFC 8615）

职责边界（零幻觉口径，必须保持）：
- 本端点只提供「发现层」能力：让外部 Agent 凭域名取得 Agent Card。
- 平台**未实现** A2A 任务端点（JSONRPC / GRPC / HTTP+JSON 绑定），
  因此 Card 的 description 明确声明 Discovery-only，不得据此宣称「A2A 协议已实现」。
- 实际可调用能力仍为 REST + OpenAPI，完整端点清单见 /openapi.json。

字段依据：A2A 规范 Latest Released Version 1.0.0。
AgentCard 必填字段：name / description / supportedInterfaces / version /
capabilities / defaultInputModes / defaultOutputModes / skills；JSON 使用 camelCase。
AgentInterface 必填：url / protocolBinding / protocolVersion。
AgentSkill 必填：id / name / description / tags。
AgentCapabilities 无必填子字段，故使用空对象 {}（不声明流式、推送、扩展卡）。
protocolBinding 为开放字符串，官方核心支持值为 JSONRPC / GRPC / HTTP+JSON。
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from app.config import settings

router = APIRouter(tags=["A2A 发现层"])

# 仓库根 .well-known/agent-card.json 为静态可发布资产：
# 即使不启动后端，也可由静态站点 / GitHub Pages 在同一个域名下托管。
# __file__ = <root>/backend/app/api/agent_card_routes.py → parents[3] = <root>
CARD_FILE = Path(__file__).resolve().parents[3] / ".well-known" / "agent-card.json"

# Agent Card 变更频率低，按官方 Agent Discovery 建议提供缓存头（5 分钟）
CACHE_CONTROL = "public, max-age=300"


def _load_card() -> dict:
    """读取静态 Agent Card；文件缺失时显式报错，绝不返回伪造内容。"""
    if not CARD_FILE.is_file():
        raise HTTPException(status_code=503, detail="agent-card.json not deployed")
    return json.loads(CARD_FILE.read_text(encoding="utf-8"))


@router.get("/.well-known/agent-card.json", include_in_schema=False)
def agent_card(request: Request) -> Response:
    """
    返回 A2A Agent Card，并把接口地址与版本号对齐到当前运行实例。

    - MTO_PUBLIC_BASE_URL：部署到公网时指定外部可达地址；未配置则回退到请求 base_url。
    - ETag 由响应体内容哈希生成，配合 If-None-Match 返回 304，避免重复下载。
    - 不修改静态源文件，保证仓库内资产与运行时响应除 URL/版本外完全一致。
    """
    card = _load_card()

    base_url = os.getenv("MTO_PUBLIC_BASE_URL") or str(request.base_url).rstrip("/")
    card["supportedInterfaces"][0]["url"] = base_url
    card["version"] = settings.APP_VERSION

    body = json.dumps(card, ensure_ascii=False, separators=(",", ":"))
    etag = '"' + hashlib.sha256(body.encode("utf-8")).hexdigest()[:16] + '"'
    headers = {"Cache-Control": CACHE_CONTROL, "ETag": etag}

    # 条件请求：Card 未变更时返回 304，响应体为空
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)
    return Response(content=body, media_type="application/json", headers=headers)
