#!/bin/bash

# Audio2Sub 批量处理功能启动脚本
# 使用 uv 管理 Python 环境

set -e

echo "🎵 Audio2Sub 批量处理功能启动"
echo "================================"

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ uv 未安装，请先安装 uv"
    echo "💡 安装命令: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ uv 已安装"

# 进入后端目录
cd "$(dirname "$0")"
echo "📁 当前目录: $(pwd)"

# 检查项目文件
if [ ! -f "pyproject.toml" ]; then
    echo "❌ 未找到 pyproject.toml 文件"
    exit 1
fi

echo "✅ 项目文件检查完成"

# 安装依赖
echo "📦 安装项目依赖..."
uv sync

# 检查 Redis 是否运行
echo "🔍 检查 Redis 服务..."
if ! pgrep -x "redis-server" > /dev/null; then
    echo "⚠️  Redis 未运行，尝试启动..."
    
    # 尝试使用 Docker 启动 Redis
    if command -v docker &> /dev/null; then
        echo "🐳 使用 Docker 启动 Redis..."
        docker run -d \
            --name audio2sub-redis \
            -p 6379:6379 \
            redis:7-alpine \
            redis-server --appendonly yes
        
        # 等待 Redis 启动
        echo "⏳ 等待 Redis 启动..."
        sleep 3
    else
        echo "❌ 无法启动 Redis，请手动启动 Redis 服务"
        echo "💡 Docker 启动: docker run -d -p 6379:6379 redis:7-alpine"
        echo "💡 本地启动: redis-server"
        exit 1
    fi
else
    echo "✅ Redis 已运行"
fi

# 测试 Redis 连接
echo "🔗 测试 Redis 连接..."
if uv run python -c "
import redis
try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    print('✅ Redis 连接成功')
except Exception as e:
    print(f'❌ Redis 连接失败: {e}')
    exit(1)
"; then
    echo "✅ Redis 连接测试通过"
else
    echo "❌ Redis 连接测试失败"
    exit 1
fi

# 启动 Celery Worker (后台)
echo "🔄 启动 Celery Worker..."
uv run celery -A celery_app worker --loglevel=info --concurrency=4 &
CELERY_PID=$!

# 等待 Celery 启动
echo "⏳ 等待 Celery Worker 启动..."
sleep 5

# 检查 Celery 是否启动成功
if kill -0 $CELERY_PID 2>/dev/null; then
    echo "✅ Celery Worker 启动成功 (PID: $CELERY_PID)"
else
    echo "❌ Celery Worker 启动失败"
    exit 1
fi

# 启动 FastAPI 应用
echo "🚀 启动 FastAPI 应用..."
echo "📡 服务将在 http://localhost:8000 运行"
echo "📚 API 文档: http://localhost:8000/docs"
echo ""
echo "🎯 批量处理功能端点:"
echo "   POST /batch-upload/     - 批量上传文件"
echo "   GET  /batch-status/{id} - 查询批量状态"
echo "   GET  /batch-result/{id} - 获取批量结果"
echo "   DELETE /batch/{id}      - 取消批量任务"
echo ""
echo "🧪 测试批量功能:"
echo "   uv run python scripts/testing/test_batch_api.py"
echo ""
echo "按 Ctrl+C 停止服务"
echo "================================"

# 定义清理函数
cleanup() {
    echo ""
    echo "🛑 正在停止服务..."
    
    # 停止 Celery Worker
    if kill -0 $CELERY_PID 2>/dev/null; then
        echo "🔄 停止 Celery Worker..."
        kill $CELERY_PID
        wait $CELERY_PID 2>/dev/null || true
        echo "✅ Celery Worker 已停止"
    fi
    
    echo "👋 服务已停止"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 启动 FastAPI 应用
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 如果到达这里，说明应用正常退出
cleanup
