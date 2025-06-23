#!/bin/bash

# 🚀 Audio2Sub 测试快速入口
# 简化的测试执行工具

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧪 Audio2Sub 测试快速入口${NC}"
echo "========================="

# 显示选项
echo "请选择测试类型:"
echo "1) 🚀 快速验证 (API端点测试)"
echo "2) 📊 性能测试 (本地模型测试)" 
echo "3) 🎤 中文测试 (需要音频文件)"
echo "4) 🔧 开发测试 (简单功能验证)"
echo "5) 📋 帮助信息"
echo ""

read -p "请输入选择 (1-5): " choice

case $choice in
    1)
        echo -e "${BLUE}执行快速API验证...${NC}"
        if [ -f "production/test_api_curl.sh" ]; then
            cd production && ./test_api_curl.sh
        else
            ./test_api_curl.sh
        fi
        ;;
    2)
        echo -e "${BLUE}执行本地模型性能测试...${NC}"
        if [ -f "production/test_local_models.py" ]; then
            cd production && uv run python test_local_models.py
        else
            uv run python test_local_models.py
        fi
        ;;
    3)
        echo -e "${BLUE}执行中文语音测试...${NC}"
        if [ -f "production/test_real_chinese_audio.py" ]; then
            cd production && uv run python test_real_chinese_audio.py
        else
            uv run python test_real_chinese_audio.py
        fi
        ;;
    4)
        echo -e "${BLUE}执行开发功能测试...${NC}"
        if [ -f "development/test_simple_api.py" ]; then
            cd development && uv run python test_simple_api.py
        else
            uv run python test_simple_api.py
        fi
        ;;
    5)
        echo -e "${YELLOW}📋 测试工具说明:${NC}"
        echo ""
        echo "🚀 快速验证: 使用curl测试API端点，30秒内完成"
        echo "📊 性能测试: 测试4个本地模型的转录性能"
        echo "🎤 中文测试: 专门测试中文语音转录准确性"
        echo "🔧 开发测试: 轻量级的基础功能验证"
        echo ""
        echo "详细文档请参考:"
        echo "- 生产测试: production/README.md"
        echo "- 开发测试: development/README.md"
        echo "- 总体说明: README.md"
        ;;
    *)
        echo -e "${RED}❌ 无效选择${NC}"
        exit 1
        ;;
esac
