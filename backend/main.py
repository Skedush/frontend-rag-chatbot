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

from rag_chain import (
    init_vectorstore,
    get_vectorstore,
    ingest_documents,
    add_text_to_vectorstore,
    stream_minimax
)

# 配置
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/docs")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MINIMAX_API_URL = os.environ.get("MINIMAX_API_URL", "")
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_CHAT_MODEL = os.environ.get("MINIMAX_CHAT_MODEL", "MiniMax-M2.7")

# FastAPI 应用
app = FastAPI(title="Frontend RAG Chatbot API", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    status: str
    answer: str
    source_documents: Optional[List[dict]] = None


@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    try:
        init_vectorstore()
        print("Vectorstore initialized")
    except Exception as e:
        print(f"Warning: Failed to initialize vectorstore: {e}")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文档"""
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")

    try:
        file_path = Path(UPLOAD_DIR) / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 加载到向量数据库
        result = ingest_documents(UPLOAD_DIR)

        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """流式问答接口"""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # 1. 检索相关文档
    vectorstore = get_vectorstore()
    docs = vectorstore.similarity_search(request.question, k=3)

    # 2. 构建上下文
    context = "\n\n".join([doc.page_content for doc in docs])
    system_prompt = "你是一个问答助手，请基于提供的参考文档回答用户问题。参考文档：\n" + context

    # 3. 流式返回 MiniMax 的响应
    async def generate():
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.question}
            ]

            async for chunk in stream_minimax(
                api_key=MINIMAX_API_KEY,
                api_url=MINIMAX_API_URL,
                model=MINIMAX_CHAT_MODEL,
                messages=messages
            ):
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            # 返回sources
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


@app.post("/api/add-text")
async def add_text(text: str, source: Optional[str] = None):
    """直接添加文本到向量库"""
    try:
        metadata = {"source": source} if source else {}
        result = add_text_to_vectorstore(text, metadata)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def stats():
    """获取向量库统计"""
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
