"""
聊天 API
========

流式问答接口
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest
from app.services import get_vectorstore_service, get_llm_service, PromptBuilder
from app.utils import logger, create_sse_response, sse_content, sse_sources, sse_error, sse_done, format_source_documents

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
                yield await sse_content(chunk)

            # 返回来源文档
            yield await sse_sources(format_source_documents(docs))
            yield await sse_done()

        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield await sse_error(str(e))

    return create_sse_response(generate())
