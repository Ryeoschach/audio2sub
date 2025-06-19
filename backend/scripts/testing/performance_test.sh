#!/bin/bash

# Audio2Sub 性能测试脚本
# 测试不同部署模式的性能表现

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 检查API是否可用
wait_for_api() {
    local url="$1"
    local timeout=60
    local count=0
    
    log_info "等待API启动: $url"
    
    while [ $count -lt $timeout ]; do
        if curl -s -f "$url/health" > /dev/null; then
            log_success "API已就绪"
            return 0
        fi
        
        sleep 1
        count=$((count + 1))
        echo -n "."
    done
    
    echo
    log_error "API启动超时"
    return 1
}

# 上传测试文件
upload_test_file() {
    local api_url="$1"
    local test_file="$2"
    
    if [ ! -f "$test_file" ]; then
        log_error "测试文件不存在: $test_file"
        return 1
    fi
    
    log_info "上传测试文件: $test_file"
    
    local response=$(curl -s -X POST \
        -F "file=@$test_file" \
        "$api_url/upload/")
    
    local task_id=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['task_id'])" 2>/dev/null || echo "")
    
    if [ -z "$task_id" ]; then
        log_error "上传失败: $response"
        return 1
    fi
    
    echo "$task_id"
}

# 监控任务进度
monitor_task() {
    local api_url="$1"
    local task_id="$2"
    local start_time=$(date +%s)
    
    log_info "监控任务: $task_id"
    
    while true; do
        local response=$(curl -s "$api_url/status/$task_id")
        local state=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['state'])" 2>/dev/null || echo "ERROR")
        local status=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "Unknown")
        
        case "$state" in
            "SUCCESS")
                local end_time=$(date +%s)
                local duration=$((end_time - start_time))
                log_success "任务完成，耗时: ${duration}秒"
                echo "$duration"
                return 0
                ;;
            "FAILURE"|"ERROR")
                log_error "任务失败: $status"
                return 1
                ;;
            "PENDING"|"PROGRESS")
                echo -n "."
                sleep 2
                ;;
            *)
                log_warning "未知状态: $state - $status"
                sleep 2
                ;;
        esac
    done
}

# 测试单个部署模式
test_deployment_mode() {
    local mode="$1"
    local test_file="$2"
    local api_url="http://localhost:8000"
    
    log_info "测试部署模式: $mode"
    log_info "================================"
    
    # 检查API可用性
    if ! wait_for_api "$api_url"; then
        log_error "API不可用，跳过测试"
        return 1
    fi
    
    # 获取健康检查信息
    log_info "获取系统信息..."
    local health_response=$(curl -s "$api_url/health")
    echo "$health_response" | python3 -m json.tool
    
    # 上传文件并测试
    local task_id=$(upload_test_file "$api_url" "$test_file")
    if [ -z "$task_id" ]; then
        return 1
    fi
    
    # 监控任务并记录性能
    local duration=$(monitor_task "$api_url" "$task_id")
    if [ $? -eq 0 ]; then
        echo "$mode:$duration" >> performance_results.txt
        log_success "$mode 模式测试完成，耗时: ${duration}秒"
    else
        log_error "$mode 模式测试失败"
        return 1
    fi
    
    echo
}

# 运行性能基准测试
run_benchmark() {
    local test_file="$1"
    
    if [ -z "$test_file" ]; then
        # 使用默认测试文件
        test_file="/Users/creed/workspace/sourceCode/111.wav"
    fi
    
    if [ ! -f "$test_file" ]; then
        log_error "测试文件不存在: $test_file"
        log_info "请提供有效的音频文件路径"
        exit 1
    fi
    
    log_info "🔧 Audio2Sub 性能基准测试"
    log_info "测试文件: $test_file"
    log_info "==============================="
    
    # 清空结果文件
    > performance_results.txt
    
    # 测试可用的部署模式
    local modes=("cpu" "hybrid")
    
    # 检查是否支持GPU
    if docker info 2>/dev/null | grep -i nvidia &> /dev/null; then
        modes+=("gpu")
    fi
    
    for mode in "${modes[@]}"; do
        log_info "准备测试 $mode 模式..."
        
        # 停止当前服务
        docker-compose down 2>/dev/null || true
        sleep 2
        
        # 启动对应模式的服务
        case "$mode" in
            "cpu")
                docker-compose -f docker-compose.cpu.yml up -d
                ;;
            "hybrid")
                if [ -f "/usr/local/bin/whisper-cli" ]; then
                    export DEPLOYMENT_MODE=hybrid
                    docker-compose -f docker-compose.hybrid.yml up -d
                else
                    log_warning "跳过hybrid模式（whisper.cpp不可用）"
                    continue
                fi
                ;;
            "gpu")
                docker-compose -f docker-compose.gpu-new.yml up -d
                ;;
        esac
        
        # 等待服务启动
        sleep 10
        
        # 执行测试
        test_deployment_mode "$mode" "$test_file"
        
        # 清理
        docker-compose down 2>/dev/null || true
        sleep 2
    done
    
    # 显示结果汇总
    show_results
}

# 显示测试结果
show_results() {
    log_info "📊 性能测试结果汇总"
    log_info "===================="
    
    if [ ! -f "performance_results.txt" ] || [ ! -s "performance_results.txt" ]; then
        log_warning "没有测试结果"
        return
    fi
    
    echo "| 部署模式 | 耗时(秒) | 相对性能 |"
    echo "|----------|----------|----------|"
    
    # 找到最快的时间作为基准
    local fastest=$(sort -t: -k2 -n performance_results.txt | head -n1 | cut -d: -f2)
    
    while IFS=: read -r mode duration; do
        local relative=$(python3 -c "print(f'{$duration/$fastest:.2f}x')")
        printf "| %-8s | %-8s | %-8s |\n" "$mode" "$duration" "$relative"
    done < performance_results.txt
    
    echo
    log_success "性能测试完成！结果已保存到 performance_results.txt"
}

# 显示帮助信息
show_help() {
    echo "Audio2Sub 性能测试脚本"
    echo ""
    echo "用法: $0 [TEST_FILE]"
    echo ""
    echo "参数:"
    echo "  TEST_FILE  测试音频文件路径（可选，默认使用111.wav）"
    echo ""
    echo "示例:"
    echo "  $0                                    # 使用默认测试文件"
    echo "  $0 /path/to/your/audio.wav           # 使用指定测试文件"
    echo ""
    echo "注意:"
    echo "  - 该脚本会依次测试所有可用的部署模式"
    echo "  - 每次测试都会重启服务，需要一定时间"
    echo "  - 确保有足够的磁盘空间和网络连接"
}

# 主函数
main() {
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_help
        exit 0
    fi
    
    run_benchmark "$1"
}

# 执行主函数
main "$@"
