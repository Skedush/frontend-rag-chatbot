"""
RAG Chatbot 后端服务
==================

功能：
1. 文档上传：将用户上传的 .txt 文件存储并向量化
2. 流式问答：基于向量数据库检索 + LLM 生成回答
3. 健康检查：确认服务是否正常运行

技术栈：
- FastAPI: Python Web 框架，支持异步和自动 API 文档
- Chroma: 向量数据库，存储文档的向量表示
- SiliconFlow: Embedding 服务，将文本转为向量
- MiniMax: LLM 服务，用于生成回答
"""

import os
import shutil
import json
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import asyncio

# 从 rag_chain 模块导入核心函数
# - init_vectorstore: 初始化向量数据库
# - get_vectorstore: 获取向量数据库实例
# - ingest_documents: 将文档加载并向量化
# - add_text_to_vectorstore: 添加单个文本到向量库
# - stream_minimax: MiniMax 流式聊天
from rag_chain import (
    init_vectorstore,
    get_vectorstore,
    ingest_documents,
    add_text_to_vectorstore,
    stream_minimax
)

# ==================== 配置 ====================
# UPLOAD_DIR: 用户上传文件的存储目录
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/docs")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# MiniMax API 配置
# 从环境变量读取，Docker 容器启动时通过 docker-compose.yml 注入
MINIMAX_API_URL = os.environ.get("MINIMAX_API_URL", "")
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_CHAT_MODEL = os.environ.get("MINIMAX_CHAT_MODEL", "MiniMax-M2.7")

# ==================== FastAPI 应用 ====================
app = FastAPI(title="Frontend RAG Chatbot API", version="1.0.0")

# CORS 中间件配置
# 允许所有来源访问，解决浏览器跨域问题
# 生产环境建议限制 allow_origins 为具体域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应改为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 数据模型 ====================
# Pydantic 模型用于请求/响应数据验证

class ChatRequest(BaseModel):
    """聊天请求模型"""
    question: str  # 用户的问题

class ChatResponse(BaseModel):
    """聊天响应模型（目前用于文档注释）"""
    status: str
    answer: str
    source_documents: Optional[List[dict]] = None


# ==================== 生命周期事件 ====================

@app.on_event("startup")
async def startup_event():
    """
    服务启动时执行
    初始化向量数据库，确保容器启动时向量库就绪
    """
    try:
        init_vectorstore()
        print("Vectorstore initialized")
    except Exception as e:
        print(f"Warning: Failed to initialize vectorstore: {e}")


# ==================== API 端点 ====================

@app.get("/health")
async def health_check():
    """
    健康检查接口
    用于 Docker 健康检查或负载均衡探活
    返回 {"status": "ok"} 表示服务正常
    """
    return {"status": "ok"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    文档上传接口

    流程：
    1. 验证文件格式（仅支持 .txt）
    2. 保存文件到 UPLOAD_DIR 目录
    3. 调用 ingest_documents 将目录中所有文档向量化
    4. 返回处理结果

    Args:
        file: 上传的文件的文件对象

    Returns:
        JSON: {"status": "success", "message": "处理信息"}

    Raises:
        HTTPException: 400 - 文件格式不支持
        HTTPException: 500 - 服务器处理错误
    """
    # 验证文件格式，只允许 .txt 文件
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")

    try:
        # 构建文件保存路径：/app/docs/文件名.txt
        file_path = Path(UPLOAD_DIR) / file.filename

        # 将上传文件内容复制到目标路径
        # shutil.copyfileobj 会逐块复制，大文件也不会占用过多内存
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 将上传的文档加载到向量数据库
        # ingest_documents 会：
        # 1. 读取目录中所有 .txt 文件
        # 2. 将长文本切分成小块（chunk）
        # 3. 对每个 chunk 调用 Embedding 模型转成向量
        # 4. 存储到 Chroma 向量数据库
        result = ingest_documents(UPLOAD_DIR)

        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    流式问答接口

    核心 RAG 流程：
    1. 检索（Retrieval）：从向量数据库中查找与问题最相关的文档块
    2. 增强（Augmentation）：将检索到的内容作为上下文
    3. 生成（Generation）：调用 LLM 基于上下文生成回答

    使用 SSE（Server-Sent Events）实现流式输出
    前端可以逐字显示回答，提供更好的用户体验

    Args:
        request: ChatRequest，包含用户问题

    Returns:
        StreamingResponse: SSE 流，包含回答内容
    """
    # 验证问题不能为空
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # 1. 检索相关文档
    # get_vectorstore() 获取已初始化的向量数据库
    # similarity_search() 使用余弦相似度查找最相关的 k=3 个文档块
    vectorstore = get_vectorstore()
    docs = vectorstore.similarity_search(request.question, k=3)

    # 2. 构建上下文
    # 将检索到的文档内容拼接成上下文字符串
    # 这些内容会被注入到 Prompt 中，让 LLM 知道有哪些参考信息
    context = "\n\n".join([doc.page_content for doc in docs])

    # 构建 System Prompt
    # 指导 LLM 如何使用检索到的上下文
    # 如果没有检索到相关内容，context 为空，LLM 会用自己的知识回答
    system_prompt = f"""你是一个友好的助手。请直接回答用户的问题。
{context}
""" if context else "你是一个友好的助手，请直接回答用户的问题。"

    # 3. 流式返回 MiniMax 的响应
    async def generate():
        """
        异步生成器，用于 SSE 流式输出

        SSE 格式：data: {"content": "字"}\n\n
        最后一个消息：data: [DONE]\n\n 表示结束
        """
        try:
            # 构建消息列表，包含 system prompt 和用户问题
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.question}
            ]

            # 调用 stream_minimax 获取流式响应
            # MiniMax API 返回的是 SSE 格式的流
            # stream_minimax 会解析 SSE，提取 delta 内容逐个 yield
            async for chunk in stream_minimax(
                api_key=MINIMAX_API_KEY,
                api_url=MINIMAX_API_URL,
                model=MINIMAX_CHAT_MODEL,
                messages=messages
            ):
                # 将每个字符/词作为 SSE data 发送
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            # 回答完成后，发送检索到的来源文档
            # 前端可以用这些显示"参考文档"区域
            sources = [
                {
                    # 截取前 200 字符作为预览
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "metadata": doc.metadata  # 包含来源文件路径等
                }
                for doc in docs
            ]
            yield f"data: {json.dumps({'sources': sources})}\n\n"

            # 发送结束标记
            yield "data: [DONE]\n\n"

        except Exception as e:
            # 如果出错，发送错误信息
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    # 返回流式响应
    # media_type="text/event-stream" 告诉浏览器这是 SSE
    # headers 中的配置确保 Nginx 不会缓冲响应
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲，确保实时流
        }
    )


@app.post("/api/add-text")
async def add_text(text: str, source: Optional[str] = None):
    """
    直接添加文本到向量库
    用于不需要上传文件的场景，直接通过 API 添加文本
    """
    try:
        # 构建元数据，可选参数 source 标识文本来源
        metadata = {"source": source} if source else {}

        # 调用 rag_chain 中的函数添加文本
        result = add_text_to_vectorstore(text, metadata)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def stats():
    """
    获取向量库状态
    用于前端检查向量库是否已初始化
    """
    try:
        vectorstore = get_vectorstore()
        return JSONResponse(content={
            "status": "success",
            "message": "Vectorstore is ready"
        })
    except Exception as e:
        return JSONResponse(content={
            "status": "error",
            "message": str(e)
        })


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn
    # 直接运行此文件时启动服务器
    # host="0.0.0.0" 允许外部访问
    # port=8000 HTTP 端口
    uvicorn.run(app, host="0.0.0.0", port=8000)
