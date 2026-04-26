"""
Utils 模块
==========

工具函数和异常类
"""

from app.utils.exceptions import (
    logger,
    setup_logger,
    APIException,
    DocumentNotFoundError,
    FileTypeNotSupportedError,
    VectorStoreError,
    LLMError
)
from app.utils.responses import (
    SSE_HEADERS,
    create_sse_response,
    sse_content,
    sse_sources,
    sse_error,
    sse_done,
    format_source_documents
)

__all__ = [
    # exceptions
    "logger",
    "setup_logger",
    "APIException",
    "DocumentNotFoundError",
    "FileTypeNotSupportedError",
    "VectorStoreError",
    "LLMError",
    # responses
    "SSE_HEADERS",
    "create_sse_response",
    "sse_content",
    "sse_sources",
    "sse_error",
    "sse_done",
    "format_source_documents"
]
