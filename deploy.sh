#!/bin/bash

# LLM Chat App 生产环境部署脚本
# 在阿里云服务器上执行

set -e

echo "🚀 开始部署 LLM Chat App..."

# 1. 检查 Docker 和 Docker Compose
echo "📦 检查 Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，正在安装..."
    yum install -y docker
    systemctl start docker
    systemctl enable docker
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，正在安装..."
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 2. 创建项目目录
echo "📁 创建项目目录..."
mkdir -p /opt
if [ -d "/opt/llm-chat-app" ]; then
    echo "⚠️  项目目录已存在，备份旧版本..."
    mv /opt/llm-chat-app /opt/llm-chat-app.backup.$(date +%Y%m%d_%H%M%S)
fi

# 3. 克隆代码（请修改为你的 GitHub 仓库地址）
echo "📥 克隆代码..."
cd /opt
git clone https://github.com/YOUR_USERNAME/llm-chat-app.git
cd llm-chat-app

# 4. 配置环境变量
echo "⚙️  配置环境变量..."
read -sp "请输入 DeepSeek API Key: " API_KEY
echo

# 创建后端 .env 文件
cat > backend/.env << EOF
# DeepSeek API Configuration
DEEPSEEK_API_KEY=${API_KEY}
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_MODEL=deepseek-chat

# Backend Configuration
BACKEND_PORT=8000
CORS_ORIGINS=http://8.130.209.117:8080
EOF

echo "✅ 环境变量配置完成"

# 5. 开放防火墙端口
echo "🔓 开放防火墙端口..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=8080/tcp
    firewall-cmd --permanent --add-port=7000/tcp
    firewall-cmd --reload
    echo "✅ 防火墙端口已开放"
else
    echo "⚠️  firewall-cmd 未找到，请手动开放 8080 和 7000 端口"
fi

# 6. 启动服务
echo "🚀 启动服务..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
docker-compose -f docker-compose.prod.yml up -d --build

# 7. 检查服务状态
echo "🔍 检查服务状态..."
sleep 5

echo ""
echo "📊 服务状态："
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "🧪 测试后端 API..."
if curl -s http://localhost:7000/health | grep -q "healthy"; then
    echo "✅ 后端服务正常"
else
    echo "❌ 后端服务异常，请检查日志: docker-compose -f docker-compose.prod.yml logs backend"
fi

echo ""
echo "=========================================="
echo "🎉 部署完成！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  前端界面: http://8.130.209.117:8080"
echo "  后端 API: http://8.130.209.117:7000"
echo "  API 文档: http://8.130.209.117:7000/docs"
echo ""
echo "常用命令："
echo "  查看日志: docker-compose -f docker-compose.prod.yml logs -f"
echo "  停止服务: docker-compose -f docker-compose.prod.yml down"
echo "  重启服务: docker-compose -f docker-compose.prod.yml restart"
echo ""
echo "=========================================="