#!/bin/bash

# Audio2Sub 智能部署脚本
# 根据系统环境自动选择最佳部署模式

set -e

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

# 检测函数
detect_platform() {
    case "$(uname -s)" in
        Darwin*)    echo "macos";;
        Linux*)     echo "linux";;
        *)          echo "unknown";;
    esac
}

check_docker() {
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        return 0
    else
        return 1
    fi
}

check_nvidia_docker() {
    if check_docker && docker info 2>/dev/null | grep -i nvidia &> /dev/null; then
        return 0
    else
        return 1
    fi
}

check_whisper_host() {
    # 检查多个可能的whisper路径
    local whisper_paths=(
        "/usr/local/bin/whisper-cli"
        "/usr/local/bin/whisper"
        "/opt/homebrew/bin/whisper-cli"
        "/opt/homebrew/bin/whisper"
        "/Users/creed/workspace/sourceCode/whisper.cpp/build/bin/whisper-cli"
        "/Users/creed/workspace/sourceCode/whisper.cpp/build/bin/main"
    )
    
    # 检查固定路径
    for path in "${whisper_paths[@]}"; do
        if [ -f "$path" ] && [ -x "$path" ]; then
            log_success "找到whisper可执行文件: $path"
            export DETECTED_WHISPER_PATH="$path"
            return 0
        fi
    done
    
    # 检查PATH中的whisper命令
    if command -v whisper-cli &> /dev/null; then
        local whisper_path=$(which whisper-cli)
        log_success "在PATH中找到whisper-cli: $whisper_path"
        export DETECTED_WHISPER_PATH="$whisper_path"
        return 0
    fi
    
    if command -v whisper &> /dev/null; then
        local whisper_path=$(which whisper)
        log_success "在PATH中找到whisper: $whisper_path"
        export DETECTED_WHISPER_PATH="$whisper_path"
        return 0
    fi
    
    return 1
}

check_apple_silicon() {
    if [ "$(uname -s)" = "Darwin" ]; then
        if sysctl -n machdep.cpu.brand_string 2>/dev/null | grep -q "Apple"; then
            return 0
        fi
    fi
    return 1
}

# 部署模式选择
select_deployment_mode() {
    local platform=$(detect_platform)
    
    echo "检测系统环境..." >&2
    echo "平台: $platform" >&2
    
    # 检查Docker可用性
    if check_docker; then
        echo "✅ Docker 可用" >&2
    else
        echo "⚠️  Docker 不可用，将使用原生模式" >&2
        echo "native"
        return
    fi
    
    # 检查宿主机whisper.cpp
    local whisper_available=false
    if check_whisper_host; then
        echo "✅ 检测到宿主机whisper.cpp" >&2
        whisper_available=true
    else
        echo "⚠️  宿主机whisper.cpp不可用" >&2
        whisper_available=false
    fi
    
    # 根据平台和硬件选择模式
    case "$platform" in
        "macos")
            if check_apple_silicon; then
                echo "检测到Apple Silicon" >&2
                if [ "$whisper_available" = true ]; then
                    echo "✅ 推荐使用混合模式以获得MPS加速" >&2
                    echo "hybrid"
                else
                    echo "⚠️  推荐使用CPU模式（Docker中无法使用MPS）" >&2
                    echo "cpu"
                fi
            else
                echo "检测到Intel Mac" >&2
                if [ "$whisper_available" = true ]; then
                    echo "💡 推荐使用混合模式" >&2
                    echo "hybrid"
                else
                    echo "cpu"
                fi
            fi
                        ;;
        "linux")
            if check_nvidia_docker; then
                echo "✅ 检测到NVIDIA Docker支持" >&2
                echo "gpu"
            elif [ "$whisper_available" = true ]; then
                echo "💡 推荐使用混合模式" >&2
                echo "hybrid"
            else
                echo "cpu"
            fi
            ;;
        *)
            echo "⚠️  未知平台，使用CPU模式" >&2
            echo "cpu"
            ;;
    esac
}

# 部署函数
deploy_native() {
    log_info "启动原生部署模式..."
    log_info "whisper.cpp将根据系统硬件动态编译以获得最佳性能"
    
    # 仅启动Redis
    docker-compose -f docker-compose.native.yml up -d
    
    # 检测whisper路径
    if check_whisper_host; then
        log_success "自动检测到whisper路径: $DETECTED_WHISPER_PATH"
    else
        log_warning "未检测到whisper可执行文件，将在首次使用时自动编译"
    fi
    
    log_info "Redis已启动，请手动运行以下命令启动应用："
    log_info "export DEPLOYMENT_MODE=native"
    log_info "export REDIS_HOST=127.0.0.1"
    log_info "export REDIS_PORT=16379"
    
    if [ -n "$DETECTED_WHISPER_PATH" ]; then
        log_info "export WHISPER_CPP_PATH=$DETECTED_WHISPER_PATH"
    fi
    
    log_info "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    log_info ""
    log_info "或者运行worker:"
    log_info "celery -A celery_app worker --loglevel=info"
    log_info ""
    log_warning "注意：首次使用时whisper.cpp编译可能需要几分钟时间"
}

deploy_hybrid() {
    log_info "启动混合部署模式..."
    log_info "在此模式下，whisper.cpp将在容器内编译Linux版本"
    
    # 检查模型目录 (可选)
    local model_paths=(
        "/Users/creed/workspace/sourceCode/whisper.cpp/models"
        "./whisper.cpp/models"
        "/usr/local/share/whisper/models"
        "/opt/homebrew/share/whisper/models"
    )
    
    local model_dir=""
    for dir in "${model_paths[@]}"; do
        if [ -d "$dir" ] && [ -f "$dir/ggml-base.bin" ]; then
            model_dir="$dir"
            log_success "找到模型目录: $model_dir"
            break
        fi
    done
    
    if [ -z "$model_dir" ]; then
        log_warning "未找到本地模型目录，容器将自动下载模型"
        model_dir=""
    fi
    
    # 设置环境变量
    export DEPLOYMENT_MODE=hybrid
    if [ -n "$model_dir" ]; then
        export HOST_MODEL_DIR="$model_dir"
        log_info "环境变量设置:"
        log_info "  MODEL_DIR: $model_dir"
    else
        log_info "将使用容器内自动下载的模型"
    fi
    
    docker-compose -f docker-compose.hybrid.yml up -d --build
}

deploy_gpu() {
    log_info "启动GPU部署模式..."
    
    if ! check_nvidia_docker; then
        log_error "NVIDIA Docker不可用，请安装nvidia-docker2"
        exit 1
    fi
    
    docker-compose -f docker-compose.gpu-new.yml up -d
}

deploy_cpu() {
    log_info "启动CPU部署模式..."
    docker-compose -f docker-compose.cpu.yml up -d
}

# 主函数
main() {
    log_info "🚀 Audio2Sub 智能部署脚本"
    log_info "================================"
    
    # 选择部署模式
    local deployment_mode=""
    if [ -n "$1" ]; then
        deployment_mode="$1"
        log_info "使用指定的部署模式: $deployment_mode"
    else
        log_info "自动检测最佳部署模式..."
        deployment_mode=$(select_deployment_mode 2>/dev/null | tail -1)
        if [ -z "$deployment_mode" ]; then
            log_error "无法检测部署模式"
            exit 1
        fi
        log_info "自动选择部署模式: $deployment_mode"
    fi
    
    # 确认部署
    echo -n "确认使用 $deployment_mode 模式部署? (y/n): "
    read -r reply
    if [[ ! $reply =~ ^[Yy]$ ]]; then
        log_info "部署已取消"
        exit 0
    fi
    
    # 执行部署
    case "$deployment_mode" in
        "native")
            deploy_native
            ;;
        "hybrid")
            deploy_hybrid
            ;;
        "gpu")
            deploy_gpu
            ;;
        "cpu")
            deploy_cpu
            ;;
        *)
            log_error "未知部署模式: $deployment_mode"
            log_info "可用模式: native, hybrid, gpu, cpu"
            exit 1
            ;;
    esac
    
    log_success "部署完成！"
    log_info ""
    log_info "访问链接:"
    log_info "- API文档: http://localhost:8000/docs"
    log_info "- 健康检查: http://localhost:8000/health"
    if [ "$deployment_mode" != "native" ]; then
        log_info "- Flower监控: http://localhost:5555"
    fi
    log_info ""
    if [ "$deployment_mode" != "native" ]; then
        log_info "查看日志: docker-compose -f docker-compose.$deployment_mode.yml logs -f"
    fi
}

# 帮助信息
show_help() {
    echo "Audio2Sub 智能部署脚本"
    echo ""
    echo "用法: $0 [MODE]"
    echo ""
    echo "可用模式:"
    echo "  native  - 原生模式（仅Redis容器化，应用直接运行）"
    echo "  hybrid  - 混合模式（容器化服务 + 宿主机whisper.cpp）"
    echo "  gpu     - GPU模式（支持NVIDIA CUDA加速）"
    echo "  cpu     - CPU模式（完全容器化，CPU推理）"
    echo ""
    echo "如果不指定模式，脚本将自动检测最佳模式"
    echo ""
    echo "示例:"
    echo "  $0          # 自动检测模式"
    echo "  $0 hybrid   # 强制使用混合模式"
}

# 检查参数
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

# 执行主函数
main "$@"
