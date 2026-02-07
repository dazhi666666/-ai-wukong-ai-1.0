#!/bin/bash

# 创建部署包
# 在 Windows 上双击运行此脚本，生成 deploy-package.tar.gz

echo "📦 正在创建部署包..."

# 进入项目目录
cd "$(dirname "$0")"

# 创建临时目录
mkdir -p deploy-package/llm-chat-app

# 复制所有文件（排除敏感信息和不需要的文件）
echo "📁 复制项目文件..."
rsync -av --exclude='.git' \
          --exclude='backend/.env' \
          --exclude='frontend/node_modules' \
          --exclude='backend/venv' \
          --exclude='__pycache__' \
          --exclude='*.pyc' \
          --exclude='test_api.py' \
          --exclude='api_response.json' \
          --exclude='deploy-package' \
          . deploy-package/llm-chat-app/

# 创建部署说明
cat > deploy-package/README.txt << 'EOF'
LLM Chat App 部署包
===================

部署步骤：
1. 将此文件夹上传到服务器 /opt/ 目录
2. SSH 登录服务器
3. 执行: cd /opt/llm-chat-app && ./install.sh

访问地址：
- 前端: http://8.130.209.117:8080
- 后端: http://8.130.209.117:7000

注意：部署时会要求输入 DeepSeek API Key
EOF

# 创建安装脚本
cat > deploy-package/llm-chat-app/install.sh << 'INSTALLSCRIPT'
#!/bin/bash
set -e

echo "🚀 LLM Chat App 安装脚本"
echo "========================"

# 检查是否为 root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 请使用 root 权限运行: sudo ./install.sh"
    exit 1
fi

# 安装 Docker
echo "📦 检查 Docker..."
if ! command -v docker &> /dev/null; then
    echo "正在安装 Docker..."
    yum install -y docker
    systemctl start docker
    systemctl enable docker
fi

# 安装 Docker Compose
echo "📦 检查 Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "正在安装 Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 配置环境变量
echo ""
echo "⚙️  配置环境变量"
echo "========================"

# 检查是否已有 .env 文件
if [ -f "backend/.env" ]; then
    echo "✅ 发现已有的环境变量配置"
    read -p "是否重新配置? (y/N): " reconfig
    if [[ $reconfig =~ ^[Yy]$ ]]; then
        configure_env=true
    else
        configure_env=false
    fi
else
    configure_env=true
fi

if [ "$configure_env" = true ]; then
    echo ""
    echo "请输入 DeepSeek API Key"
    echo "获取地址: https://platform.deepseek.com/"
    read -sp "API Key: " api_key
    echo ""
    
    # 创建 .env 文件
    cat > backend/.env << EOF
DEEPSEEK_API_KEY=${api_key}
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_MODEL=deepseek-chat
BACKEND_PORT=8000
CORS_ORIGINS=http://8.130.209.117:8080
EOF
    
    echo "✅ 环境变量配置完成"
fi

# 开放防火墙端口
echo ""
echo "🔓 配置防火墙..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=8080/tcp
    firewall-cmd --permanent --add-port=7000/tcp
    firewall-cmd --reload
    echo "✅ 防火墙端口已开放 (8080, 7000)"
else
    echo "⚠️  未找到 firewall-cmd，请手动开放端口 8080 和 7000"
fi

# 启动服务
echo ""
echo "🚀 启动服务..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
docker-compose -f docker-compose.prod.yml up -d --build

# 等待服务启动
echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "📊 检查服务状态..."
if curl -s http://localhost:7000/health | grep -q "healthy"; then
    echo "✅ 后端服务运行正常"
else
    echo "❌ 后端服务异常"
    echo "查看日志: docker-compose -f docker-compose.prod.yml logs backend"
fi

echo ""
echo "========================================"
echo "🎉 部署完成！"
echo "========================================"
echo ""
echo "访问地址："
echo "  🌐 前端界面: http://8.130.209.117:8080"
echo "  🔌 后端 API: http://8.130.209.117:7000"
echo "  📚 API 文档: http://8.130.209.117:7000/docs"
echo ""
echo "常用命令："
echo "  查看日志: docker-compose -f docker-compose.prod.yml logs -f"
echo "  停止服务: docker-compose -f docker-compose.prod.yml down"
echo "  重启服务: docker-compose -f docker-compose.prod.yml restart"
echo ""
echo "========================================"
INSTALLSCRIPT

chmod +x deploy-package/llm-chat-app/install.sh

# 创建压缩包
echo "📦 创建压缩包..."
cd deploy-package
tar -czvf ../llm-chat-app-deploy.tar.gz .
cd ..

# 清理临时文件
rm -rf deploy-package

echo ""
echo "✅ 部署包创建成功！"
echo ""
echo "文件: llm-chat-app-deploy.tar.gz"
echo ""
echo "上传到服务器的命令："
echo "  scp llm-chat-app-deploy.tar.gz root@8.130.209.117:/opt/"
echo ""
echo "然后在服务器上执行："
echo "  ssh root@8.130.209.117"
echo "  cd /opt && tar -xzvf llm-chat-app-deploy.tar.gz"
echo "  cd llm-chat-app && ./install.sh"
echo ""
read -p "按回车键退出..."