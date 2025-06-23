# 🚀 Audio2Sub 生产环境测试套件

这个目录包含了 Audio2Sub 项目的核心生产环境测试脚本，用于验证系统的完整功能和性能。

## 📋 测试脚本说明

### 1. `test_local_models.py` - 本地模型性能测试 ⭐⭐⭐

**用途**: 测试本地已下载的 Whisper 模型的性能和准确性

**支持的模型**:
- `tiny` - 39MB, 最快速度
- `base` - 142MB, 平衡推荐  
- `small` - 466MB, 高质量
- `large-v3-turbo` - 809MB, 快速高质量

**使用方法**:
```bash
uv run python test_local_models.py
```

**测试内容**:
- ✅ 四种模型的性能对比
- ✅ 不同语言设置 (auto/zh/en)
- ✅ 不同输出格式 (srt/vtt/both)
- ✅ 处理时间统计
- ✅ 转录质量分析

**输出**: 
- 详细的性能报告
- JSON 格式的测试结果文件

---

### 2. `test_api_curl.sh` - API 端点验证测试 ⭐⭐⭐

**用途**: 使用 curl 快速验证所有 API 端点的可用性

**依赖**: 
- `curl` 命令
- `jq` JSON 处理工具

**使用方法**:
```bash
./test_api_curl.sh
```

**测试内容**:
- ✅ 健康检查端点 (/health)
- ✅ 模型列表端点 (/models/)
- ✅ 文件上传端点 (/upload/)
- ✅ 任务状态查询 (/status/)
- ✅ 多模型测试 (tiny/base/small)

**特点**:
- 🚀 快速执行 (< 30秒)
- 📊 详细状态报告
- 🔧 自动清理测试文件
- ⚡ 无外部依赖 (除 curl/jq)

---

### 3. `test_real_chinese_audio.py` - 中文语音专项测试 ⭐⭐

**用途**: 专门测试中文语音转录的准确性和语言检测

**前提条件**: 
- 需要真实的中文音频文件: `/Users/creed/Desktop/audio.mp3`

**使用方法**:
```bash
uv run python test_real_chinese_audio.py
```

**测试配置**:
1. **自动检测 + SRT**: 验证语言自动识别
2. **指定中文 + VTT**: 验证指定语言转录
3. **自动检测 + 翻译**: 验证翻译功能

**分析内容**:
- 🔍 语言检测准确性
- 📝 转录内容质量
- ⏱️ 处理时间统计
- 📊 中英文字符分析

## 🔧 运行环境要求

### 系统要求
- macOS / Linux
- Python 3.8+
- Node.js 16+ (用于前端测试)

### 服务依赖
```bash
# 1. 后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 2. Celery Worker
export PYTHONPATH="."
uv run celery -A celery_app.celery_app worker --loglevel=info --pool=solo

# 3. Redis 服务
brew services start redis
```

### 模型文件
确保以下模型文件已下载到 `models/` 目录:
- `ggml-tiny.bin`
- `ggml-base.bin` 
- `ggml-small.bin`
- `ggml-large-v3-turbo.bin`

## 📊 测试结果示例

### 性能基准 (MacBook, MPS 设备)
| 模型 | 文件大小 | 处理时间 | 转录精度 | 推荐场景 |
|------|---------|---------|---------|---------|
| tiny | 39MB | ~0.05s | 较低 | 快速测试 |
| base | 142MB | ~0.08s | 良好 | 日常使用 |
| small | 466MB | ~0.15s | 较高 | 高质量需求 |
| large-v3-turbo | 809MB | ~0.37s | 很高 | 专业转录 |

## 🚨 故障排除

### 常见问题

1. **连接失败**
   ```bash
   ❌ API 连接错误: Connection refused
   ```
   **解决**: 确保后端服务运行在 http://localhost:8000

2. **模型文件缺失**
   ```bash
   ❌ 模型文件不存在
   ```
   **解决**: 检查 `models/` 目录中是否有对应的 `.bin` 文件

3. **Redis 连接失败**
   ```bash
   ❌ Redis 连接失败
   ```
   **解决**: 启动 Redis 服务 `brew services start redis`

4. **中文转录为英文**
   ```bash
   ⚠️ 指定中文但转录结果为英文
   ```
   **解决**: 
   - 确保音频确实是中文语音
   - 使用 `language: "zh"` 而不是 `"auto"`
   - 检查音频质量和清晰度

## 📈 性能优化建议

### 模型选择策略
- **开发测试**: 使用 `tiny` 模型快速验证
- **演示展示**: 使用 `base` 模型平衡效果
- **生产环境**: 根据质量要求选择 `small` 或 `large-v3-turbo`

### 并发处理
- 单个 Celery Worker 适合开发测试
- 生产环境建议配置多个 Worker 进程
- 监控 Redis 内存使用情况

## 📝 测试最佳实践

1. **定期执行**: 每次代码变更后运行核心测试
2. **环境一致**: 确保测试环境与生产环境配置一致
3. **数据多样**: 使用不同类型和长度的音频文件测试
4. **性能监控**: 记录和比较不同版本的性能指标
5. **错误追踪**: 保存失败测试的详细日志

## 🔗 相关文档

- [主要测试说明](../README.md)
- [开发环境测试](../development/)
- [前端测试指南](../../../frontend/README.md)
- [API 文档](../../docs/api.md)

---

**最后更新**: 2025年6月19日
**维护者**: Audio2Sub 开发团队
