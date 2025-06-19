#!/bin/bash

# 测试whisper路径检测脚本

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

log_info "🔍 Whisper路径检测测试"
log_info "========================"

# 测试固定路径
log_info "检查固定路径..."
fixed_paths=(
    "/usr/local/bin/whisper-cli"
    "/usr/local/bin/whisper"
    "/opt/homebrew/bin/whisper-cli"
    "/opt/homebrew/bin/whisper"
    "/Users/creed/workspace/sourceCode/whisper.cpp/build/bin/whisper-cli"
    "/Users/creed/workspace/sourceCode/whisper.cpp/build/bin/main"
)

for path in "${fixed_paths[@]}"; do
    if [ -f "$path" ] && [ -x "$path" ]; then
        log_success "✅ 找到: $path"
        # 测试执行
        if "$path" --help &>/dev/null; then
            log_success "   可正常执行"
        else
            log_warning "   执行测试失败"
        fi
    else
        log_warning "❌ 未找到: $path"
    fi
done

# 测试PATH中的命令
log_info ""
log_info "检查PATH中的命令..."
for cmd in "whisper-cli" "whisper"; do
    if command -v "$cmd" &> /dev/null; then
        path=$(which "$cmd")
        log_success "✅ 在PATH中找到 $cmd: $path"
        if "$cmd" --help &>/dev/null; then
            log_success "   可正常执行"
        else
            log_warning "   执行测试失败"
        fi
    else
        log_warning "❌ 在PATH中未找到: $cmd"
    fi
done

# 测试模型文件
log_info ""
log_info "检查模型文件..."
model_paths=(
    "/Users/creed/workspace/sourceCode/whisper.cpp/models/ggml-base.bin"
    "./whisper.cpp/models/ggml-base.bin"
    "./models/ggml-base.bin"
    "/usr/local/share/whisper/models/ggml-base.bin"
    "/opt/homebrew/share/whisper/models/ggml-base.bin"
    "$HOME/.cache/whisper/ggml-base.bin"
)

for path in "${model_paths[@]}"; do
    expanded_path=$(eval echo "$path")  # 展开变量
    if [ -f "$expanded_path" ]; then
        size=$(ls -lh "$expanded_path" | awk '{print $5}')
        log_success "✅ 找到模型: $expanded_path ($size)"
    else
        log_warning "❌ 未找到模型: $expanded_path"
    fi
done

# 测试Python配置检测
log_info ""
log_info "测试Python配置检测..."
cd /Users/creed/workspace/sourceCode/audio2sub/backend

python3 -c "
import sys
sys.path.append('.')
from app.config import settings

print(f'检测结果:')
print(f'  部署模式: {settings.DEPLOYMENT_MODE}')
print(f'  设备类型: {settings.WHISPER_DEVICE}')
print(f'  whisper路径: {settings.WHISPER_CPP_PATH}')
print(f'  模型路径: {settings.MODEL_PATH}')
print(f'  whisper可用: {settings.is_whisper_available()}')
print(f'  模型可用: {settings.is_model_available()}')
print()
print('部署信息:')
import json
print(json.dumps(settings.get_deployment_info(), indent=2, ensure_ascii=False))
"

log_info ""
log_success "检测完成！"
