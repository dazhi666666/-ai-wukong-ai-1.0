#!/bin/bash

# LLM Chat App 生产环境部署脚本
# 适用于 Alibaba Cloud Linux 3

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印信息函数
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 和 Docker Compose
check_docker() {
    print_info "检查 Docker 环境..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    # 检查 Docker 服务状态
    if ! systemctl is-active --quiet docker; then
        print_warn "Docker 服务未运行，正在启动..."
        sudo systemctl start docker
    fi
    
    print_info "Docker 环境检查通过"
}

# 检查环境变量
check_env() {
    print_info "检查环境变量..."
    
    if [ ! -f "backend/.env" ]; then
        print_error "backend/.env 文件不存在"
        print_info "请复制 backend/.env.example 到 backend/.env 并配置您的 API Key"
        exit 1
    fi
    
    # 检查 DEEPSEEK_API_KEY
    if ! grep -q "DEEPSEEK_API_KEY=" backend/.env || grep -q "DEEPSEEK_API_KEY=$" backend/.env; then
        print_error "DEEPSEEK_API_KEY 未配置"
        print_info "请在 backend/.env 中设置您的 DeepSeek API Key"
        exit 1
    fi
    
    print_info "环境变量检查通过"
}

# 拉取最新代码
pull_code() {
    print_info "拉取最新代码..."
    
    if [ -d ".git" ]; then
        git pull origin main || git pull origin master
        print_info "代码更新完成"
    else
        print_warn "当前目录不是 Git 仓库，跳过代码拉取"
    fi
}

# 部署应用
deploy() {
    print_info "开始部署应用..."
    
    # 停止旧容器
    print_info "停止旧容器..."
    docker-compose -f docker-compose.prod.yml down || true
    
    # 清理旧镜像
    print_info "清理旧镜像..."
    docker system prune -f
    
    # 构建并启动新容器
    print_info "构建并启动容器..."
    docker-compose -f docker-compose.prod.yml up -d --build
    
    # 等待服务启动
    print_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    print_info "检查服务状态..."
    docker-compose -f docker-compose.prod.yml ps
    
    # 健康检查
    print_info "进行健康检查..."
    if curl -s http://localhost/health > /dev/null; then
        print_info "✓ Nginx 服务运行正常"
    else
        print_warn "✗ Nginx 服务可能未正常运行"
    fi
    
    if curl -s http://localhost:8000/health > /dev/null 2>&1 || curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        print_info "✓ 后端服务运行正常"
    else
        print_warn "✗ 后端服务可能未正常运行"
    fi
}

# 查看日志
show_logs() {
    print_info "查看日志（按 Ctrl+C 退出）..."
    docker-compose -f docker-compose.prod.yml logs -f
}

# 主函数
main() {
    echo "========================================"
    echo "   LLM Chat App 生产环境部署脚本"
    echo "========================================"
    echo ""
    
    # 检查是否在项目根目录
    if [ ! -f "docker-compose.prod.yml" ]; then
        print_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 解析命令行参数
    case "${1:-deploy}" in
        deploy)
            check_docker
            check_env
            pull_code
            deploy
            print_info "========================================"
            print_info "部署完成！"
            print_info "访问地址: http://$(curl -s ifconfig.me || echo 'your-server-ip')"
            print_info "API 文档: http://$(curl -s ifconfig.me || echo 'your-server-ip'):8000/docs"
            print_info "========================================"
            ;;
        logs)
            show_logs
            ;;
        stop)
            print_info "停止服务..."
            docker-compose -f docker-compose.prod.yml down
            print_info "服务已停止"
            ;;
        restart)
            print_info "重启服务..."
            docker-compose -f docker-compose.prod.yml restart
            print_info "服务已重启"
            ;;
        update)
            check_docker
            check_env
            pull_code
            deploy
            ;;
        status)
            docker-compose -f docker-compose.prod.yml ps
            ;;
        *)
            echo "用法: $0 {deploy|logs|stop|restart|update|status}"
            echo ""
            echo "命令说明:"
            echo "  deploy  - 部署应用（默认）"
            echo "  logs    - 查看日志"
            echo "  stop    - 停止服务"
            echo "  restart - 重启服务"
            echo "  update  - 更新并重新部署"
            echo "  status  - 查看服务状态"
            exit 1
            ;;
    esac
}

main "$@"
