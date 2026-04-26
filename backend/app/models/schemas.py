"""
数据模型
=========

Pydantic 模型定义，用于请求/响应数据验证
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """聊天请求"""
    question: str = Field(..., min_length=1, description="用户问题")


class SourceDocument(BaseModel):
    """来源文档"""
    content: str = Field(..., description="文档内容")
    metadata: dict = Field(default_factory=dict, description="元数据")


class ChatResponse(BaseModel):
    """聊天响应"""
    status: str
    answer: str
    sources: Optional[List[SourceDocument]] = None


class UploadResponse(BaseModel):
    """上传响应"""
    status: str
    message: str
    chunks: Optional[int] = None
    documents: Optional[int] = None


class StatsResponse(BaseModel):
    """状态响应"""
    status: str
    message: str


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "ok"
