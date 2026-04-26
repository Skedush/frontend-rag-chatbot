"""
上传 API
========

文档上传和向量化接口
"""

import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.settings import get_settings
from app.services import get_vectorstore_service
from app.utils import logger

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    上传文档

    支持 .txt 文件，上传到指定目录后自动向量化
    """
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")

    settings = get_settings()

    try:
        # 保存文件
        file_path = Path(settings.UPLOAD_DIR) / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Uploaded file: {file.filename}")

        # 向量化
        vectorstore = get_vectorstore_service()
        result = vectorstore.ingest_documents(settings.UPLOAD_DIR)

        return result

    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-text")
async def add_text(text: str, source: str = None):
    """
    直接添加文本

    用于不需要上传文件的场景
    """
    try:
        vectorstore = get_vectorstore_service()
        metadata = {"source": source} if source else {}
        result = vectorstore.add_text(text, metadata)

        logger.info(f"Added text from: {source or 'unknown'}")

        return result

    except Exception as e:
        logger.error(f"Add text error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
