# Audio2Sub Backend 测试说明

## 测试文件组织结构

### 📁 tests/ - 主要测试文件
- `test_api_complete.py` - **完整API测试** (推荐使用)
  - 测试整个API端点流程：文件上传 → 转录 → 字幕生成 → 文件下载
  - 验证修复后的字幕生成功能
  - 包含健康检查、错误处理等完整测试

- `test_whisper_core.py` - **核心Whisper功能测试**
  - 测试Whisper转录核心功能
  - 验证字幕生成算法
  - 单元级别的功能验证

- `test_comprehensive.py` - **综合环境测试**
  - 测试uv虚拟环境配置
  - 验证所有依赖安装情况
  - 环境完整性检查

- `test_api_legacy.py` - **遗留API测试**
  - 旧版本API测试代码（保留作为参考）

### 🔧 tests/debug/ - 调试和故障排除文件
- `debug_celery_task.py` - Celery任务调试
- `debug_data_flow.py` - 数据流转调试
- `debug_subtitle_generation.py` - 字幕生成调试
- `debug_subtitle_issue.py` - 字幕问题诊断
- `debug_subtitle_test.py` - 字幕测试调试
- `debug_transcription.py` - 转录功能调试
- `test_fixed_celery_task.py` - 修复后的Celery任务测试
- `test_subtitle_debug.py` - 字幕调试专用

### 🧪 tests/units/ - 单元测试
- `test_whisper_manager.py` - WhisperManager类测试
- `test_transcription_unit.py` - 转录功能单元测试
- `test_subtitle_unit.py` - 字幕生成单元测试

## 如何运行测试

### 运行完整API测试（推荐）
```bash
# 确保API服务器已启动
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# 运行完整API测试
uv run python tests/test_api_complete.py
```

### 运行核心功能测试
```bash
uv run python tests/test_whisper_core.py
```

### 运行环境检查
```bash
uv run python tests/test_comprehensive.py
```

### 运行单元测试
```bash
uv run python tests/test_whisper_manager.py
uv run python tests/test_transcription_unit.py
uv run python tests/test_subtitle_unit.py
```

## 故障排除

如果遇到问题，可以运行调试文件：
```bash
# 调试Celery任务
uv run python tests/debug/debug_celery_task.py

# 调试数据流转
uv run python tests/debug/debug_data_flow.py

# 调试字幕生成
uv run python tests/debug/debug_subtitle_generation.py
```

## 注意事项

1. **音频文件要求**: 测试需要有效的音频文件，默认使用 `/Users/creed/workspace/sourceCode/whisper.cpp/111.wav`
2. **服务器状态**: API测试需要后端服务器运行在 `localhost:8000`
3. **环境依赖**: 确保在uv虚拟环境中运行所有测试
4. **文件清理**: 测试会在 `results/` 目录生成临时文件，可以定期清理

## 修复历史

- ✅ 修复了Celery任务中的 `update_state` 错误
- ✅ 解决了SRT/VTT文件为空的问题
- ✅ 改进了错误处理机制
- ✅ 优化了字幕生成算法
