"""
聊天 API
========

流式问答接口
"""

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest, SourceDocument
from app.services import get_vectorstore_service, get_llm_service, PromptBuilder
from app.utils import logger

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    流式问答接口

    流程：
    1. 检索相关文档
    2. 构建 Prompt
    3. 调用 LLM 流式生成回答
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # 1. 检索相关文档
    vectorstore = get_vectorstore_service()
    docs = vectorstore.similarity_search(request.question, k=3)

    # 2. 构建上下文
    context = "\n\n".join([doc.page_content for doc in docs])
    messages = PromptBuilder.build_rag_prompt(context, request.question)

    # 3. 流式生成
    async def generate():
        try:
            llm = get_llm_service()
            async for chunk in llm.chat(messages):
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            # 返回来源文档
            sources = [
                {
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in docs
            ]
            yield f"data: {json.dumps({'sources': sources})}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
