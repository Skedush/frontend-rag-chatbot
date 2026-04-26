"""
健康检查 API
=============

服务状态和统计接口
"""

from fastapi import APIRouter

from app.services import get_vectorstore_service
from app.utils import logger

router = APIRouter(tags=["system"])


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}


@router.get("/api/stats")
async def stats():
    """向量库统计"""
    try:
        vectorstore = get_vectorstore_service()
        result = vectorstore.get_stats()
        return result
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {"status": "error", "message": str(e)}
