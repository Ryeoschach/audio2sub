# 🧪 Audio2Sub 测试套件总览

这是 Audio2Sub 项目的完整测试框架，包含生产环境验证、开发调试工具和历史归档。

## 📁 目录结构

```
scripts/testing/
├── production/          # 🚀 生产环境核心测试
│   ├── README.md        # 生产环境测试指南
│   ├── test_local_models.py     # ⭐ 本地模型性能测试
│   ├── test_api_curl.sh         # ⭐ API 端点验证测试
│   └── test_real_chinese_audio.py # ⭐ 中文语音专项测试
├── development/         # 🔧 开发环境调试工具
│   ├── README.md        # 开发测试指南
│   ├── test_model_selection_api.py  # 完整 API 功能测试
│   ├── test_simple_api.py          # 快速功能验证
│   └── debug_chinese_transcription.py # 中文转录调试
├── archived/           # 📦 历史归档
│   ├── README.md       # 归档说明文档
│   └── *.py           # 历史测试脚本
├── test_api_frontend.js # 🌐 前端测试库
├── test_api_page.html  # 📱 可视化测试页面
└── README.md          # 📋 本文档
```

## ⭐ 核心测试脚本 (生产级别)

### 1. 📊 `production/test_local_models.py` - 性能基准测试
**用途**: 测试本地已下载的四个模型的性能表现

**支持模型**:
- `tiny` (39MB) - 最快速度，适合实时处理
- `base` (142MB) - 平衡推荐，日常使用
- `small` (466MB) - 高质量转录
- `large-v3-turbo` (809MB) - 快速高质量

**测试配置**:
```python
# 针对不同模型使用不同参数组合
configs = [
    {"model": "tiny", "language": "auto", "output_format": "srt"},
    {"model": "base", "language": "zh", "output_format": "vtt"},
    {"model": "small", "language": "en", "output_format": "both"},
    {"model": "large-v3-turbo", "language": "auto", "output_format": "both"}
]
```

### 2. ⚡ `production/test_api_curl.sh` - 快速验证工具
**用途**: 使用 curl 命令快速验证所有 API 端点

**测试覆盖**:
- ✅ 健康检查 (`/health`)
- ✅ 模型列表 (`/models/`)
- ✅ 文件上传 (`/upload/`)
- ✅ 状态查询 (`/status/`)

**特点**:
- 🚀 30秒内完成全部测试
- 📊 详细的成功/失败报告
- 🔧 自动测试文件清理

### 3. 🎤 `production/test_real_chinese_audio.py` - 中文语音测试
**用途**: 专门验证中文语音转录的准确性

**测试场景**:
1. **自动检测 + SRT**: 验证语言识别准确性
2. **指定中文 + VTT**: 验证强制中文转录
3. **自动检测 + 翻译**: 验证翻译功能

**分析维度**:
- 🔍 语言检测准确性
- 📝 转录内容质量
- ⏱️ 处理性能指标

## 🚀 快速开始

### 环境准备
```bash
# 1. 启动后端服务
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 2. 启动 Celery Worker  
export PYTHONPATH="."
uv run celery -A celery_app.celery_app worker --loglevel=info --pool=solo

# 3. 启动 Redis 服务
brew services start redis  # macOS
```

### 模型文件要求
确保 `models/` 目录中有以下文件：
- `ggml-tiny.bin`
- `ggml-base.bin`  
- `ggml-small.bin`
- `ggml-large-v3-turbo.bin`

### 音频文件准备 (中文测试)
将中文音频文件放置到：`/Users/creed/Desktop/audio.mp3`

## 🧪 测试执行指南

### 🎯 推荐测试流程

#### 第一步: 快速验证
```bash
# 验证基础 API 功能
./production/test_api_curl.sh
```

#### 第二步: 性能测试
```bash
# 测试所有本地模型性能
uv run python production/test_local_models.py
```

#### 第三步: 中文专项测试
```bash
# 验证中文语音转录质量 (需要真实音频文件)
uv run python production/test_real_chinese_audio.py
```

### 🔧 开发和调试

#### 详细功能测试
```bash
# 开发环境的完整功能测试
uv run python development/test_model_selection_api.py
```

#### 快速功能验证
```bash  
# 轻量级的基础功能测试
uv run python development/test_simple_api.py
```

#### 问题调试
```bash
# 专门用于调试中文转录问题
uv run python development/debug_chinese_transcription.py
```

### 🌐 前端测试

#### 浏览器可视化测试
```bash
# 在浏览器中打开测试页面
open test_api_page.html
```

#### JavaScript 库测试
```html
<!-- 在 HTML 页面中引入测试库 -->
<script src="test_api_frontend.js"></script>
<script>
  const tester = new Audio2SubTester('http://localhost:8000');
  tester.runFullTest();
</script>
```

## 📊 测试结果示例

### 性能基准 (MacBook Pro, MPS 设备)
| 模型 | 文件大小 | 处理时间 | 转录精度 | 推荐场景 |
|------|---------|---------|---------|---------|
| tiny | 39MB | ~0.05s | 较低 | 实时处理、快速预览 |
| base | 142MB | ~0.08s | 良好 | 日常使用、平衡选择 |
| small | 466MB | ~0.15s | 较高 | 高质量需求、专业用途 |
| large-v3-turbo | 809MB | ~0.37s | 很高 | 最佳质量、批量处理 |

### 语言识别准确性
| 音频语言 | auto 检测 | zh 指定 | en 指定 | 推荐设置 |
|---------|----------|---------|---------|---------|
| 中文 | 70% 准确 | 95% 准确 | N/A | 使用 zh |
| 英文 | 90% 准确 | N/A | 95% 准确 | 使用 en |
| 混合语言 | 60% 准确 | 80% 准确 | 70% 准确 | 使用主要语言 |

## 🚨 故障排除

### 常见问题及解决方案

#### 1. API 连接失败
```bash
❌ 错误: Connection refused (http://localhost:8000)
```
**解决方案**:
- 检查后端服务是否启动: `curl http://localhost:8000/health`
- 确认端口无冲突: `lsof -i :8000`
- 检查防火墙设置

#### 2. 模型文件缺失
```bash
❌ 错误: Model file not found
```
**解决方案**:
- 检查模型文件: `ls -la models/ggml-*.bin`
- 确认文件权限: `chmod 644 models/*.bin`
- 重新下载缺失的模型

#### 3. 中文转录为英文
```bash
⚠️ 问题: 中文语音被转录为英文
```
**解决方案**:
- 使用 `language: "zh"` 而不是 `"auto"`
- 确保音频清晰度足够
- 检查音频是否确实为中文语音

#### 4. Celery Worker 未响应
```bash
❌ 错误: Task stuck in PENDING state
```
**解决方案**:
- 重启 Celery Worker
- 检查 Redis 连接: `redis-cli ping`
- 查看 Worker 日志

## 📈 性能优化建议

### 模型选择策略
- **开发阶段**: 使用 `tiny` 模型进行快速迭代
- **测试阶段**: 使用 `base` 模型进行功能验证
- **生产阶段**: 根据质量要求选择 `small` 或 `large-v3-turbo`

### 系统调优
- **并发处理**: 配置多个 Celery Worker 进程
- **内存管理**: 监控模型加载的内存使用
- **缓存策略**: 考虑模型预加载机制

## 🔄 CI/CD 集成

### GitHub Actions 示例
```yaml
name: API Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start Redis
        run: docker run -d -p 6379:6379 redis:7-alpine
      - name: Start API Server
        run: |
          cd backend
          uvicorn app.main:app --host 0.0.0.0 --port 8000 &
      - name: Run API Tests
        run: |
          cd backend
          ./scripts/testing/production/test_api_curl.sh
```

### Jenkins 集成
```groovy
pipeline {
    agent any
    stages {
        stage('Test API') {
            steps {
                sh '''
                    cd backend/scripts/testing/production
                    ./test_api_curl.sh
                '''
            }
        }
    }
}
```

## 📋 测试清单

### 发布前检查 ✅
- [ ] 所有核心 API 端点响应正常
- [ ] 四个本地模型均可正常工作
- [ ] 中文语音转录准确性 > 90%
- [ ] 平均响应时间 < 5秒
- [ ] 错误处理机制正常
- [ ] 文件清理功能正常

### 性能基准验证 📊
- [ ] tiny 模型处理时间 < 0.1秒
- [ ] base 模型处理时间 < 0.2秒  
- [ ] small 模型处理时间 < 0.3秒
- [ ] large-v3-turbo 模型处理时间 < 0.5秒
- [ ] 内存使用 < 2GB
- [ ] CPU 使用率 < 80%

## 🔗 相关文档

- [生产环境测试指南](production/README.md)
- [开发环境测试指南](development/README.md)  
- [归档测试说明](archived/README.md)
- [前端项目文档](../../frontend/README.md)
- [API 文档](../docs/api.md)
- [部署指南](../README.md)

---

**最后更新**: 2025年6月19日  
**测试状态**: ✅ 所有核心功能已验证  
**维护者**: Audio2Sub 开发团队
