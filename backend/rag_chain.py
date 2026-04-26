"""
RAG 核心逻辑模块
==================

功能：
1. Embedding 模型封装（文本 → 向量）
2. 向量数据库初始化和持久化
3. 文档加载、切分、向量化
4. 相似度检索
5. MiniMax LLM 调用（支持流式）

技术栈：
- Chroma: 轻量级向量数据库
- LangChain: RAG 应用框架
- httpx: 异步 HTTP 客户端
"""

import os
from typing import List, Optional

# LangChain 组件
# TextLoader: 加载文本文件
# DirectoryLoader: 加载目录下所有文件
from langchain_community.document_loaders import TextLoader, DirectoryLoader

# RecursiveCharacterTextSplitter: 递归字符文本分割器
# 将长文档切分成小块，支持重叠
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Chroma: 向量数据库
from langchain_community.vectorstores import Chroma

# RetrievalQA: 检索增强问答链
from langchain.chains import RetrievalQA

# Document: LangChain 的文档对象
from langchain.schema import Document

# RunnableLambda: 将普通函数转为 Runnable
from langchain_core.runnables import RunnableLambda

# httpx: 异步 HTTP 客户端，用于调用 MiniMax API
import httpx

# ==================== 配置 ====================

# 向量数据库存储路径
# Docker 容器内：/app/vectorstore
# 宿主机映射到 ./vectorstore
VECTORSTORE_DIR = os.environ.get("VECTORSTORE_DIR", "/app/vectorstore")

# Chroma 持久化目录
PERSIST_DIRECTORY = os.path.join(VECTORSTORE_DIR, "chroma_db")

# MiniMax API 配置（从环境变量读取）
MINIMAX_API_URL = os.environ.get("MINIMAX_API_URL", "")
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_CHAT_MODEL = os.environ.get("MINIMAX_CHAT_MODEL", "MiniMax-M2.7")

# SiliconFlow API 配置（Embedding 服务，国内可访问）
SILICONFLOW_API_KEY = os.environ.get("SILICONFLOW_API_KEY", "")

# ==================== 全局变量 ====================

# 全局向量数据库实例
# 避免重复连接，提升性能
vectorstore: Optional[Chroma] = None

# 全局 QA Chain 实例
# RetrievalQA 链，用于执行 RAG 问答
qa_chain: Optional[RetrievalQA] = None


# ==================== MiniMax LLM ====================

def create_minimax_llm(api_key: str, api_url: str, model: str):
    """
    创建 MiniMax LLM 实例

    这是一个同步版本的 LLM 调用（非流式）
    用于初始化 RetrievalQA 链

    Args:
        api_key: MiniMax API 密钥
        api_url: MiniMax API 地址
        model: 模型名称

    Returns:
        RunnableLambda: 可调用的 LLM 对象
    """
    def call(prompt, **kwargs) -> str:
        """
        执行 LLM 调用

        Args:
            prompt: 输入提示词
            kwargs: 其他参数，如 temperature

        Returns:
            str: LLM 生成的回答
        """
        # 处理 prompt（可能是 StringPromptValue 对象）
        prompt_text = str(prompt) if not isinstance(prompt, str) else prompt

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt_text}],
            "temperature": kwargs.get("temperature", 0.7)
        }

        # 使用同步 httpx.Client 调用 API
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{api_url}/v1/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    return RunnableLambda(call)


async def stream_minimax(api_key: str, api_url: str, model: str, messages: list, temperature: float = 0.7):
    """
    MiniMax 流式聊天

    使用 SSE（Server-Sent Events）逐字返回 LLM 生成的内容
    实现真正的流式输出

    Args:
        api_key: MiniMax API 密钥
        api_url: MiniMax API 地址
        model: 模型名称
        messages: 消息列表 [{"role": "user", "content": "..."}]
        temperature: 温度参数，控制随机性

    Yields:
        str: 每次 yield 一个字/词
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": True  # 启用流式输出
    }

    # 使用异步客户端
    async with httpx.AsyncClient(timeout=120.0) as client:
        # 发送请求并处理流式响应
        async with client.stream("POST", f"{api_url}/v1/chat/completions", headers=headers, json=data) as response:
            # iter_lines() 逐行读取响应
            async for line in response.aiter_lines():
                # SSE 格式：data: {...}
                if line.startswith("data: "):
                    data_str = line[6:]  # 去掉 "data: " 前缀

                    # MiniMax API 结束时发送 [DONE]
                    if data_str == "[DONE]":
                        break

                    try:
                        import json
                        chunk = json.loads(data_str)

                        # 提取 delta 中的内容
                        delta = chunk.get("choices", [{}])[0].get("delta", {})

                        # 如果有内容，yield 它
                        if delta.get("content"):
                            yield delta["content"]
                    except json.JSONDecodeError:
                        continue


# ==================== Embedding 模型 ====================

class SiliconFlowEmbeddings:
    """
    SiliconFlow Embedding 封装类

    将文本转换为向量表示
    使用 BAAI/bge-m3 模型，多语言支持效果好

    Embedding 是什么？
    - 把文字/图片转成数字向量（一串浮点数）
    - 语义相近的内容，向量也相近
    - 通过向量相似度计算实现语义检索
    """

    def __init__(self, api_key: str):
        """
        初始化 Embedding 模型

        Args:
            api_key: SiliconFlow API 密钥
        """
        self.api_key = api_key
        # SiliconFlow 的 Embedding API 地址
        self.api_url = "https://api.siliconflow.cn/v1/embeddings"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量将文本转换为向量

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 向量列表，每个向量是浮点数列表
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "BAAI/bge-m3",  # BAAI 开源的 Embedding 模型
            "input": texts  # 批量处理
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                self.api_url,
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()

            # 提取 embeddings 数组
            return [item["embedding"] for item in result["data"]]

    def embed_query(self, text: str) -> List[float]:
        """
        将单个查询文本转换为向量

        Args:
            text: 查询文本

        Returns:
            List[float]: 向量
        """
        return self.embed_documents([text])[0]

    def __call__(self, text: str) -> List[float]:
        """
        使对象可调用，等同于 embed_query

        这样可以直接：embedding("你好")
        """
        return self.embed_query(text)


# ==================== 向量数据库初始化 ====================

def init_vectorstore():
    """
    初始化向量数据库

    流程：
    1. 创建 Embedding 实例
    2. 如果已有持久化数据，加载它
    3. 否则创建新的空向量库
    4. 初始化 QA Chain（检索+生成链）

    向量数据库持久化：
    - Chroma 会将向量数据保存到磁盘
    - 重启容器后数据不会丢失
    - 存储在 PERSIST_DIRECTORY 目录
    """
    global vectorstore, qa_chain

    # 1. 创建 Embedding 实例
    embeddings = SiliconFlowEmbeddings(api_key=SILICONFLOW_API_KEY)

    # 2. 加载或创建向量数据库
    if os.path.exists(PERSIST_DIRECTORY):
        # 已有数据，加载它
        vectorstore = Chroma(
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=embeddings  # 重要：加载时也需要相同的 embedding 函数
        )
        print(f"Loaded existing vectorstore from {PERSIST_DIRECTORY}")
    else:
        # 创建新目录
        os.makedirs(PERSIST_DIRECTORY, exist_ok=True)

        # 创建新的 Chroma 实例
        vectorstore = Chroma(
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=embeddings
        )
        print(f"Created new vectorstore at {PERSIST_DIRECTORY}")

    # 3. 初始化 QA Chain
    # 这是 LangChain 提供的 RAG 链
    llm = create_minimax_llm(
        api_key=MINIMAX_API_KEY,
        api_url=MINIMAX_API_URL,
        model=MINIMAX_CHAT_MODEL
    )

    # 创建检索增强问答链
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",  # 简单链类型，所有上下文塞进一个 prompt
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),  # 检索返回 3 个最相关文档
        return_source_documents=True  # 返回来源文档
    )


def get_qa_chain():
    """
    获取 QA Chain 实例

    懒加载：如果还没有初始化，先初始化

    Returns:
        RetrievalQA: RAG 问答链实例
    """
    global qa_chain
    if qa_chain is None:
        init_vectorstore()
    return qa_chain


def get_vectorstore():
    """
    获取向量数据库实例

    懒加载：如果还没有初始化，先初始化

    Returns:
        Chroma: 向量数据库实例
    """
    global vectorstore
    if vectorstore is None:
        init_vectorstore()
    return vectorstore


# ==================== 文档处理 ====================

def ingest_documents(docs_path: str = "/app/docs") -> dict:
    """
    加载并向量化文档

    流程：
    1. 从指定目录加载所有 .txt 文件
    2. 将长文档切分成小块（chunk）
    3. 对每个 chunk 计算向量
    4. 存储到向量数据库

    为什么要切分？
    - LLM 有上下文长度限制
    - 切分后能更精准检索
    - 避免长文本稀释相关信息

    Args:
        docs_path: 文档目录路径

    Returns:
        dict: 处理结果 {"status": "success/error", "message": "..."}
    """
    global vectorstore

    # 检查目录存在
    if not os.path.exists(docs_path):
        return {"status": "error", "message": f"Directory not found: {docs_path}"}

    # 1. 加载文档
    # DirectoryLoader 会递归加载目录下所有匹配 glob 的文件
    loader = DirectoryLoader(docs_path, glob="**/*.txt", loader_cls=TextLoader)
    documents = loader.load()

    if not documents:
        return {"status": "error", "message": "No documents found"}

    # 2. 切分文档
    # RecursiveCharacterTextSplitter 会递归地按段落/句子切分
    # chunk_size: 每个块的最大字符数
    # chunk_overlap: 相邻块之间的重叠字符数，避免丢失边界信息
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,      # 每个 chunk 约 500 字符
        chunk_overlap=100,   # 相邻 chunk 重叠 100 字符
        length_function=len   # 按字符数计算长度
    )
    texts = text_splitter.split_documents(documents)

    # 3. 嵌入并存储
    # 创建新的 Chroma 实例时会覆盖旧数据
    # 所以每次上传会重建向量库（新文档替换旧文档）
    embeddings = SiliconFlowEmbeddings(api_key=SILICONFLOW_API_KEY)
    vectorstore = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )
    vectorstore.persist()  # 显式保存到磁盘

    return {
        "status": "success",
        "message": f"Ingested {len(texts)} chunks from {len(documents)} documents"
    }


def add_text_to_vectorstore(text: str, metadata: dict = None) -> dict:
    """
    添加单个文本到向量数据库

    用于不需要上传文件的场景

    Args:
        text: 要添加的文本内容
        metadata: 元数据，如 {"source": "manual_input"}

    Returns:
        dict: 处理结果
    """
    global vectorstore

    if vectorstore is None:
        init_vectorstore()

    # 创建 Document 对象
    doc = Document(page_content=text, metadata=metadata or {})

    # 切分文本
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len
    )
    splits = text_splitter.split_documents([doc])

    # 添加到向量库
    vectorstore.add_documents(splits)
    vectorstore.persist()

    return {"status": "success", "message": f"Added {len(splits)} chunks"}


# ==================== RAG 问答 ====================

def query_documents(question: str) -> dict:
    """
    查询文档并生成回答

    这是 RAG 的核心函数：
    1. 检索相关文档
    2. 构建 Prompt
    3. 调用 LLM 生成回答
    4. 返回回答和来源

    注意：这个函数是同步版本，已被 main.py 中的流式版本替代

    Args:
        question: 用户问题

    Returns:
        dict: {"status": "success", "answer": "...", "source_documents": [...]}
    """
    # 获取 QA Chain 并执行
    chain = get_qa_chain()
    result = chain.invoke({"query": question})

    return {
        "status": "success",
        "answer": result["result"],
        "source_documents": [
            {
                # 截取前 200 字符作为预览
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "metadata": doc.metadata
            }
            for doc in result.get("source_documents", [])
        ]
    }
