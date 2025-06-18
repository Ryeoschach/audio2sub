#!/bin/bash
# Audio2Sub Backend whisper.cpp 快速启动脚本

echo "🚀 Audio2Sub Backend whisper.cpp 快速启动"
echo "================================================"

# 检查当前目录
if [ ! -f "pyproject.toml" ]; then
    echo "❌ 错误: 请在backend项目根目录下运行此脚本"
    exit 1
fi

echo "📍 当前目录: $(pwd)"

# 检查依赖
echo "🔍 检查依赖..."
if [ ! -d ".venv" ]; then
    echo "📦 安装依赖..."
    uv sync
else
    echo "✅ 虚拟环境已存在"
fi

# 检查whisper.cpp
WHISPER_PATH="/Users/creed/workspace/sourceCode/whisper.cpp/build/bin/whisper-cli"
if [ -f "$WHISPER_PATH" ]; then
    echo "✅ whisper.cpp 已找到: $WHISPER_PATH"
else
    echo "⚠️ whisper.cpp 未找到，请检查路径配置"
fi

# 检查模型
MODEL_PATH="models/ggml-base.bin"
if [ -f "$MODEL_PATH" ]; then
    echo "✅ 模型文件已存在: $MODEL_PATH"
else
    echo "📥 复制模型文件..."
    mkdir -p models
    if [ -f "/Users/creed/workspace/sourceCode/whisper.cpp/models/ggml-base.bin" ]; then
        cp "/Users/creed/workspace/sourceCode/whisper.cpp/models/ggml-base.bin" "$MODEL_PATH"
        echo "✅ 模型文件复制完成"
    else
        echo "⚠️ 源模型文件未找到，需要手动下载"
    fi
fi

# 启动选项
echo ""
echo "🎯 选择启动模式:"
echo "1) 开发模式 (API + Worker)"
echo "2) 仅API服务"
echo "3) 仅Worker"
echo "4) 运行测试"
echo "5) Docker部署"

read -p "请选择 (1-5): " choice

case $choice in
    1)
        echo "🚀 启动开发模式..."
        echo "📱 API服务将在 http://localhost:8000 启动"
        echo "📝 API文档: http://localhost:8000/docs"
        echo ""
        echo "在新终端中启动Worker:"
        echo "cd $(pwd) && uv run celery -A app.tasks worker --loglevel=info --pool=solo"
        echo ""
        uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    2)
        echo "🌐 仅启动API服务..."
        uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    3)
        echo "⚙️ 仅启动Worker..."
        uv run celery -A app.tasks worker --loglevel=info --pool=solo
        ;;
    4)
        echo "🧪 运行测试..."
        if [ -f "test_whisper_manager.py" ]; then
            echo "测试 WhisperManager..."
            PYTHONPATH=. uv run python test_whisper_manager.py
        fi
        if [ -f "test_simple_transcription.py" ]; then
            echo "测试 API转录..."
            PYTHONPATH=. uv run python test_simple_transcription.py
        fi
        ;;
    5)
        echo "🐳 Docker部署..."
        if [ -f "deploy_whisper.sh" ]; then
            ./deploy_whisper.sh auto
        else
            echo "❌ deploy_whisper.sh 未找到"
        fi
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac
