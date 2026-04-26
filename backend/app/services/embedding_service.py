"""
Embedding 服务
==============

文本向量化和检索功能
"""

import os
from typing import List, Optional
import httpx

from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.schema import Document

from app.core.settings import get_settings
from app.utils import logger


class SiliconFlowEmbeddings:
    """
    SiliconFlow Embedding 封装

    将文本转换为向量表示
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.siliconflow.cn/v1/embeddings"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量将文本转换为向量"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {"model": "BAAI/bge-m3", "input": texts}

        with httpx.Client(timeout=60.0) as client:
            response = client.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return [item["embedding"] for item in result["data"]]

    def embed_query(self, text: str) -> List[float]:
        """将单个查询文本转换为向量"""
        return self.embed_documents([text])[0]

    def __call__(self, text: str) -> List[float]:
        return self.embed_query(text)


class VectorStoreService:
    """
    向量存储服务

    负责：
    1. 向量数据库初始化
    2. 文档加载和向量化
    3. 相似度检索
    """

    def __init__(self):
        self.settings = get_settings()
        self._vectorstore: Optional[Chroma] = None
        self._embeddings: Optional[SiliconFlowEmbeddings] = None

    @property
    def embeddings(self) -> SiliconFlowEmbeddings:
        """获取 Embedding 实例（懒加载）"""
        if self._embeddings is None:
            self._embeddings = SiliconFlowEmbeddings(
                api_key=self.settings.SILICONFLOW_API_KEY
            )
        return self._embeddings

    @property
    def vectorstore(self) -> Chroma:
        """获取向量库实例（懒加载）"""
        if self._vectorstore is None:
            self.init_vectorstore()
        return self._vectorstore

    def init_vectorstore(self) -> None:
        """初始化向量数据库"""
        logger.info("Initializing vectorstore...")

        os.makedirs(self.settings.PERSIST_DIRECTORY, exist_ok=True)

        self._vectorstore = Chroma(
            persist_directory=self.settings.PERSIST_DIRECTORY,
            embedding_function=self.embeddings
        )

        logger.info(f"Vectorstore initialized at {self.settings.PERSIST_DIRECTORY}")

    def ingest_documents(self, docs_path: str) -> dict:
        """
        加载并向量化文档

        Args:
            docs_path: 文档目录路径

        Returns:
            dict: 处理结果
        """
        if not os.path.exists(docs_path):
            return {"status": "error", "message": f"Directory not found: {docs_path}"}

        # 加载文档
        loader = DirectoryLoader(docs_path, glob="**/*.txt", loader_cls=TextLoader)
        documents = loader.load()

        if not documents:
            return {"status": "error", "message": "No documents found"}

        # 切分文档
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            length_function=len
        )
        texts = text_splitter.split_documents(documents)

        # 向量化存储
        self._vectorstore = Chroma.from_documents(
            documents=texts,
            embedding=self.embeddings,
            persist_directory=self.settings.PERSIST_DIRECTORY
        )
        self._vectorstore.persist()

        logger.info(f"Ingested {len(texts)} chunks from {len(documents)} documents")

        return {
            "status": "success",
            "message": f"Ingested {len(texts)} chunks from {len(documents)} documents",
            "chunks": len(texts),
            "documents": len(documents)
        }

    def add_text(self, text: str, metadata: dict = None) -> dict:
        """
        添加单个文本到向量库

        Args:
            text: 文本内容
            metadata: 元数据

        Returns:
            dict: 处理结果
        """
        doc = Document(page_content=text, metadata=metadata or {})

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            length_function=len
        )
        splits = text_splitter.split_documents([doc])

        self.vectorstore.add_documents(splits)
        self.vectorstore.persist()

        logger.info(f"Added {len(splits)} chunks")

        return {
            "status": "success",
            "message": f"Added {len(splits)} chunks"
        }

    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        """
        相似度检索

        Args:
            query: 查询文本
            k: 返回数量

        Returns:
            List[Document]: 相关的文档列表
        """
        return self.vectorstore.similarity_search(query, k=k)

    def get_stats(self) -> dict:
        """获取向量库状态"""
        try:
            collection = self.vectorstore._collection
            return {
                "status": "success",
                "message": f"Vectorstore ready. {collection.count()} documents."
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {
                "status": "error",
                "message": str(e)
            }


# 全局单例
_vectorstore_service: Optional[VectorStoreService] = None


def get_vectorstore_service() -> VectorStoreService:
    """获取向量库服务单例"""
    global _vectorstore_service
    if _vectorstore_service is None:
        _vectorstore_service = VectorStoreService()
    return _vectorstore_service
