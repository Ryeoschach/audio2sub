#!/bin/bash

# Audio2Sub 管理脚本
# 提供常用的管理命令

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    echo "Audio2Sub 管理脚本"
    echo ""
    echo "用法: ./manage.sh [命令]"
    echo ""
    echo "可用命令:"
    echo "  start [mode]     启动服务 (native|hybrid|gpu|cpu)"
    echo "  stop             停止所有服务"
    echo "  restart [mode]   重启服务"
    echo "  status           查看服务状态"
    echo "  logs [service]   查看日志 (backend|worker|redis|flower)"
    echo "  health           健康检查"
    echo "  clean            清理未使用的Docker资源"
    echo "  monitor          打开监控界面"
    echo "  test             运行测试"
    echo "  deploy           智能部署"
    echo "  help             显示此帮助信息"
}

# 检测当前部署模式
detect_current_mode() {
    if docker ps --format "table {{.Names}}" | grep -q "hybrid"; then
        echo "hybrid"
    elif docker ps --format "table {{.Names}}" | grep -q "native"; then
        echo "native"
    elif docker ps --format "table {{.Names}}" | grep -q "gpu"; then
        echo "gpu"
    elif docker ps --format "table {{.Names}}" | grep -q "cpu"; then
        echo "cpu"
    else
        echo "none"
    fi
}

# 启动服务
start_service() {
    local mode=${1:-hybrid}
    
    log_info "启动 $mode 模式服务..."
    
    case $mode in
        native)
            if [ ! -f "docker-compose.native.yml" ]; then
                log_error "native 模式配置文件不存在"
                exit 1
            fi
            docker-compose -f docker-compose.native.yml up -d
            ;;
        hybrid)
            if [ ! -f "docker-compose.hybrid.yml" ]; then
                log_error "hybrid 模式配置文件不存在"
                exit 1
            fi
            docker-compose -f docker-compose.hybrid.yml up -d
            ;;
        gpu)
            if [ ! -f "docker-compose.gpu-new.yml" ]; then
                log_error "gpu 模式配置文件不存在"
                exit 1
            fi
            docker-compose -f docker-compose.gpu-new.yml up -d
            ;;
        cpu)
            if [ ! -f "docker-compose.cpu.yml" ]; then
                log_error "cpu 模式配置文件不存在"
                exit 1
            fi
            docker-compose -f docker-compose.cpu.yml up -d
            ;;
        *)
            log_error "未知的部署模式: $mode"
            log_info "支持的模式: native, hybrid, gpu, cpu"
            exit 1
            ;;
    esac
    
    log_success "$mode 模式服务启动完成"
    sleep 3
    show_status
}

# 停止服务
stop_service() {
    local current_mode=$(detect_current_mode)
    
    if [ "$current_mode" = "none" ]; then
        log_warning "没有检测到运行中的服务"
        return
    fi
    
    log_info "停止 $current_mode 模式服务..."
    
    case $current_mode in
        native)
            docker-compose -f docker-compose.native.yml down
            ;;
        hybrid)
            docker-compose -f docker-compose.hybrid.yml down
            ;;
        gpu)
            docker-compose -f docker-compose.gpu-new.yml down
            ;;
        cpu)
            docker-compose -f docker-compose.cpu.yml down
            ;;
    esac
    
    log_success "服务已停止"
}

# 重启服务
restart_service() {
    local mode=${1:-$(detect_current_mode)}
    
    if [ "$mode" = "none" ]; then
        log_warning "没有检测到运行中的服务，将使用默认的 hybrid 模式"
        mode="hybrid"
    fi
    
    log_info "重启 $mode 模式服务..."
    stop_service
    sleep 2
    start_service "$mode"
}

# 显示服务状态
show_status() {
    local current_mode=$(detect_current_mode)
    
    echo ""
    log_info "=== 服务状态 ==="
    echo "当前模式: $current_mode"
    echo ""
    
    if [ "$current_mode" != "none" ]; then
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(audio2sub|redis)"
        echo ""
        
        # 健康检查
        log_info "=== 健康检查 ==="
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            log_success "Backend API: 健康"
        else
            log_error "Backend API: 不可访问"
        fi
        
        if curl -sf http://localhost:5555 > /dev/null 2>&1; then
            log_success "Flower监控: 可访问"
        else
            log_warning "Flower监控: 不可访问"
        fi
    else
        log_warning "没有运行中的服务"
    fi
}

# 查看日志
show_logs() {
    local service=${1:-backend}
    local current_mode=$(detect_current_mode)
    
    if [ "$current_mode" = "none" ]; then
        log_error "没有运行中的服务"
        exit 1
    fi
    
    case $service in
        backend)
            docker logs -f "audio2sub_backend_$current_mode"
            ;;
        worker)
            docker logs -f "audio2sub_worker_$current_mode"
            ;;
        redis)
            docker logs -f "audio2sub_redis_$current_mode"
            ;;
        flower)
            docker logs -f "audio2sub_flower_$current_mode"
            ;;
        *)
            log_error "未知的服务: $service"
            log_info "支持的服务: backend, worker, redis, flower"
            exit 1
            ;;
    esac
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查Docker服务
    if ! docker ps > /dev/null 2>&1; then
        log_error "Docker服务未运行"
        exit 1
    fi
    
    # 检查API健康
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        log_success "API健康检查通过"
        curl -s http://localhost:8000/health | jq . 2>/dev/null || curl -s http://localhost:8000/health
    else
        log_error "API健康检查失败"
        exit 1
    fi
    
    # 检查Redis连接
    local current_mode=$(detect_current_mode)
    if [ "$current_mode" != "none" ]; then
        if docker exec "audio2sub_redis_$current_mode" redis-cli ping > /dev/null 2>&1; then
            log_success "Redis连接正常"
        else
            log_error "Redis连接失败"
        fi
    fi
}

# 清理Docker资源
clean_docker() {
    log_info "清理未使用的Docker资源..."
    
    # 停止所有audio2sub相关容器
    docker ps -a --format "table {{.Names}}" | grep audio2sub | xargs -r docker rm -f
    
    # 清理未使用的镜像
    docker image prune -f
    
    # 清理未使用的卷
    docker volume prune -f
    
    # 清理未使用的网络
    docker network prune -f
    
    log_success "Docker资源清理完成"
}

# 打开监控界面
open_monitor() {
    log_info "打开监控界面..."
    
    if curl -sf http://localhost:5555 > /dev/null 2>&1; then
        if command -v open > /dev/null 2>&1; then
            open http://localhost:5555
        else
            log_info "请在浏览器中访问: http://localhost:5555"
        fi
    else
        log_error "监控界面不可访问，请检查Flower服务是否运行"
    fi
}

# 运行测试
run_test() {
    log_info "运行系统测试..."
    
    # 检查测试文件是否存在
    if [ -f "test_whisper_detection.sh" ]; then
        ./test_whisper_detection.sh
    else
        log_warning "测试脚本不存在"
    fi
    
    # 运行健康检查
    health_check
}

# 智能部署
smart_deploy() {
    log_info "启动智能部署..."
    
    if [ -f "smart_deploy_v2.sh" ]; then
        ./smart_deploy_v2.sh
    else
        log_error "智能部署脚本不存在"
        exit 1
    fi
}

# 主函数
main() {
    case ${1:-help} in
        start)
            start_service "$2"
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service "$2"
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2"
            ;;
        health)
            health_check
            ;;
        clean)
            clean_docker
            ;;
        monitor)
            open_monitor
            ;;
        test)
            run_test
            ;;
        deploy)
            smart_deploy
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
