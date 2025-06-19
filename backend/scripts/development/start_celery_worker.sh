#!/bin/bash
# 🚀 Audio2Sub Celery Worker 启动脚本

set -e

# 设置环境
export PYTHONPATH="."
export CELERY_WORKER_HIJACK_ROOT_LOGGER="false"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "🔧 启动 Audio2Sub Celery Worker"
echo "📁 项目根目录: $PROJECT_ROOT"
echo "🔗 Python 路径: $PYTHONPATH"

cd "$PROJECT_ROOT"

# 检查 Redis 连接
echo "🔍 检查 Redis 连接..."
if ! uv run python -c "
import redis
from app.config import settings
r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
r.ping()
print('✅ Redis 连接成功')
" 2>/dev/null; then
    echo "❌ Redis 连接失败"
    echo "💡 请确保 Redis 服务正在运行:"
    echo "   macOS: brew services start redis"
    echo "   Docker: docker run -d -p 6379:6379 redis:7-alpine"
    exit 1
fi

# 启动 Celery Worker
echo "🚀 启动 Celery Worker..."
echo "   模式: Solo Pool (ML 友好)"
echo "   日志级别: INFO"
echo ""

exec uv run celery -A celery_app.celery_app worker \
    --loglevel=info \
    --pool=solo \
    --concurrency=1 \
    --max-tasks-per-child=10
