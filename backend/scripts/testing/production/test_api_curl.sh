#!/bin/bash
# Audio2Sub API 模型选择测试脚本 (curl)
# 使用 curl 命令测试不同模型的 API 功能

set -e

echo "🎯 Audio2Sub API Testing with curl"
echo "=================================="

BASE_URL="http://localhost:8000"
TEST_FILE="test_audio_curl.txt"

# 颜色输出函数
print_success() {
    echo -e "✅ $1"
}

print_error() {
    echo -e "❌ $1"
}

print_info() {
    echo -e "🔍 $1"
}

print_section() {
    echo -e "\n📋 $1"
    echo "$(printf '%.0s-' {1..40})"
}

# 检查依赖
check_dependencies() {
    print_info "Checking dependencies..."
    
    if ! command -v curl &> /dev/null; then
        print_error "curl is required but not installed"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        print_error "jq is required but not installed. Install with: brew install jq"
        exit 1
    fi
    
    print_success "Dependencies check passed"
}

# 测试健康检查
test_health() {
    print_section "Testing Health Endpoint"
    
    local response
    if response=$(curl -s "$BASE_URL/health" 2>/dev/null); then
        print_success "Health endpoint accessible"
        echo "$response" | jq '.'
        return 0
    else
        print_error "Health endpoint failed"
        return 1
    fi
}

# 获取可用模型
get_models() {
    print_section "Getting Available Models"
    
    local response
    if response=$(curl -s "$BASE_URL/models/" 2>/dev/null); then
        print_success "Models endpoint accessible"
        echo "$response" | jq '.'
        
        # 提取默认模型
        local default_model
        default_model=$(echo "$response" | jq -r '.default_model // "base"')
        print_info "Default model: $default_model"
        
        return 0
    else
        print_error "Models endpoint failed"
        return 1
    fi
}

# 创建测试文件
create_test_file() {
    print_section "Creating Test File"
    
    cat > "$TEST_FILE" << EOF
Hello, this is a test audio file for Audio2Sub API testing.
We are testing different Whisper models including tiny, base, and small.
Each model has different speed and accuracy characteristics.
This test helps validate the dynamic model selection functionality.
Testing Chinese content: 你好，这是一个测试文件。
Testing numbers: 1, 2, 3, 4, 5.
Testing punctuation: Hello! How are you? I'm fine, thank you.
EOF
    
    print_success "Created test file: $TEST_FILE ($(wc -c < "$TEST_FILE") bytes)"
}

# 上传文件并测试模型
test_upload_with_model() {
    local model="$1"
    local language="$2"
    local output_format="$3"
    local description="$4"
    
    print_section "Testing Model: $model"
    echo "Description: $description"
    echo "Language: $language"
    echo "Output format: $output_format"
    
    local response
    response=$(curl -s -X POST "$BASE_URL/upload/" \
      -F "file=@$TEST_FILE" \
      -F "model=$model" \
      -F "language=$language" \
      -F "output_format=$output_format" \
      -F "task=transcribe" 2>/dev/null)
    
    if [ $? -eq 0 ] && echo "$response" | jq -e '.task_id' > /dev/null 2>&1; then
        print_success "Upload successful for $model model"
        echo "$response" | jq '.'
        
        # 提取任务 ID
        local task_id
        task_id=$(echo "$response" | jq -r '.task_id')
        
        if [ "$task_id" != "null" ] && [ -n "$task_id" ]; then
            print_info "Task ID: $task_id"
            
            # 监控任务状态
            monitor_task_status "$task_id" "$model"
        else
            print_error "No task ID returned"
        fi
    else
        print_error "Upload failed for $model model"
        echo "Response: $response"
    fi
    
    echo ""
}

# 监控任务状态
monitor_task_status() {
    local task_id="$1"
    local model="$2"
    local max_attempts=20
    local attempt=1
    
    print_info "Monitoring task status for $model model..."
    
    while [ $attempt -le $max_attempts ]; do
        local status_response
        status_response=$(curl -s "$BASE_URL/status/$task_id" 2>/dev/null)
        
        if [ $? -eq 0 ]; then
            local state
            state=$(echo "$status_response" | jq -r '.state // "UNKNOWN"')
            
            echo "Attempt $attempt/$max_attempts - State: $state"
            
            case "$state" in
                "SUCCESS")
                    print_success "Task completed successfully!"
                    
                    # 显示结果详情
                    local result
                    result=$(echo "$status_response" | jq '.result // {}')
                    
                    # 提取时间信息
                    local total_time
                    total_time=$(echo "$result" | jq -r '.timing.total_time // "N/A"')
                    echo "Total processing time: ${total_time}s"
                    
                    # 提取模型信息
                    local used_model
                    used_model=$(echo "$result" | jq -r '.transcription_params.model // "N/A"')
                    echo "Model used: $used_model"
                    
                    # 提取生成的文件
                    local files_count
                    files_count=$(echo "$result" | jq '.files | length // 0')
                    echo "Generated files: $files_count"
                    
                    if [ "$files_count" -gt 0 ]; then
                        echo "Files:"
                        echo "$result" | jq -r '.files[]? | "  - \(.filename) (\(.type))"'
                    fi
                    
                    # 显示转录文本预览
                    local full_text
                    full_text=$(echo "$result" | jq -r '.full_text // ""')
                    if [ -n "$full_text" ] && [ "$full_text" != "" ]; then
                        local preview
                        preview=$(echo "$full_text" | cut -c1-100)
                        echo "Transcription preview: $preview..."
                    fi
                    
                    return 0
                    ;;
                "FAILURE")
                    print_error "Task failed!"
                    echo "$status_response" | jq '.result // {}'
                    return 1
                    ;;
                "PROGRESS")
                    local progress_status
                    progress_status=$(echo "$status_response" | jq -r '.result.status // "Processing..."')
                    echo "Progress: $progress_status"
                    ;;
                "PENDING")
                    echo "Status: Pending..."
                    ;;
                *)
                    echo "Status: $state"
                    ;;
            esac
            
            sleep 5
        else
            print_error "Failed to check status (attempt $attempt)"
        fi
        
        ((attempt++))
    done
    
    print_error "Timeout waiting for task completion"
    return 1
}

# 运行完整测试套件
run_full_test() {
    print_section "Running Full Test Suite"
    
    # 定义测试配置
    local test_configs=(
        "tiny|auto|srt|最快速度，适合实时处理"
        "base|zh|vtt|平衡速度和质量，日常使用推荐"
        "small|auto|both|更高的准确度，专业转录"
    )
    
    local success_count=0
    local total_count=${#test_configs[@]}
    
    for config in "${test_configs[@]}"; do
        IFS='|' read -r model language output_format description <<< "$config"
        
        echo ""
        echo "🧪 Test $(($success_count + 1))/$total_count"
        
        if test_upload_with_model "$model" "$language" "$output_format" "$description"; then
            ((success_count++))
            print_success "Test passed for $model model"
        else
            print_error "Test failed for $model model"
        fi
        
        echo "$(printf '%.0s=' {1..60})"
    done
    
    # 输出测试总结
    print_section "Test Summary"
    echo "Total tests: $total_count"
    echo "Successful: $success_count"
    echo "Failed: $((total_count - success_count))"
    
    if [ $success_count -eq $total_count ]; then
        print_success "All tests passed! 🎉"
        return 0
    else
        print_error "Some tests failed"
        return 1
    fi
}

# 清理函数
cleanup() {
    print_section "Cleaning Up"
    
    if [ -f "$TEST_FILE" ]; then
        rm -f "$TEST_FILE"
        print_success "Removed test file: $TEST_FILE"
    fi
}

# 主函数
main() {
    echo "Starting Audio2Sub API tests..."
    echo "Time: $(date)"
    echo ""
    
    # 检查依赖
    check_dependencies
    
    # 测试健康检查
    if ! test_health; then
        print_error "API health check failed. Please ensure the server is running:"
        echo "  Backend: uvicorn app.main:app --reload"
        echo "  Celery: celery -A celery_app.celery_app worker --loglevel=info"
        exit 1
    fi
    
    # 获取模型列表
    if ! get_models; then
        print_error "Failed to get models list"
        exit 1
    fi
    
    # 创建测试文件
    create_test_file
    
    # 设置清理陷阱
    trap cleanup EXIT
    
    # 运行完整测试
    if run_full_test; then
        print_success "All API tests completed successfully! 🚀"
        exit 0
    else
        print_error "Some API tests failed"
        exit 1
    fi
}

# 运行主函数
main "$@"
