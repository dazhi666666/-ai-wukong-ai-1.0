# LLM Chat App 部署包使用说明

## 📦 快速部署（3 步骤）

### 步骤 1：生成部署包

在 Windows 上执行：
```bash
cd C:\Users\user\Desktop\llm\llm-chat-app

# 手动打包（推荐）
tar -czvf llm-chat-app-deploy.tar.gz --exclude='.git' --exclude='backend/.env' --exclude='frontend/node_modules' --exclude='backend/venv' --exclude='__pycache__' --exclude='*.pyc' --exclude='test_api.py' --exclude='api_response.json' .
```

### 步骤 2：上传到服务器

```bash
# 在 Windows PowerShell 或 CMD 中执行
scp C:\Users\user\Desktop\llm\llm-chat-app\llm-chat-app-deploy.tar.gz root@8.130.209.117:/opt/
```

**如果没有 scp 命令，使用 FileZilla：**
1. 下载 FileZilla
2. 连接服务器：sftp://root@8.130.209.117
3. 上传文件到 /opt/ 目录

### 步骤 3：服务器部署

```bash
# SSH 登录服务器
ssh root@8.130.209.117

# 解压并部署
cd /opt
tar -xzvf llm-chat-app-deploy.tar.gz
cd llm-chat-app

# 创建环境变量（输入你的 API Key）
cat > backend/.env << 'EOF'
DEEPSEEK_API_KEY=sk-a3c2e93e85b64ee5bf9165e707e3211a
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_MODEL=deepseek-chat
BACKEND_PORT=8000
CORS_ORIGINS=http://8.130.209.117:8080
EOF

# 安装 Docker（如果未安装）
yum install -y docker
systemctl start docker
systemctl enable docker

# 安装 Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 开放防火墙端口
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --permanent --add-port=7000/tcp
firewall-cmd --reload

# 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 检查状态
sleep 5
docker-compose -f docker-compose.prod.yml ps
curl http://localhost:7000/health
```

---

## 🌐 访问地址

部署完成后：
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

# 停止服务
docker-compose -f docker-compose.prod.yml down

# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 重新构建
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## ⚠️ 注意事项

1. **API Key 安全**：backend/.env 文件包含敏感信息，已加入 .gitignore
2. **防火墙**：确保 8080 和 7000 端口已开放
3. **内存**：服务器至少 2GB 内存（当前 3.5GB 足够）
4. **网络**：首次部署需要下载 Docker 镜像，请确保网络通畅

---

## 🐛 故障排查

### 端口被占用
```bash
netstat -tlnp | grep 8080
kill -9 <PID>
```

### 防火墙问题
```bash
# 临时关闭测试
systemctl stop firewalld

# 或开放端口
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --permanent --add-port=7000/tcp
firewall-cmd --reload
```

### Docker 问题
```bash
# 检查 Docker 状态
systemctl status docker

# 重启 Docker
systemctl restart docker

# 查看容器日志
docker logs llm-chat-backend
docker logs llm-chat-frontend
```