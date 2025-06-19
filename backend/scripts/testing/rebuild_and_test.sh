#!/bin/bash

echo "🔄 重新构建Audio2Sub Docker镜像并测试whisper.cpp"
echo "================================================="

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose -f docker-compose.cpu.yml down

# 删除旧镜像（强制重新构建）
echo "🗑️ 删除旧镜像..."
docker rmi $(docker images | grep "backend-" | awk '{print $3}') 2>/dev/null || echo "没有找到旧镜像"

# 重新构建镜像
echo "🏗️ 重新构建镜像..."
docker-compose -f docker-compose.cpu.yml build --no-cache

# 启动服务
echo "🚀 启动服务..."
docker-compose -f docker-compose.cpu.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose -f docker-compose.cpu.yml ps

# 检查whisper.cpp是否安装成功
echo "🔍 检查whisper.cpp安装状态..."
docker exec audio2sub_backend_cpu which whisper-cli
docker exec audio2sub_backend_cpu ls -la /usr/local/bin/whisper-cli
docker exec audio2sub_backend_cpu ls -la /app/models/

# 测试健康检查
echo "🏥 测试健康检查..."
curl -s http://localhost:8000/health | jq

echo "✅ 重新构建完成！现在可以测试真实的转录功能了"
echo "📝 访问 http://localhost:8000 上传音频文件测试"
echo "🌸 访问 http://localhost:5555 查看Flower监控"
