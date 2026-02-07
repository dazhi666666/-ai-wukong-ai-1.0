# LLM Chat App Docker 生产环境部署

## 📋 配置文件说明

### 1. `docker-compose.prod.yml`
生产环境 Docker Compose 配置：
- **nginx**: 提供前端静态文件和反向代理
- **backend**: FastAPI 后端服务
- 包含健康检查和资源限制

### 2. `frontend/Dockerfile.prod`
前端生产环境 Dockerfile：
- 使用多阶段构建减小镜像体积
- 基于 Node.js 构建，Nginx 提供服务

### 3. `frontend/nginx.conf`
Nginx 配置文件：
- 提供前端静态文件
- 反向代理 API 请求到后端
- 健康检查端点

### 4. `deploy-prod.sh`
自动化部署脚本，支持：
- 部署、日志查看、停止、重启、更新、状态检查

---

## 🚀 快速部署步骤

### 方式一：使用自动化脚本（推荐）

```bash
# 1. SSH 登录服务器
ssh root@8.130.209.117

# 2. 克隆代码
cd /opt
git clone https://github.com/dazhi666666/llm-chat-app.git
cd llm-chat-app

# 3. 配置环境变量
cat > backend/.env << 'EOF'
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_MODEL=deepseek-chat
EOF

# 4. 添加脚本执行权限
chmod +x deploy-prod.sh

# 5. 执行部署
./deploy-prod.sh
```

### 方式二：手动部署

```bash
# 1. 登录服务器并克隆代码
ssh root@8.130.209.117
cd /opt
git clone https://github.com/dazhi666666/llm-chat-app.git
cd llm-chat-app

# 2. 配置环境变量
vim backend/.env
# 填入您的 DeepSeek API Key

# 3. 开放防火墙端口
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --reload

# 4. 启动服务
docker-compose -f docker-compose.prod.yml up -d --build

# 5. 检查状态
docker-compose -f docker-compose.prod.yml ps
curl http://localhost/health
```

---

## 🔧 部署脚本使用

```bash
# 部署应用
./deploy-prod.sh deploy

# 查看日志
./deploy-prod.sh logs

# 停止服务
./deploy-prod.sh stop

# 重启服务
./deploy-prod.sh restart

# 更新代码并重新部署
./deploy-prod.sh update

# 查看服务状态
./deploy-prod.sh status
```

---

## 🌐 访问应用

部署完成后：
- **前端界面**: http://8.130.209.117
- **API 接口**: http://8.130.209.117/api
- **API 文档**: http://8.130.209.117/api/docs (通过 Nginx 代理)

---

## 📊 架构说明

```
┌─────────────────┐
│     用户        │
└────────┬────────┘
         │ HTTP:80
         ▼
┌─────────────────┐
│  Nginx (容器)   │  ┌──────────────┐
│  - 前端静态文件  │  │ 前端构建产物  │
│  - 反向代理     │  └──────────────┘
└────────┬────────┘
         │ API 请求
         ▼
┌─────────────────┐
│  Backend (容器) │
│  FastAPI:8000   │
│  - 聊天接口     │
│  - DeepSeek API │
└─────────────────┘
```

---

## 🔍 故障排查

### 1. 查看容器状态
```bash
docker-compose -f docker-compose.prod.yml ps
```

### 2. 查看日志
```bash
# 所有服务
docker-compose -f docker-compose.prod.yml logs -f

# 仅后端
docker-compose -f docker-compose.prod.yml logs -f backend

# 仅 Nginx
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### 3. 测试 API
```bash
# 测试后端健康检查
curl http://localhost:8000/health

# 测试聊天接口
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "你好"}'
```

### 4. 进入容器调试
```bash
# 进入后端容器
docker exec -it llm-chat-backend /bin/sh

# 进入 Nginx 容器
docker exec -it llm-chat-nginx /bin/sh
```

### 5. 重新构建
```bash
# 完全重建
docker-compose -f docker-compose.prod.yml down
docker system prune -f
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 🔄 更新部署

当代码更新后，执行：

```bash
# 使用脚本自动更新
./deploy-prod.sh update

# 或手动更新
git pull
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## ⚠️ 重要提示

1. **API Key**: 永远不要将包含真实 API Key 的 `.env` 文件提交到 Git
2. **端口**: 生产环境只暴露 80 端口，后端 8000 不直接暴露
3. **安全**: 建议配置 HTTPS 和域名
4. **监控**: 可以配置健康检查告警

---

## 📞 技术支持

如有问题，请查看：
- GitHub Issues: https://github.com/dazhi666666/llm-chat-app/issues
- DeepSeek 文档: https://platform.deepseek.com/
