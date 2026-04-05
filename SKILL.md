# LLM Chat App Development Skill

⚠️ **关键教训：后端进程超时问题**
> 直接在 Bash 中运行 uvicorn 会因工具超时而自动终止（通常 15-30 秒），导致 "Failed to fetch" 错误。
> **解决方案：始终使用 `start` 命令在新窗口启动后端，或使用后台进程 `&` 运行。**

This skill provides workflows for managing the LLM Chat Application development environment.

## Environment Overview

- **Frontend**: React + Vite, default port 5173 (auto-switch if occupied)
- **Backend**: FastAPI + Uvicorn, port 8000
- **Location**: `llm-chat-app/` directory
- **Python Env**: `backend/venv/` (Windows)

## Quick Commands

### Start Development Servers

⚠️ **警告：后端启动方式至关重要**

**❌ 错误做法**（bash 超时会杀死进程）：
```bash
# 不要使用这种方式 - 15-30秒后进程会被终止
./venv/Scripts/python.exe -c "import uvicorn; uvicorn.run('app.main:app', ...)"
```

**✅ 正确做法**（进程独立运行，不会超时）：

**重要**：后端必须使用 `start` 命令在新窗口启动，否则会因 bash 超时终止！

#### 启动后端（必须在新窗口）

```bash
cd llm-chat-app/backend
start "" "C:/Users/user/Desktop/llm/llm-chat-app/backend/venv/Scripts/uvicorn.exe" app.main:app --reload --port 8000 --host 0.0.0.0
```

等待看到 `Application startup complete` 消息。

#### 启动前端

```bash
cd llm-chat-app/frontend
npm run dev
```

**验证**：
```bash
curl http://localhost:8000/  # 检查后端
curl http://localhost:5173  # 检查前端
```

### Stop Servers

Press `Ctrl+C` in the terminal where the server is running.

To force kill on Windows:
```bash
# Find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## Common Issues & Solutions

### 1. "Failed to fetch" 错误
**Cause**: 后端服务未运行（最常见原因）
**Solution**: 使用 `start` 命令启动后端
```bash
cd llm-chat-app/backend
start "" "C:/Users/user/Desktop/llm/llm-chat-app/backend/venv/Scripts/uvicorn.exe" app.main:app --reload --port 8000 --host 0.0.0.0
```
**验证**: `curl http://localhost:8000/`

### 2. "No module named 'app'" Error
**Cause**: Not running from backend directory
**Solution**: 
```bash
cd backend
# Then run uvicorn
```

### 3. 后端进程超时终止 ⭐ 重要教训
**Cause**: 
- 直接在 Bash 中运行 uvicorn（如 `./venv/Scripts/python.exe -c "..."`），bash 工具会设置超时限制
- 默认 15-30 秒后进程被自动终止
- 结果是：后端启动成功 → 15秒后消失 → 前端显示 "Failed to fetch"

**Solution**: 
- **必须**使用 `start` 命令在新窗口启动后端，让进程独立于 bash 会话运行
- 或者使用后台进程 `&` 符号
- 或使用 Docker 容器化运行

**错误示例**（不要这样做）：
```bash
# ❌ 错误：bash 超时会杀死进程
./venv/Scripts/python.exe -c "import uvicorn; uvicorn.run(...)"  # 15秒后终止
```

**正确示例**：
```bash
# ✅ 正确：使用 start 在新窗口启动
start "" "D:/llm/llm-chat-app/backend/venv/Scripts/uvicorn.exe" app.main:app --reload --port 8000 --host 0.0.0.0

# ✅ 或：后台运行（当前会话可用）
./venv/Scripts/uvicorn.exe app.main:app --reload --port 8000 --host 0.0.0.0 > server.log 2>&1 &
```

### 4. Port 8000 Already in Use
**Solution**:
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### 4. Frontend Port Changed (e.g., 5174 instead of 5173)
**Solution**: This is normal when 5173 is occupied. Check CORS_ORIGINS in `backend/.env`:
```
CORS_ORIGINS=http://localhost:5173,http://localhost:5174,http://frontend:5173
```

### 5. Environment Variables Not Loaded
**Solution**: Ensure `.env` file exists in backend directory with:
- `DEEPSEEK_API_KEY=sk-...`
- `DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions`
- `CORS_ORIGINS=http://localhost:5173,http://localhost:5174`

## API Endpoints

- `GET /` - Root message
- `GET /health` - Health check
- `GET /docs` - Swagger UI documentation (http://localhost:8000/docs)
- `POST /api/chat` - Send message to DeepSeek

## Complete Startup Workflow

When user says "启动项目" or "启动服务":

1. **Check current status**:
   ```bash
   curl -s http://localhost:8000/ && echo "Backend OK" || echo "Backend not running"
   curl -s http://localhost:5173/ | head -1 && echo "Frontend OK" || echo "Frontend not running"
   ```

2. **Start Backend** (if not running) - 必须在新窗口启动：
   ```bash
   cd llm-chat-app/backend
   start "" "C:/Users/user/Desktop/llm/llm-chat-app/backend/venv/Scripts/uvicorn.exe" app.main:app --reload --port 8000 --host 0.0.0.0
   ```
   Wait for "Application startup complete"

3. **Start Frontend** (if not running):
   ```bash
   cd llm-chat-app/frontend
   npm run dev
   ```
   Note the port (5173 or 5174)

4. **Report URLs**:
   - Backend: http://localhost:8000
   - Frontend: http://localhost:5173 (or actual port)
   - API Docs: http://localhost:8000/docs

## Verification Checklist

- [ ] Backend started in new window with `start` command
- [ ] Backend shows "Application startup complete"
- [ ] Frontend shows "VITE ready"
- [ ] Can access http://localhost:8000/
- [ ] Can access frontend URL
- [ ] Can access http://localhost:8000/docs

## Windows-Specific Notes

- Use forward slashes in paths: `C:/Users/...` not `C:\Users\...`
- Quote paths if they contain spaces
- Use single quotes around full command paths in Git Bash
- Virtual environment is at `backend/venv/`
- Python executable: `backend/venv/Scripts/python.exe`
- Uvicorn executable: `backend/venv/Scripts/uvicorn.exe`


please read AGENTS.md
