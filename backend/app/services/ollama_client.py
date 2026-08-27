"""
bus-pDOOH 子系统 — Ollama HTTP 客户端（异步）

通过 httpx 调用本地 Ollama API（Qwen3.5-9B），
支持 chat 和结构化 JSON 输出。
"""
import json
import httpx
from typing import Optional, Dict, Any, List
from app.config import settings


class OllamaClient:
    """Ollama 异步 HTTP 客户端"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or "qwen3.5-9b"

    async def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        调用 Ollama chat 接口。

        Parameters
        ----------
        prompt : str
            用户消息
        system_prompt : str | None
            系统提示
        temperature : float
            采样温度

        Returns
        -------
        str
            模型回复文本
        """
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        return data.get("message", {}).get("content", "")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        调用 Ollama generate 接口（非 chat 模式）。

        Parameters
        ----------
        prompt : str
            用户提示
        system_prompt : str | None
            系统提示（会被拼接到 prompt 前面）
        temperature : float
            采样温度

        Returns
        -------
        str
            模型回复文本
        """
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        return data.get("response", "")

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """
        调用 Ollama 并解析 JSON 返回。

        Parameters
        ----------
        prompt : str
            用户消息（需包含要求返回 JSON 的指示）
        system_prompt : str | None
            系统提示
        temperature : float
            采样温度（低温度利于结构化输出）

        Returns
        -------
        dict
            解析后的 JSON 对象
        """
        text = await self.chat(prompt, system_prompt=system_prompt, temperature=temperature)
        # 尝试从回复中提取 JSON
        text = text.strip()
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # 尝试从 markdown 代码块中提取
        if "```json" in text:
            start = text.index("```json") + 7
            end = text.index("```", start)
            json_str = text[start:end].strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        elif "```" in text:
            parts = text.split("```")
            if len(parts) >= 2:
                json_str = parts[1].strip()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
        # 兜底返回原始文本
        return {"raw_response": text, "parse_error": True}

    async def is_available(self) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False


# 全局实例
ollama_client = OllamaClient()
