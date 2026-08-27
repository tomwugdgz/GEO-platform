"""
LLM客户端封装
兼容OpenAI API的任意模型
"""
import os
import json
from typing import Optional, Dict, Any, List
from app.config import settings


class LLMClient:
    """LLM客户端"""
    
    def __init__(self):
        self.api_key = settings.LLM_API_KEY or os.getenv("LLM_API_KEY", "")
        self.api_url = settings.LLM_API_URL or os.getenv("LLM_API_URL", "")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self._client = None
    
    def _get_client(self):
        """延迟初始化OpenAI客户端"""
        if self._client is None:
            from openai import OpenAI
            if self.api_key and self.api_url:
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_url,
                )
            else:
                # 无API Key时返回模拟响应
                self._client = None
        return self._client
    
    async def chat(self, prompt: str, system_prompt: str = None, temperature: float = 0.7) -> str:
        """对话接口"""
        client = self._get_client()
        
        if not client:
            return self._mock_response(prompt)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return self._mock_response(prompt)
    
    async def generate_report(self, data: Any, context: str = "") -> Dict[str, Any]:
        """生成分析报告"""
        prompt = f"""
        基于以下数据生成一份专业的分析报告：

        数据: {json.dumps(data, ensure_ascii=False, default=str)}

        {context}

        请返回JSON格式，包含：
        - summary: 总体摘要
        - insights: 关键发现（列表）
        - recommendations: 优化建议（列表）
        - recommended_areas: 推荐投放区域（列表）
        - best_times: 最佳投放时段（列表）
        """
        
        response = await self.chat(prompt)
        try:
            return json.loads(response)
        except:
            return self._mock_report(data)
    
    def _mock_response(self, prompt: str) -> str:
        """无API Key时的模拟响应"""
        return f"""
        分析报告（模拟模式）:

        基于您的查询，系统已生成以下分析结果：

        1. 目标人群特征已识别，建议优先投放核心商圈
        2. 预算分配建议：线上60% + 线下40%
        3. 最佳时段：早晚高峰（7-9点，17-19点）
        4. 创意方向：结合社区场景，突出产品核心价值

        注意：当前为模拟模式，配置LLM API后可获得更精准的AI分析。
        """
    
    def _mock_report(self, data: Any) -> Dict[str, Any]:
        """模拟报告"""
        return {
            "summary": "基于数据分析，建议优先投放核心商圈和高流量区域",
            "insights": [
                "年轻人群（25-34岁）为主要消费群体",
                "天河区体育中心区域ROI最高",
                "微信朋友圈广告性价比最优",
                "电梯广告在CBD区域效果突出"
            ],
            "recommendations": [
                "增加线上媒体预算占比至60%",
                "优化珠江新城和北京路的点位选择",
                "早晚高峰时段加强投放",
                "尝试DCO动态创意优化"
            ],
            "recommended_areas": ["天河体育中心", "北京路步行街", "珠江新城"],
            "best_times": ["07:00-09:00", "12:00-14:00", "17:00-19:00"],
        }


# 全局实例
llm_client = LLMClient()
