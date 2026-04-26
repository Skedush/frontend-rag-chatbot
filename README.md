# Frontend RAG Chatbot

基于 RAG（检索增强生成）的技术文档智能问答系统，支持 React 和 Vue 3 双前端。

## 功能

- 上传 .txt 格式的文档
- 基于文档内容进行智能问答（流式输出）
- Markdown 渲染 + 代码高亮
- 支持上下文检索

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + ChromaDB + MiniMax LLM |
| Embedding | SiliconFlow (BAAI/bge-m3) |
| React 前端 | React 18 + Vite + TailwindCSS |
| Vue 前端 | Vue 3 + Element Plus + Pinia + Vue Router |
| 容器化 | Docker + Docker Compose |

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Keys
```

### 2. 启动服务（生产环境）

```bash
docker-compose up -d --build
```

### 3. 启动开发环境（热更新）

```bash
docker-compose -f docker-compose.dev.yml up -d --build
```

### 4. 访问应用

| 服务 | 地址 |
|------|------|
| React 前端 | http://localhost:5173 |
| **Vue 前端** | **http://localhost:3000** |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |

## 项目结构

```
frontend-rag-chatbot/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/               # API 路由 (chat, upload, health)
│   │   ├── core/              # 配置 (settings.py)
│   │   ├── models/            # Pydantic 模型
│   │   ├── services/          # 业务逻辑 (embedding, llm)
│   │   └── utils/             # 工具函数
│   ├── main.py                # 应用入口
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                   # React 前端 (端口 5173)
│   ├── src/
│   ├── nginx.conf
│   └── Dockerfile
│
├── vue-frontend/              # Vue 3 前端 (端口 3000)
│   ├── src/
│   │   ├── api/              # API 服务层
│   │   ├── stores/            # Pinia 状态管理
│   │   ├── views/             # 页面视图
│   │   └── components/        # UI 组件
│   ├── vite.config.js
│   ├── Dockerfile            # 生产环境
│   └── Dockerfile.dev        # 开发环境
│
├── docs/                      # 测试文档
├── vectorstore/               # Chroma 向量数据库
├── docker-compose.yml         # 生产环境
├── docker-compose.dev.yml     # 开发环境
└── .env.example
```

## 开发

### 本地运行后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 本地运行 React 前端

```bash
cd frontend
npm install
npm run dev
```

### 本地运行 Vue 前端

```bash
cd vue-frontend
pnpm install
pnpm run dev
```

## 云服务器部署

1. 上传项目到服务器
2. 配置 `.env` 文件
3. 生产环境部署：
   ```bash
   docker-compose up -d --build
   ```
4. 配置 Nginx 反向代理 + SSL 证书

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/chat` | POST | 流式问答 |
| `/api/upload` | POST | 上传文档 |
| `/api/health` | GET | 健康检查 |

## 注意事项

- 文档仅支持 .txt 格式
- 向量数据存储在 `vectorstore/` 目录
- Docker 开发环境修改代码后需重建容器
- Vue 前端使用 pnpm 作为包管理器
