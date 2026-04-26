"""
API 模块
========

路由定义
"""

from fastapi import APIRouter
from app.api import chat, upload, health

# 创建主路由
api_router = APIRouter()

# 注册子路由
api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(upload.router)

__all__ = ["api_router"]
