# Frontend RAG Chatbot

基于 RAG（检索增强生成）的前端技术文档问答系统。

## 功能

- 上传 .txt 格式的文档
- 基于文档内容进行智能问答
- 支持上下文检索

## 技术栈

- **后端**: FastAPI + LangChain + ChromaDB
- **前端**: React + Vite + TailwindCSS
- **LLM**: MiniMax API
- **容器化**: Docker + Docker Compose

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 MiniMax API Key 和 URL
```

### 2. 启动服务

```bash
docker-compose up -d
```

### 3. 访问应用

- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 4. 使用

1. 访问 http://localhost:5173
2. 上传 `docs/react-guide.txt` 测试文档
3. 提问测试，如："React useState 怎么用？"

## 项目结构

```
frontend-rag-chatbot/
├── backend/              # FastAPI 后端
│   ├── main.py           # API 接口
│   ├── rag_chain.py      # RAG 核心逻辑
│   ├── requirements.txt  # Python 依赖
│   └── Dockerfile
├── frontend/             # React 前端
│   ├── src/             # 源代码
│   ├── package.json
│   ├── nginx.conf       # Nginx 配置
│   └── Dockerfile
├── docs/                # 测试文档
├── vectorstore/         # Chroma 数据存储
├── docker-compose.yml
└── .env.example
```

## 开发

### 本地运行后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 本地运行前端

```bash
cd frontend
npm install
npm run dev
```

## 云服务器部署

1. 上传项目到服务器
2. 配置 `.env` 文件
3. 运行 `docker-compose up -d`
4. 配置 Nginx 反向代理（或直接访问 5173 端口）
5. 配置域名和 SSL 证书

## 注意事项

- 确保 MiniMax API Key 有效
- 文档仅支持 .txt 格式
- 向量数据存储在 `vectorstore/` 目录，重启后保留
