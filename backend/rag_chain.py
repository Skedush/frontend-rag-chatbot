import os
from typing import List, Optional
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain_core.runnables import RunnableLambda
import httpx

# 配置
VECTORSTORE_DIR = os.environ.get("VECTORSTORE_DIR", "/app/vectorstore")
PERSIST_DIRECTORY = os.path.join(VECTORSTORE_DIR, "chroma_db")
MINIMAX_API_URL = os.environ.get("MINIMAX_API_URL", "")
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_CHAT_MODEL = os.environ.get("MINIMAX_CHAT_MODEL", "MiniMax-M2.7")
JINA_API_KEY = os.environ.get("JINA_API_KEY", "")

# 全局向量数据库实例
vectorstore: Optional[Chroma] = None
qa_chain: Optional[RetrievalQA] = None


def create_minimax_llm(api_key: str, api_url: str, model: str):
    """创建 MiniMax LLM"""
    def call(prompt, **kwargs) -> str:
        # 将 prompt 转换为字符串（可能是 StringPromptValue 对象）
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
    """MiniMax 流式聊天"""
    import json

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": True
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", f"{api_url}/v1/chat/completions", headers=headers, json=data) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        if delta.get("content"):
                            yield delta["content"]
                    except json.JSONDecodeError:
                        continue


class JinaEmbeddings:
    """Jina AI Embedding 封装"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.jina.ai/v1/embeddings"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {"model": "jina-embeddings-v3", "input": texts}
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                self.api_url,
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            return [item["embedding"] for item in result["data"]]

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

    def __call__(self, text: str) -> List[float]:
        return self.embed_query(text)


def init_vectorstore():
    """初始化向量数据库"""
    global vectorstore, qa_chain

    embeddings = JinaEmbeddings(api_key=JINA_API_KEY)

    # 加载或创建向量数据库
    if os.path.exists(PERSIST_DIRECTORY):
        vectorstore = Chroma(
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=embeddings
        )
        print(f"Loaded existing vectorstore from {PERSIST_DIRECTORY}")
    else:
        os.makedirs(PERSIST_DIRECTORY, exist_ok=True)
        vectorstore = Chroma(
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=embeddings
        )
        print(f"Created new vectorstore at {PERSIST_DIRECTORY}")

    # 初始化 QA Chain
    llm = create_minimax_llm(
        api_key=MINIMAX_API_KEY,
        api_url=MINIMAX_API_URL,
        model=MINIMAX_CHAT_MODEL
    )
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )


def get_qa_chain():
    """获取 QA chain"""
    global qa_chain
    if qa_chain is None:
        init_vectorstore()
    return qa_chain


def get_vectorstore():
    """获取向量数据库"""
    global vectorstore
    if vectorstore is None:
        init_vectorstore()
    return vectorstore


def ingest_documents(docs_path: str = "/app/docs") -> dict:
    """加载并向量化文档"""
    global vectorstore

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

    # 嵌入并存储
    embeddings = JinaEmbeddings(api_key=JINA_API_KEY)
    vectorstore = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )
    vectorstore.persist()

    return {
        "status": "success",
        "message": f"Ingested {len(texts)} chunks from {len(documents)} documents"
    }


def add_text_to_vectorstore(text: str, metadata: dict = None) -> dict:
    """添加单个文本到向量数据库"""
    global vectorstore

    if vectorstore is None:
        init_vectorstore()

    doc = Document(page_content=text, metadata=metadata or {})
    texts = [doc]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len
    )
    splits = text_splitter.split_documents(texts)

    vectorstore.add_documents(splits)
    vectorstore.persist()

    return {"status": "success", "message": f"Added {len(splits)} chunks"}


def query_documents(question: str) -> dict:
    """查询文档"""
    chain = get_qa_chain()
    result = chain.invoke({"query": question})

    return {
        "status": "success",
        "answer": result["result"],
        "source_documents": [
            {
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "metadata": doc.metadata
            }
            for doc in result.get("source_documents", [])
        ]
    }
