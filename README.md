# Audio2Sub - 音频/视频转字幕 Web 应用

> **最新更新 (2025-06-16):** 🚀 重大性能优化！切换到 transformers pipeline，添加智能字幕分段，支持详细时间跟踪。处理速度提升，字幕质量大幅改善！

本项目是一个基于 FastAPI 后端和 React 前端的 Web 应用，用于将音频或视频文件转换为高质量的字幕文件。

## ✨ 主要特性

- 🎙️ **多格式支持**: 支持 MP3, WAV, FLAC, M4A, MP4, AVI, MOV 等主流音视频格式
- 🚀 **高性能转录**: 基于 OpenAI Whisper 模型，支持 Apple Silicon (MPS) 硬件加速
- 📝 **智能分段**: 自动生成合理时长的字幕条目（6秒以内），支持自然语义断句
- ⏱️ **实时监控**: 详细的处理时间统计和进度跟踪
- 📄 **多格式输出**: 同时生成 SRT 和 WebVTT 格式字幕
- 🎛️ **可配置参数**: 灵活的性能和质量配置选项

## 🛠️ 技术栈

### 后端
- **FastAPI**: 现代化的 Python Web 框架
- **Celery**: 分布式任务队列，支持异步处理
- **Redis**: 消息代理和结果存储
- **Transformers**: Hugging Face 的 Whisper 模型实现
- **FFmpeg**: 音视频处理和格式转换

### 前端
- **React 18**: 现代化的前端框架
- **Vite**: 快速的构建工具
- **TypeScript**: 类型安全的 JavaScript
- **Tailwind CSS**: 实用优先的 CSS 框架

### 部署
- **Docker & Docker Compose**: 容器化部署
- **uv**: 快速的 Python 包管理器

## 📊 性能指标

- **处理速度**: 1:2 到 1:3 的处理比例（1分钟音频需要2-3分钟）
- **字幕精度**: 基于 `whisper-large-v3-turbo` 模型，高准确度
- **分段质量**: 智能分段，单个条目6秒以内，便于阅读
- **硬件优化**: 支持 Apple Silicon MPS 加速

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

1. **克隆项目**
```bash
git clone <repository-url>
cd audio2sub
```

2. **启动服务**
```bash
docker-compose up --build
```

3. **访问应用**
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 方式二：本地开发

1. **后端环境**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. **启动 Redis**
```bash
redis-server
```

3. **启动 Celery Worker**
```bash
celery -A celery_app.celery_app worker --loglevel=info --pool=solo
```

4. **启动后端服务**
```bash
uvicorn app.main:app --reload --port 8000
```

5. **启动前端**
```bash
cd frontend
npm install
npm run dev
```

## 📡 API 接口

### 文件上传
```
POST /upload/
Content-Type: multipart/form-data
参数: file (音频/视频文件)
```

### 任务状态查询
```
GET /status/{task_id}
返回: 任务状态、进度、结果信息
```

### 结果下载
```
GET /results/{file_id}/{filename}
支持: .srt 和 .vtt 格式
```

### 响应示例
```json
{
  "state": "SUCCESS",
  "result": {
    "status": "Completed",
    "srt_path": "filename.srt",
    "vtt_path": "filename.vtt",
    "full_text": "转录的完整文本",
    "timing": {
      "total_time": 41.22,
      "total_time_formatted": "0:00:41",
      "transcription_time": 38.72,
      "ffmpeg_time": 2.35,
      "subtitle_generation_time": 0.15
    }
  }
}
```

## ⚙️ 配置参数

### 模型配置
```python
MODEL_NAME = "openai/whisper-large-v3-turbo"  # 转录模型
MODEL_DEVICE = "mps"  # 设备选择: mps/cuda/cpu
TORCH_DTYPE = "float16"  # 数据类型优化
```

### 性能配置
```python
BATCH_SIZE = 4  # 批处理大小
CHUNK_LENGTH_S = 30  # 音频块长度（秒）
STRIDE_LENGTH_S = 5  # 块重叠长度（秒）
```

### 字幕分段配置
```python
MAX_SUBTITLE_DURATION = 6  # 最大字幕时长（秒）
MAX_WORDS_PER_SUBTITLE = 10  # 最大词数
MAX_CHARS_PER_SUBTITLE = 60  # 最大字符数
```

## 🎛️ 使用指南

### 前端界面操作
1. 📁 选择或拖拽音频/视频文件
2. 🚀 点击上传开始处理
3. ⏱️ 实时查看处理进度和时间
4. 📄 下载生成的 SRT/VTT 字幕文件

### 支持的文件格式
- **音频**: MP3, WAV, FLAC, M4A, AAC, OGG, WMA
- **视频**: MP4, AVI, MOV, MKV, WEBM, FLV, WMV

### 字幕质量优化
- ✅ 智能分段：自动在合适的位置分割字幕
- ✅ 时间同步：精确的时间戳对齐
- ✅ 语义完整：优先在句子边界分段
- ✅ 长度控制：避免过长或过短的字幕条目

## 🔧 开发指南

### 项目结构
```
audio2sub/
├── backend/                 # FastAPI 后端
│   ├── app/                # 应用主代码
│   │   ├── main.py        # FastAPI 应用入口
│   │   ├── tasks.py       # Celery 任务定义
│   │   └── config.py      # 配置文件
│   ├── celery_app.py      # Celery 应用配置
│   └── requirements.txt   # Python 依赖
├── frontend/               # React 前端
│   ├── src/               # 源代码
│   └── package.json       # Node.js 依赖
└── docker-compose.yml     # Docker 编排文件
```

### 环境要求
- **Python**: 3.10+
- **Node.js**: 18+
- **Redis**: 6.0+
- **FFmpeg**: 4.0+
- **GPU**: 可选，支持 CUDA/MPS 加速

## 📈 性能监控

### 时间跟踪功能
系统提供详细的性能分析：
- 📁 文件处理时间（FFmpeg 音频提取）
- 🎙️ 转录时间（Whisper 模型推理）
- 📄 字幕生成时间
- 🎯 总处理时间

### 控制台输出示例
```
📁 Starting transcription task for file: example.mp3
🕐 Task started at: 2025-06-16 22:45:30
🎙️ Starting transcription with model: openai/whisper-large-v3-turbo
✅ Transcription completed
📄 SRT saved to: /path/to/result.srt
🏁 Task completed at: 2025-06-16 22:46:15
⏱️  TIMING SUMMARY:
   📁 File processing: 2.35s
   🎙️  Transcription: 38.72s
   📄 Subtitle generation: 0.15s
   🎯 TOTAL TIME: 41.22s (0:00:41)
```

## 🐛 故障排除

### 常见问题
1. **Redis 连接失败**: 检查 Redis 服务是否启动
2. **FFmpeg 未找到**: 确保系统已安装 FFmpeg
3. **内存不足**: 降低 `BATCH_SIZE` 参数
4. **转录速度慢**: 检查是否启用硬件加速 (MPS/CUDA)

### 日志查看
```bash
# Celery Worker 日志
celery -A celery_app.celery_app worker --loglevel=debug

# FastAPI 日志
uvicorn app.main:app --log-level debug
```

## 🔮 roadmap

- [ ] **WebSocket 支持**: 实时进度推送
- [ ] **多语言检测**: 自动识别音频语言
- [ ] **说话人分离**: 区分不同说话人
- [ ] **批量处理**: 支持多文件同时上传
- [ ] **字幕编辑**: 在线字幕编辑功能
- [ ] **API 认证**: 添加用户认证和限流

## 📝 更新日志

### v2.0.0 (2025-06-16)
- 🚀 **重大性能优化**: 切换到 transformers pipeline
- 📝 **智能字幕分段**: 6秒以内的合理时间段
- ⏱️ **时间跟踪功能**: 详细的性能监控
- 🔇 **警告优化**: 清洁的控制台输出
- ⚡ **速度提升**: 批处理和硬件加速优化

### v1.0.0
- 🎉 **基础功能**: 音频/视频转字幕
- 🌐 **Web 界面**: React + FastAPI 架构
- 🐳 **容器化**: Docker 部署支持

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

*最后更新：2025年6月16日*

