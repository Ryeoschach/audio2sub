# 🔧 Audio2Sub 开发环境测试套件

这个目录包含了用于开发过程中调试、验证和性能分析的测试脚本。

## 📋 测试脚本说明

### 1. `test_model_selection_api.py` - 完整 API 功能测试 ⭐⭐

**用途**: 全面测试动态模型选择功能的 Python 实现

**特点**:
- 📊 详细的日志输出
- 🔍 错误追踪和调试信息
- 📈 性能指标收集
- 🧪 多模型对比测试

**使用方法**:
```bash
uv run python test_model_selection_api.py
```

**测试配置**:
```python
test_configs = [
    {"model": "tiny", "language": "auto", "output_format": "srt"},
    {"model": "base", "language": "zh", "output_format": "vtt"},
    {"model": "small", "language": "auto", "output_format": "both"}
]
```

**输出内容**:
- 健康检查结果
- 模型列表信息
- 上传响应详情
- 任务监控日志
- 性能统计报告

---

### 2. `test_simple_api.py` - 快速功能验证 ⭐

**用途**: 简化的 API 测试，用于快速验证基本功能

**适用场景**:
- 🚀 快速功能验证
- 🐛 问题快速定位
- ⚡ CI/CD 集成测试

**使用方法**:
```bash
uv run python test_simple_api.py
```

**测试流程**:
1. API 健康检查
2. 获取模型列表
3. 单一模型上传测试
4. 任务状态监控
5. 结果验证

**特点**:
- 轻量级设计
- 快速执行 (< 10秒)
- 清晰的成功/失败输出

---

### 3. `debug_chinese_transcription.py` - 中文转录调试 🐛

**用途**: 专门用于调试中文语音转录相关问题

**调试功能**:
- 🔍 详细的 whisper.cpp 命令输出
- 📝 转录参数验证
- 🌍 语言检测分析
- 📄 字幕文件内容检查

**使用方法**:
```bash
uv run python debug_chinese_transcription.py
```

**调试信息包括**:
- whisper.cpp 命令行参数
- 模型加载状态
- 语言参数传递
- 输出文件生成过程
- 错误详细堆栈

**问题排查清单**:
- [ ] whisper.cpp 路径正确
- [ ] 模型文件存在
- [ ] 语言参数有效
- [ ] 音频文件格式支持
- [ ] 输出目录权限

## 🔧 开发工具集成

### VS Code 集成
在 `.vscode/tasks.json` 中添加测试任务:
```json
{
    "label": "Test API",
    "type": "shell",
    "command": "uv run python scripts/testing/development/test_simple_api.py",
    "group": "test",
    "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "new"
    }
}
```

### Git Hooks
在 `.git/hooks/pre-commit` 中添加:
```bash
#!/bin/bash
echo "Running API tests..."
cd backend
uv run python scripts/testing/development/test_simple_api.py
if [ $? -ne 0 ]; then
    echo "API tests failed. Commit aborted."
    exit 1
fi
```

## 🐛 调试技巧

### 1. 逐步调试流程

**第一步: 基础连接测试**
```bash
curl http://localhost:8000/health
```

**第二步: 模型可用性检查**
```bash
curl http://localhost:8000/models/ | jq '.models[].name'
```

**第三步: 单一上传测试**
```python
# 使用 test_simple_api.py 进行快速验证
```

**第四步: 详细调试**
```python
# 使用 debug_chinese_transcription.py 深入分析
```

### 2. 常见问题诊断

#### 问题: 转录结果为空
```bash
# 检查 whisper.cpp 直接调用
/Users/creed/.audio2sub/whisper.cpp/build/bin/whisper-cli \
  --model models/ggml-base.bin \
  --language zh \
  --output-srt \
  test_audio.mp3
```

#### 问题: 语言检测错误
```python
# 在 debug_chinese_transcription.py 中检查
# 1. 音频文件是否为真实中文语音
# 2. language 参数是否正确传递
# 3. whisper.cpp 版本兼容性
```

#### 问题: 任务超时
```python
# 检查 Celery Worker 状态
# 1. Worker 进程是否运行
# 2. Redis 连接是否正常
# 3. 模型文件是否完整
```

## 📊 性能分析

### 性能测试脚本
```python
import time
import requests

def benchmark_model(model_name, test_file):
    start_time = time.time()
    
    # 上传测试
    upload_time = time.time()
    response = upload_file(test_file, model_name)
    upload_duration = time.time() - upload_time
    
    # 处理测试
    process_time = time.time()
    result = wait_for_completion(response['task_id'])
    process_duration = time.time() - process_time
    
    total_duration = time.time() - start_time
    
    return {
        'model': model_name,
        'upload_time': upload_duration,
        'process_time': process_duration,
        'total_time': total_duration,
        'success': result is not None
    }
```

### 性能基准记录
| 测试日期 | 模型 | 音频时长 | 处理时间 | 内存使用 | 备注 |
|---------|------|---------|---------|---------|------|
| 2025-06-19 | tiny | 30s | 0.05s | 50MB | 基准测试 |
| 2025-06-19 | base | 30s | 0.08s | 150MB | 推荐配置 |
| 2025-06-19 | small | 30s | 0.15s | 500MB | 高质量 |

## 🧪 自定义测试

### 创建新的测试用例
```python
def test_custom_scenario():
    """自定义测试场景"""
    # 1. 准备测试数据
    test_config = {
        'model': 'base',
        'language': 'zh',
        'output_format': 'both',
        'test_description': '自定义测试场景'
    }
    
    # 2. 执行测试
    result = run_transcription_test(test_config)
    
    # 3. 验证结果
    assert result['success'] == True
    assert 'files' in result
    assert len(result['files']) == 2  # SRT + VTT
    
    # 4. 记录结果
    log_test_result(test_config, result)
```

### 批量测试脚本
```python
def run_batch_tests():
    """批量运行多个测试用例"""
    test_cases = [
        {'model': 'tiny', 'language': 'auto'},
        {'model': 'base', 'language': 'zh'},
        {'model': 'small', 'language': 'en'},
    ]
    
    results = []
    for test_case in test_cases:
        result = run_single_test(test_case)
        results.append(result)
    
    generate_report(results)
```

## 📝 测试文档模板

### Bug 报告模板
```markdown
## 🐛 Bug 报告

**描述**: 简要描述问题

**复现步骤**:
1. 运行命令: `uv run python test_xxx.py`
2. 使用参数: `model=base, language=zh`
3. 观察结果: 转录结果为空

**期望结果**: 应该生成中文字幕

**实际结果**: 返回空的字幕文件

**环境信息**:
- OS: macOS 14.5
- Python: 3.11
- Whisper.cpp: latest
- 模型: ggml-base.bin

**相关日志**:
```
[ERROR] whisper.cpp failed to process audio
```

**解决方案**: (待填写)
```

## 🔗 相关资源

- [生产环境测试](../production/)
- [归档测试](../archived/)
- [API 文档](../../docs/)
- [开发指南](../../README.md)

---

**最后更新**: 2025年6月19日
**维护者**: Audio2Sub 开发团队
