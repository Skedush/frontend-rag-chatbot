"""
统一响应工具
============

SSE 流式响应和统一响应格式
"""

import json
from typing import Any, Dict, List, Optional
from fastapi.responses import StreamingResponse


# SSE 流式响应 Headers
SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no"
}


def create_sse_response(generator) -> StreamingResponse:
    """
    创建 SSE 流式响应

    Args:
        generator: 异步生成器

    Returns:
        StreamingResponse
    """
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers=SSE_HEADERS
    )


async def sse_content(content: str) -> str:
    """生成 SSE 内容帧"""
    return f"data: {json.dumps({'content': content})}\n\n"


async def sse_sources(sources: List[Dict[str, Any]]) -> str:
    """生成 SSE 来源文档帧"""
    return f"data: {json.dumps({'sources': sources})}\n\n"


async def sse_error(error: str) -> str:
    """生成 SSE 错误帧"""
    return f"data: {json.dumps({'error': error})}\n\n"


async def sse_done() -> str:
    """生成 SSE 结束帧"""
    return "data: [DONE]\n\n"


def format_source_documents(docs: list) -> List[Dict[str, Any]]:
    """
    格式化来源文档

    Args:
        docs: 文档列表

    Returns:
        格式化后的字典列表
    """
    return [
        {
            "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
            "metadata": doc.metadata
        }
        for doc in docs
    ]
