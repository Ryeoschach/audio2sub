#!/bin/bash

# Audio2Sub Docker 部署和测试脚本
# 用于快速部署和验证系统功能

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    echo "Audio2Sub Docker 部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  dev       启动开发环境"
    echo "  prod      启动生产环境"
    echo "  stop      停止所有服务"
    echo "  test      运行系统测试"
    echo "  clean     清理Docker资源"
    echo "  logs      查看服务日志"
    echo "  status    查看服务状态"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 dev     # 启动开发环境"
    echo "  $0 prod    # 启动生产环境"
    echo "  $0 test    # 运行测试"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    print_success "Docker 环境检查通过"
}

# 启动开发环境
start_dev() {
    print_info "启动开发环境..."
    
    # 检查配置文件
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml 文件不存在"
        exit 1
    fi
    
    # 验证配置
    print_info "验证 Docker Compose 配置..."
    docker-compose config > /dev/null
    
    # 构建并启动服务
    print_info "构建和启动服务..."
    docker-compose up --build -d
    
    # 等待服务启动
    print_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    check_services_dev
    
    print_success "开发环境启动成功！"
    print_info "服务访问地址:"
    print_info "  - 后端API: http://localhost:8000"
    print_info "  - API文档: http://localhost:8000/docs"
    print_info "  - 前端: http://localhost:5173"
    print_info "  - Redis: localhost:6379"
}

# 启动生产环境
start_prod() {
    print_info "启动生产环境..."
    
    # 检查配置文件
    if [ ! -f "docker-compose.prod.yml" ]; then
        print_error "docker-compose.prod.yml 文件不存在"
        exit 1
    fi
    
    # 验证配置
    print_info "验证 Docker Compose 配置..."
    docker-compose -f docker-compose.prod.yml config > /dev/null
    
    # 构建并启动服务
    print_info "构建和启动服务..."
    docker-compose -f docker-compose.prod.yml up --build -d
    
    # 等待服务启动
    print_info "等待服务启动..."
    sleep 15
    
    # 检查服务状态
    check_services_prod
    
    print_success "生产环境启动成功！"
    print_info "服务访问地址:"
    print_info "  - 后端API: http://localhost:8000"
    print_info "  - API文档: http://localhost:8000/docs"
    print_info "  - 前端: http://localhost:5173"
}

# 检查开发环境服务状态
check_services_dev() {
    print_info "检查服务状态..."
    
    # 检查容器状态
    if ! docker ps | grep -q "audio2sub_backend"; then
        print_error "Backend 服务未运行"
        return 1
    fi
    
    if ! docker ps | grep -q "audio2sub_celery_worker"; then
        print_error "Celery Worker 服务未运行"
        return 1
    fi
    
    if ! docker ps | grep -q "audio2sub_redis"; then
        print_error "Redis 服务未运行"
        return 1
    fi
    
    print_success "所有服务运行正常"
}

# 检查生产环境服务状态
check_services_prod() {
    print_info "检查服务状态..."
    
    # 检查容器状态
    if ! docker ps | grep -q "audio2sub_backend_prod"; then
        print_error "Backend 服务未运行"
        return 1
    fi
    
    if ! docker ps | grep -q "audio2sub_celery_worker_prod"; then
        print_error "Celery Worker 服务未运行"
        return 1
    fi
    
    if ! docker ps | grep -q "audio2sub_redis_prod"; then
        print_error "Redis 服务未运行"
        return 1
    fi
    
    print_success "所有服务运行正常"
}

# 停止服务
stop_services() {
    print_info "停止服务..."
    
    # 停止开发环境
    if [ -f "docker-compose.yml" ]; then
        docker-compose down
    fi
    
    # 停止生产环境
    if [ -f "docker-compose.prod.yml" ]; then
        docker-compose -f docker-compose.prod.yml down
    fi
    
    print_success "服务已停止"
}

# 运行测试
run_tests() {
    print_info "运行系统测试..."
    
    # 检查服务是否运行
    if ! docker ps | grep -q "audio2sub"; then
        print_error "没有检测到运行中的服务，请先启动环境"
        exit 1
    fi
    
    # API健康检查
    print_info "测试 API 健康状态..."
    if curl -f -s http://localhost:8000/docs > /dev/null; then
        print_success "API 服务正常"
    else
        print_error "API 服务异常"
    fi
    
    # Redis连接测试
    print_info "测试 Redis 连接..."
    if docker exec -it audio2sub_redis redis-cli -a redispassword ping | grep -q "PONG"; then
        print_success "Redis 连接正常"
    else
        print_error "Redis 连接异常"
    fi
    
    # Celery状态检查
    print_info "检查 Celery Worker 状态..."
    if docker logs audio2sub_celery_worker 2>&1 | grep -q "ready"; then
        print_success "Celery Worker 正常"
    else
        print_warning "Celery Worker 可能未就绪，请检查日志"
    fi
    
    print_success "系统测试完成"
}

# 清理Docker资源
clean_docker() {
    print_warning "清理 Docker 资源..."
    
    # 停止服务
    stop_services
    
    # 删除相关镜像
    print_info "删除相关镜像..."
    docker images | grep audio2sub | awk '{print $3}' | xargs -r docker rmi -f
    
    # 清理未使用的资源
    print_info "清理未使用的资源..."
    docker system prune -f
    
    print_success "Docker 资源清理完成"
}

# 查看日志
show_logs() {
    if docker ps | grep -q "audio2sub"; then
        print_info "显示服务日志 (按 Ctrl+C 退出)..."
        if docker ps | grep -q "audio2sub_backend_prod"; then
            docker-compose -f docker-compose.prod.yml logs -f
        else
            docker-compose logs -f
        fi
    else
        print_error "没有检测到运行中的服务"
    fi
}

# 查看状态
show_status() {
    print_info "服务状态:"
    docker ps --filter "name=audio2sub" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    print_info ""
    print_info "资源使用情况:"
    docker stats --no-stream --filter "name=audio2sub" --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

# 主函数
main() {
    case "${1:-help}" in
        "dev")
            check_docker
            start_dev
            ;;
        "prod")
            check_docker
            start_prod
            ;;
        "stop")
            stop_services
            ;;
        "test")
            run_tests
            ;;
        "clean")
            clean_docker
            ;;
        "logs")
            show_logs
            ;;
        "status")
            show_status
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"
