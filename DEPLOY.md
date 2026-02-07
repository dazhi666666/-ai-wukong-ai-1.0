# LLM Chat App 部署指南

## 🚀 快速部署步骤

### 1. 上传代码到 GitHub

**在本地执行：**
```bash
cd C:\Users\user\Desktop\llm\llm-chat-app

# 如果还没推送，执行：
git remote add origin https://github.com/dazhi666666/llm-chat-app.git
git branch -M main

# 推送时会要求输入 GitHub 用户名和密码（或 Token）
git push -u origin main
```

**注意：** GitHub 已不支持密码登录，需要创建 Personal Access Token：
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 勾选 `repo` 权限
4. 复制 Token（只显示一次）
5. 推送时输入 Token 作为密码

---

### 2. 服务器部署

**SSH 登录服务器：**
```bash
ssh root@8.130.209.117
```

**执行部署：**
```bash
cd /opt

# 下载部署脚本
curl -O https://raw.githubusercontent.com/dazhi666666/llm-chat-app/main/deploy.sh
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh
```

**或手动部署：**
```bash
# 1. 安装 Git 和 Docker
yum install -y git docker
systemctl start docker
systemctl enable docker

# 2. 克隆代码
cd /opt
git clone https://github.com/dazhi666666/llm-chat-app.git
cd llm-chat-app

# 3. 创建后端 .env 文件（输入你的 API Key）
cat > backend/.env << 'EOF'
DEEPSEEK_API_KEY=sk-a3c2e93e85b64ee5bf9165e707e3211a
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_MODEL=deepseek-chat
BACKEND_PORT=8000
CORS_ORIGINS=http://8.130.209.117:8080
EOF

# 4. 开放防火墙端口
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --permanent --add-port=7000/tcp
firewall-cmd --reload

# 5. 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 6. 检查状态
docker-compose -f docker-compose.prod.yml ps
curl http://localhost:7000/health
```

---

### 3. 访问应用

部署完成后访问：
- **前端界面**：http://8.130.209.117:8080
- **后端 API**：http://8.130.209.117:7000
- **API 文档**：http://8.130.209.117:7000/docs

---

## 🔧 常用命令

```bash
# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看后端日志
docker-compose -f docker-compose.prod.yml logs -f backend

# 查看前端日志
docker-compose -f docker-compose.prod.yml logs -f frontend

# 停止服务
docker-compose -f docker-compose.prod.yml down

# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 重新构建并启动
docker-compose -f docker-compose.prod.yml up -d --build

# 进入容器调试
docker exec -it llm-chat-backend /bin/sh
docker exec -it llm-chat-frontend /bin/sh
```

---

## 🛠️ 故障排查

### 问题 1：端口被占用
```bash
# 查看占用端口的进程
netstat -tlnp | grep 8080
netstat -tlnp | grep 7000

# 停止占用进程
kill -9 <PID>
```

### 问题 2：防火墙阻止访问
```bash
# 检查防火墙状态
firewall-cmd --state

# 查看开放的端口
firewall-cmd --list-ports

# 临时关闭防火墙（测试用）
systemctl stop firewalld

# 永久关闭（不推荐）
systemctl disable firewalld
```

### 问题 3：DeepSeek API 调用失败
```bash
# 检查 API Key 是否配置正确
docker-compose -f docker-compose.prod.yml exec backend env | grep DEEPSEEK

# 查看后端详细日志
docker-compose -f docker-compose.prod.yml logs backend | tail -50
```

### 问题 4：前端无法连接后端
```bash
# 测试后端是否正常运行
curl http://localhost:7000/health

# 测试 API 接口
curl -X POST http://localhost:7000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "你好"}'
```

---

## 🔄 更新部署

**代码更新后重新部署：**
```bash
cd /opt/llm-chat-app
git pull
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 📝 配置文件说明

### docker-compose.prod.yml
- 后端端口：7000（映射到容器内 8000）
- 前端端口：8080（映射到容器内 5173）
- 使用生产环境变量
- 自动重启策略

### backend/.env
- 包含 DeepSeek API Key（敏感信息，不要上传 GitHub）
- CORS 配置允许前端跨域访问

### 端口映射关系
| 服务 | 容器内端口 | 宿主机端口 | 访问地址 |
|------|-----------|-----------|----------|
| Backend | 8000 | 7000 | http://8.130.209.117:7000 |
| Frontend | 5173 | 8080 | http://8.130.209.117:8080 |

---

## 🎉 部署成功标志

访问 http://8.130.209.117:8080 能看到：
- 🤖 LLM Chat 标题
- 输入框和发送按钮
- 正常与 DeepSeek 对话

如果有问题，检查：
1. Docker 是否运行：`docker ps`
2. 端口是否开放：`firewall-cmd --list-ports`
3. 日志是否有错误：`docker-compose logs`

---

**项目地址：** https://github.com/dazhi666666/llm-chat-app  
**部署时间：** $(date)  
**服务器：** 8.130.209.117