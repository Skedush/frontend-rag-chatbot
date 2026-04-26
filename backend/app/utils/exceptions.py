"""
工具模块
==========

通用工具函数和异常类
"""

import logging
from fastapi import HTTPException, status


# 配置日志
def setup_logger(name: str) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# 全局日志器
logger = setup_logger(__name__)


class APIException(HTTPException):
    """API 异常基类"""

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: dict = None
    ):
        super().__init(status_code=status_code, detail=detail, headers=headers)
        logger.error(f"API Exception: {status_code} - {detail}")


class DocumentNotFoundError(APIException):
    """文档未找到"""

    def __init__(self, detail: str = "Directory not found"):
        super().__init__(
            status_code=status_code,
            detail=detail
        )


class FileTypeNotSupportedError(APIException):
    """文件类型不支持"""

    def __init__(self, detail: str = "Only .txt files are supported"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class VectorStoreError(APIException):
    """向量库错误"""

    def __init__(self, detail: str = "Vector store operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class LLMError(APIException):
    """LLM 调用错误"""

    def __init__(self, detail: str = "LLM service error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )
