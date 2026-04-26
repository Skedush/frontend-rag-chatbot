"""
LLM 服务
=========

MiniMax API 调用，支持流式输出
"""

import json
import httpx

from app.core.settings import get_settings
from app.utils import logger


class MiniMaxService:
    """
    MiniMax LLM 服务

    支持：
    1. 同步调用
    2. 流式调用（SSE）
    """

    def __init__(self):
        self.settings = get_settings()

    async def chat(
        self,
        messages: list,
        temperature: float = 0.7,
        stream: bool = True
    ):
        """
        发送聊天请求

        Args:
            messages: 消息列表
            temperature: 温度参数
            stream: 是否流式输出

        Yields:
            str: 每次返回一个字符/词
        """
        headers = {
            "Authorization": f"Bearer {self.settings.MINIMAX_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.settings.MINIMAX_CHAT_MODEL,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.settings.MINIMAX_API_URL}/v1/chat/completions",
                headers=headers,
                json=data
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]

                        if data_str == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})

                            if delta.get("content"):
                                yield delta["content"]
                        except json.JSONDecodeError:
                            continue


class PromptBuilder:
    """
    Prompt 构建器

    负责构建不同场景的 prompt
    """

    @staticmethod
    def build_rag_prompt(context: str, question: str) -> list:
        """
        构建 RAG 问答 prompt

        Args:
            context: 检索到的上下文
            question: 用户问题

        Returns:
            list: messages 列表
        """
        system_prompt = f"""你是一个友好的助手。请直接回答用户的问题。

{context}
""" if context else "你是一个友好的助手，请直接回答用户的问题。"

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]


# 全局单例
_llm_service = None


def get_llm_service() -> MiniMaxService:
    """获取 LLM 服务单例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = MiniMaxService()
    return _llm_service
