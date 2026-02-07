# LLM Chat Application

基于 React + FastAPI + DeepSeek API 的智能对话应用

## 🚀 快速开始

### 1. 配置环境变量

```bash
# 复制环境变量示例文件
cp backend/.env.example backend/.env

# 编辑 backend/.env，填入你的 DeepSeek API Key
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 2. 启动应用（Docker）

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 3. 访问应用

- **前端界面**：http://localhost:5173
- **后端 API**：http://localhost:8000
- **API 文档**：http://localhost:8000/docs

## 📁 项目结构

```
llm-chat-app/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── main.py       # 主应用入口
│   │   └── routers/
│   │       └── chat.py   # 聊天 API 路由
│   ├── Dockerfile        # 后端 Docker 镜像
│   ├── requirements.txt  # Python 依赖
│   └── .env.example      # 环境变量示例
├── frontend/             # React + Vite 前端
│   ├── src/
│   │   ├── components/
│   │   │   └── Chat.jsx  # 聊天组件
│   │   ├── App.jsx       # 主应用组件
│   │   ├── main.jsx      # 入口文件
│   │   └── index.css     # 全局样式
│   ├── index.html        # HTML 模板
│   ├── package.json      # Node.js 依赖
│   └── vite.config.js    # Vite 配置
└── docker-compose.yml    # Docker Compose 配置
```

## 🔧 API 接口

### POST /api/chat

发送消息给 DeepSeek 大模型

**请求体：**
```json
{
  "prompt": "你好，请介绍一下自己",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**响应：**
```json
{
  "response": "你好！我是 DeepSeek...",
  "model": "deepseek-chat",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  }
}
```

## 🛠️ 开发模式

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

### 后端开发

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 🔑 获取 DeepSeek API Key

1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com/)
2. 注册账号
3. 在控制台创建 API Key
4. 将 Key 填入 `backend/.env` 文件

## 📝 License

MIT