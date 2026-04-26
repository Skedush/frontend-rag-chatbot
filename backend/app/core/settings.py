"""
配置模块
==========

统一管理所有环境变量配置
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 项目信息
    APP_NAME: str = "RAG Chatbot API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 路径配置
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_DIR: str = os.environ.get("UPLOAD_DIR", "/app/docs")
    VECTORSTORE_DIR: str = os.environ.get("VECTORSTORE_DIR", "/app/vectorstore")
    PERSIST_DIRECTORY: str = os.path.join(
        os.environ.get("VECTORSTORE_DIR", "/app/vectorstore"),
        "chroma_db"
    )

    # MiniMax API
    MINIMAX_API_URL: str = os.environ.get("MINIMAX_API_URL", "")
    MINIMAX_API_KEY: str = os.environ.get("MINIMAX_API_KEY", "")
    MINIMAX_CHAT_MODEL: str = os.environ.get("MINIMAX_CHAT_MODEL", "MiniMax-M2.7")

    # SiliconFlow API (Embedding)
    SILICONFLOW_API_KEY: str = os.environ.get("SILICONFLOW_API_KEY", "")

    # CORS 配置
    CORS_ORIGINS: list = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
