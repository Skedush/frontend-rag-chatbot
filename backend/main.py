"""
RAG Chatbot API 入口
=====================

FastAPI 应用主文件

功能：
- 文档上传和向量化
- 流式问答
- 健康检查

启动：
    uvicorn main:app --host 0.0.0.0 --port 8000
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.core.settings import get_settings
from app.api import api_router
from app.services import get_vectorstore_service
from app.utils import logger

# 获取配置
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时初始化向量数据库
    """
    # 启动时执行
    logger.info("Starting RAG Chatbot API...")
    try:
        get_vectorstore_service()
        logger.info("Vectorstore initialized")
    except Exception as e:
        logger.warning(f"Vectorstore init warning: {e}")

    yield

    # 关闭时执行
    logger.info("Shutting down...")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="RAG Chatbot with FastAPI, Chroma and MiniMax",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router)


# SSE 流式响应助手
async def sse_response(generator):
    """生成 SSE 流式响应"""
    async def generate():
        try:
            async for chunk in generator:
                yield chunk
        except Exception as e:
            logger.error(f"SSE error: {e}")
            yield f"data: {str(e)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# 启动入口
if __name__ == "__main__":
    import uvicorn

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
