# LLM Chat App - Agent Guidelines

## Quick Start

### 启动后端服务

**重要**：后端必须在新窗口启动，否则会因超时终止！

在 backend 目录下启动：

```bash
cd llm-chat-app/backend
start "" "C:/Users/user/Desktop/llm/llm-chat-app/backend/venv/Scripts/uvicorn.exe" app.main:app --reload --port 8000 --host 0.0.0.0
```

或使用 Python 启动（效果相同）：

```bash
cd llm-chat-app/backend
start "" "venv/Scripts/python.exe" -c "import uvicorn; uvicorn.run('app.main:app',host='0.0.0.0',port=8000,reload=True)"
```

**验证后端是否运行**：
```bash
curl http://localhost:8000/
```

### 启动前端

在 frontend 目录下启动：

```bash
cd llm-chat-app/frontend
npm run dev
```

**注意**：如果端口 5173 被占用，Vite 会自动切换到其他端口（如 5174）。

## Access URLs

- **前端界面**：http://localhost:5173（如果被占用会自动切换端口）
- **后端 API**：http://localhost:8000
- **API 文档**：http://localhost:8000/docs

## 自动启动流程

**必须使用 `start` 命令启动后端**，否则进程会因超时终止！

### 启动后端（在新窗口）

```bash
cd llm-chat-app/backend
start "" "C:/Users/user/Desktop/llm/llm-chat-app/backend/venv/Scripts/uvicorn.exe" app.main:app --reload --port 8000 --host 0.0.0.0
```

等待看到 `Application startup complete` 消息。

## Troubleshooting

### "Failed to fetch" Error
- **Cause**: 后端服务未运行或已终止
- **Solution**: 使用 `start` 命令重新启动后端
  ```bash
  cd llm-chat-app/backend
  start "" "C:/Users/user/Desktop/llm/llm-chat-app/backend/venv/Scripts/uvicorn.exe" app.main:app --reload --port 8000 --host 0.0.0.0
  ```
- **验证**: `curl http://localhost:8000/`

### 后端进程超时终止
- **Cause**: 直接在 Bash 中运行 uvicorn，命令超时后进程被终止
- **Solution**: 必须使用 `start` 命令在新窗口启动后端

### CORS Errors
- **Cause**: Frontend URL not in CORS_ORIGINS
- **Fix**: Update `backend/.env` CORS_ORIGINS to include frontend URL
- **Example**: If前端在5174端口，确保 CORS_ORIGINS 包含 `http://localhost:5174`

### Port Conflicts

**后端端口 8000 被占用：**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**前端端口被占用：**
- Vite 会自动切换到下一个可用端口（5174, 5175, ...）
- 检查启动时的输出获取实际端口号

## Project Structure

```
llm-chat-app/
├── backend/
│   ├── app/main.py       # FastAPI entry
│   ├── app/routers/chat.py
│   ├── requirements.txt
│   ├── .env             # API keys
│   └── venv/            # Python virtual environment
└── frontend/
    ├── src/App.jsx
    ├── src/components/Chat.jsx
    └── package.json
```

## Important Notes

1. **必须使用完整路径启动 uvicorn**：Windows 下的 Git Bash 需要 `'C:/Users/.../uvicorn.exe'` 格式
2. **启动后端前必须 cd 到 backend 目录**：否则找不到 `app` 模块
3. **后端启动成功标志**：看到 `Application startup complete` 消息
4. **DeepSeek API key** 已配置在 `backend/.env` 中
5. **前端代理** 配置为转发 `/api` 到 http://localhost:8000

## Verification Commands

```bash
# 检查后端是否运行
curl http://localhost:8000/

# 检查前端是否运行
curl http://localhost:5173

# 或实际使用的端口
curl http://localhost:5174
```

## 验证清单

- [ ] 后端使用 `start` 命令在新窗口启动
- [ ] 看到 "Application startup complete" 消息
- [ ] 前端显示 "VITE ready"
- [ ] 可以访问 http://localhost:8000/
- [ ] 可以访问前端地址
- [ ] 可以访问 http://localhost:8000/docs

## Stop Servers

在运行服务器的终端中按 `Ctrl+C` 停止服务。


please read SKILL.md