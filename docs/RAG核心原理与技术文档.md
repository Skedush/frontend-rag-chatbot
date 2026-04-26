# RAG 核心原理与技术文档

## 1. RAG 概述

**RAG = Retrieval-Augmented Generation（检索增强生成）**

是一种结合信息检索与语言模型生成的技术，让 AI 基于私有/特定文档回答问题，而不是仅靠模型自的知识。

### 为什么需要 RAG？

| 问题                     | RAG 解决方案                 |
| ---------------------- | ------------------------ |
| LLM 知识有截止日期            | 实时检索最新文档                 |
| LLM 不知道私有数据            | 检索用户上传的文档                |
| LLM 容易 hallucinate（瞎编） | 基于检索到的真实内容生成             |
| 无法追溯答案来源               | 返回 source\_documents 可验证 |

### RAG 工作流程

```
用户问题
    │
    ▼
┌─────────────────┐
│  1. Embedding   │ ← 把用户问题转成向量
│  (向量化)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. 相似度检索   │ ← 在向量数据库中找最相关的文档块
│  (Vector Search) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  3. 构建 Prompt │ ← 把检索到的内容塞进 system prompt
│  (Context)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  4. LLM 生成    │ ← 让 AI 基于文档回答问题
│  (Generation)   │
└────────┬────────┘
         │
         ▼
     返回答案 + 来源
```

***

## 2. 向量数据库

### 2.1 什么是向量（Embedding）

把文字/图片/语音转成一串数字数组（向量），用于计算相似度。

**例子：**

- "苹果水果" → \[0.12, -0.34, 0.78, ...]
- "apple fruit" → \[0.11, -0.33, 0.79, ...]  // 相似！

语义相近的内容，向量也相近。

### 2.2 主流向量数据库对比

| 数据库          | 特点           | 适用场景        |
| ------------ | ------------ | ----------- |
| **Chroma**   | 轻量级、易上手、本地运行 | Demo / 快速开发 |
| **Milvus**   | 生产级、分布式、高并发  | 大规模数据、企业级   |
| **Pinecone** | 云原生、免运维、SaaS | 不想自己运维      |
| **Weaviate** | 支持多模态（文本+图片） | 多模态 RAG     |

### 2.3 Chroma 核心概念

```python
import chromadb

# 创建向量库
client = chromadb.Client()
collection = client.create_collection("my_docs")

# 添加文档（会自动 Embedding）
collection.add(
    documents=["React useState 的用法", "Vue3 响应式原理"],
    ids=["doc1", "doc2"]
)

# 检索
results = collection.query(
    query_texts=["React Hook 怎么用？"],
    n_results=2
)
```

***

## 3. Embedding 模型

### 3.1 作用

把文本转成向量，是 RAG 的第一步。

### 3.2 常见模型

| 模型                     | 提供商     | 特点     |
| ---------------------- | ------- | ------ |
| text-embedding-ada-002 | OpenAI  | 效果好，贵  |
| embedding-01           | MiniMax | 性价比高   |
| jina-embeddings-v3     | Jina AI | 开源、多语言 |
| BGE                    | 国产开源    | 中文优化   |

### 3.3 Embedding 调用示例

```python
import requests

response = requests.post(
    "https://api.jina.ai/v1/embeddings",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "model": "jina-embeddings-v3",
        "input": ["需要嵌入的文本"]
    }
)
vector = response.json()["data"][0]["embedding"]
```

***

## 4. LangChain 基础

LangChain 是一个 LLM 应用开发框架，简化 RAG、Agent、Memory 等功能的实现。

### 4.1 核心组件

| 组件                  | 作用                        |
| ------------------- | ------------------------- |
| **Document Loader** | 加载各种格式文档（PDF、Word、TXT...） |
| **Text Splitter**   | 把长文档切成小块                  |
| **Embedding**       | 向量化文本                     |
| **VectorStore**     | 存储向量                      |
| **Retriever**       | 检索相关文档                    |
| **Chain**           | 把多个步骤串起来                  |
| **Memory**          | 对话历史记忆                    |

### 4.2 简化版 RAG 实现

```python
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.schema import Document

# 1. 加载文档
loader = TextLoader("react-guide.txt")
documents = loader.load()

# 2. 切分文档
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
texts = splitter.split_documents(documents)

# 3. 向量存储
vectorstore = Chroma.from_documents(texts, embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 4. 构建 QA Chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",  # 把所有检索到的文档塞进一个 prompt
    retriever=retriever,
    return_source_documents=True  # 返回来源
)

# 5. 问答
result = qa_chain.invoke({"query": "useState 怎么用？"})
print(result["result"])           # 答案
print(result["source_documents"])  # 来源
```

***

## 5. 流式输出（Streaming）

### 5.1 什么是流式输出

传统：等 AI **全部生成完**再返回（慢）
流式：AI **生成一个字**就返回一个字（快，即时感）

### 5.2 SSE（Server-Sent Events）协议

后端 → 前端 单向推送数据，常用于流式输出。

**SSE 格式：**

```
data: 你好
data: ，世界

data: [DONE]
```

### 5.3 后端流式实现（FastAPI）

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

@app.post("/chat")
async def chat(question: str):
    async def generate():
        # 假设 LLM 返回流式数据
        async for chunk in llm.astream(question):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

### 5.4 前端处理流

```javascript
const response = await fetch("/api/chat", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ question: "..." })
})

const reader = response.body.getReader()
const decoder = new TextDecoder()

while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value, { stream: true })
    // 解析 SSE: data: xxx\n\n
    const lines = chunk.split("\n")
    for (const line of lines) {
        if (line.startsWith("data: ")) {
            console.log(line.slice(6)) // 拿到数据
        }
    }
}
```

***

## 6. MiniMax API 调用

### 6.1 非流式调用

```python
import httpx

response = httpx.post(
    "https://api.minimaxi.com/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={
        "model": "MiniMax-M2.7",
        "messages": [
            {"role": "user", "content": "你好"}
        ]
    }
)
answer = response.json()["choices"][0]["message"]["content"]
```

### 6.2 流式调用

```python
import httpx
import json

response = httpx.stream(
    "POST",
    "https://api.minimaxi.com/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={
        "model": "MiniMax-M2.7",
        "messages": [{"role": "user", "content": "你好"}],
        "stream": True
    }
)

for line in response.iter_lines():
    if line.startswith("data: "):
        data = line[6:]
        if data == "[DONE]":
            break
        chunk = json.loads(data)
        delta = chunk["choices"][0]["delta"]["content"]
        print(delta, end="", flush=True)
```

***

## 7. 完整 RAG 项目架构

```
┌─────────────────────────────────────────────────────┐
│                     前端 (React)                     │
│         http://localhost:5173                        │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────┐
│                   FastAPI 后端                       │
│                  /api/chat (流式)                    │
│                  /api/upload                         │
└────────┬──────────────────────────────┬─────────────┘
         │                              │
┌────────▼────────┐           ┌─────────▼──────────┐
│   用户上传文档   │           │  向量数据库 (Chroma) │
│  存储到 /docs   │           │   /app/vectorstore  │
└─────────────────┘           └─────────┬──────────┘
                                        │
                        ┌───────────────┴───────────────┐
                        │                               │
               ┌────────▼────────┐         ┌──────────▼─────────┐
               │  Jina Embedding │         │   MiniMax API      │
               │   (向量化)       │         │   (LLM 生成)       │
               └─────────────────┘         └───────────────────┘
```

***

## 8. 学习路径建议

### 入门（1-2周）

1. 理解 RAG 原理 ✓（本文档）
2. 学会调用 LLM API（非流式 + 流式）✓
3. 掌握 Chroma 基本用法 ✓
4. 能独立实现一个简单 RAG

### 进阶（2-4周）

1. 学习 LangChain 高级用法（Chain、Agent）
2. 理解对话 Memory 原理
3. 接入生产级向量库（Milvus/Pinecone）
4. Prompt Engineering 技巧

### 高级（持续学习）

1. Agent（自主决策 + 工具调用）
2. 多模态 RAG（文本+图片）
3. RAG 优化（召回率、重排序）
4. 微调 Embedding 模型

***

## 9. 面试常见问题

**Q: RAG 和 Fine-tuning 的区别？**

- RAG：检索外部知识，实时性高，可解释性强
- Fine-tuning：用数据微调模型，知识内化，响应更快但更新成本高

**Q: 向量检索为什么比关键词检索好？**

- 关键词检索（TF-IDF/BM25）只能匹配字面
- 向量检索能匹配语义相似的内容

**Q: 如何提升 RAG 召回率？**

- 更好的 Embedding 模型
- 优化分块策略（chunk\_size）
- 混合检索（向量+关键词）
- 重排序（Reranker）

**Q: LangChain 的 stuff、map\_reduce、refine 区别？**

- stuff：把所有文档塞进一个 prompt（快，适合少量文档）
- map\_reduce：每个文档单独处理，再汇总（适合大量文档）
- refine：逐文档迭代优化答案（质量高，速度慢）

