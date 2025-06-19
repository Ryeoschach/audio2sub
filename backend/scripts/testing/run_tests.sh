#!/bin/bash
# Audio2Sub Backend 测试运行脚本

set -e  # 遇到错误时退出

echo "🧪 Audio2Sub Backend 测试套件"
echo "=================================================="

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查uv环境
echo -e "${YELLOW}📋 检查环境...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ uv 环境正常${NC}"

# 函数：运行测试
run_test() {
    local test_file=$1
    local test_name=$2
    
    echo -e "${YELLOW}🧪 运行 ${test_name}...${NC}"
    if uv run python "$test_file"; then
        echo -e "${GREEN}✅ ${test_name} 通过${NC}"
        return 0
    else
        echo -e "${RED}❌ ${test_name} 失败${NC}"
        return 1
    fi
}

# 检查API服务器是否运行
check_api_server() {
    echo -e "${YELLOW}🔍 检查API服务器...${NC}"
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API服务器运行正常${NC}"
        return 0
    else
        echo -e "${RED}❌ API服务器未运行，请先启动：${NC}"
        echo "  uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"
        return 1
    fi
}

# 主测试函数
main() {
    local test_type=${1:-"all"}
    local failed_tests=0
    local total_tests=0
    
    case $test_type in
        "api")
            echo -e "${YELLOW}🌐 运行API测试${NC}"
            if check_api_server; then
                ((total_tests++))
                run_test "tests/test_api_complete.py" "完整API测试" || ((failed_tests++))
            else
                echo -e "${RED}跳过API测试（服务器未运行）${NC}"
            fi
            ;;
        
        "core")
            echo -e "${YELLOW}🔧 运行核心功能测试${NC}"
            ((total_tests++))
            run_test "tests/test_whisper_core.py" "核心Whisper功能测试" || ((failed_tests++))
            ;;
        
        "units")
            echo -e "${YELLOW}🧱 运行单元测试${NC}"
            for test_file in tests/units/*.py; do
                if [[ -f "$test_file" ]]; then
                    test_name=$(basename "$test_file" .py)
                    ((total_tests++))
                    run_test "$test_file" "$test_name" || ((failed_tests++))
                fi
            done
            ;;
        
        "comprehensive")
            echo -e "${YELLOW}🔍 运行综合测试${NC}"
            ((total_tests++))
            run_test "tests/test_comprehensive.py" "综合环境测试" || ((failed_tests++))
            ;;
        
        "debug")
            echo -e "${YELLOW}🐛 运行调试测试${NC}"
            echo "可用的调试测试："
            ls tests/debug/
            echo "手动运行示例："
            echo "  uv run python tests/debug/debug_celery_task.py"
            ;;
        
        "all")
            echo -e "${YELLOW}🚀 运行所有测试${NC}"
            
            # 核心功能测试
            ((total_tests++))
            run_test "tests/test_whisper_core.py" "核心Whisper功能测试" || ((failed_tests++))
            
            # 单元测试
            for test_file in tests/units/*.py; do
                if [[ -f "$test_file" ]]; then
                    test_name=$(basename "$test_file" .py)
                    ((total_tests++))
                    run_test "$test_file" "$test_name" || ((failed_tests++))
                fi
            done
            
            # 综合测试
            ((total_tests++))
            run_test "tests/test_comprehensive.py" "综合环境测试" || ((failed_tests++))
            
            # API测试（如果服务器运行）
            if check_api_server; then
                ((total_tests++))
                run_test "tests/test_api_complete.py" "完整API测试" || ((failed_tests++))
            else
                echo -e "${YELLOW}⚠️ 跳过API测试（服务器未运行）${NC}"
            fi
            ;;
        
        *)
            echo "用法: $0 [api|core|units|comprehensive|debug|all]"
            echo ""
            echo "测试类型："
            echo "  api           - API端点测试（需要服务器运行）"
            echo "  core          - 核心功能测试"
            echo "  units         - 单元测试"
            echo "  comprehensive - 综合环境测试"
            echo "  debug         - 调试测试（显示可用的调试工具）"
            echo "  all           - 运行所有测试（默认）"
            exit 1
            ;;
    esac
    
    # 测试结果总结
    if [[ $total_tests -gt 0 ]]; then
        echo ""
        echo "=================================================="
        echo -e "${YELLOW}📊 测试结果总结${NC}"
        echo "总测试数: $total_tests"
        echo "失败测试数: $failed_tests"
        echo "成功测试数: $((total_tests - failed_tests))"
        
        if [[ $failed_tests -eq 0 ]]; then
            echo -e "${GREEN}🎉 所有测试通过！${NC}"
            exit 0
        else
            echo -e "${RED}❌ 有 $failed_tests 个测试失败${NC}"
            exit 1
        fi
    fi
}

# 运行主函数
main "$@"
