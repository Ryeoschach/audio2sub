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
- 🌓 **主题切换**: 支持浅色/深色主题自由切换，个性化用户界面

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
- **主题系统**: 基于 Context API 的浅色/深色主题切换

### 部署
- **Docker & Docker Compose**: 容器化部署
- **uv**: 快速的 Python 包管理器

## 🚀 快速开始

### 方式一：本地开发

1. **后端环境**
```bash
cd backend
uv sync --locked
```

2. **启动 Redis**
```bash
redis-server
```

3. **启动 Celery Worker**
```bash
uv run celery -A celery_app.celery_app worker --loglevel=info --pool=solo
```

4. **启动后端服务**
```bash
uv run uvicorn app.main:app --reload --port 8000
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

## 🎛️ 使用指南

### 前端界面操作
1. 📁 选择或拖拽音频/视频文件
2. 🚀 点击上传开始处理
3. ⏱️ 实时查看处理进度和时间
4. 📄 下载生成的 SRT/VTT 字幕文件
5. 🌓 使用右上角切换按钮自由切换浅色/深色主题

### 支持的文件格式
- **音频**: MP3, WAV, FLAC, M4A, AAC, OGG, WMA
- **视频**: MP4, AVI, MOV, MKV, WEBM, FLV, WMV

### 字幕质量优化
- ✅ 智能分段：自动在合适的位置分割字幕
- ✅ 时间同步：精确的时间戳对齐
- ✅ 语义完整：优先在句子边界分段
- ✅ 长度控制：避免过长或过短的字幕条目

### 主题切换功能
- 🌞 **浅色主题**: 适合白天使用，提供清爽明亮的界面
- 🌙 **深色主题**: 适合夜间使用，减少眼部疲劳
- 🔄 **一键切换**: 点击右上角的主题切换按钮即可切换
- 💾 **偏好记忆**: 主题偏好自动保存到本地存储，下次访问自动应用
- ⚡ **平滑过渡**: 主题切换时带有平滑的过渡动画效果

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
    ├── src/               # 源代码
    │   ├── components/    # React 组件
    │   │   └── ThemeToggle.tsx  # 主题切换组件
    │   ├── contexts/      # React 上下文
    │   │   └── ThemeContext.tsx # 主题上下文管理
    │   └── App.tsx        # 应用入口
    └── package.json       # Node.js 依赖

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
4. **转录速度慢**: 检查是否启用硬件加速 (MPS/CUDA/CPU)

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

### v2.1.0 (2025-01-XX)
- 🌓 **主题切换功能**: 新增浅色/深色主题支持
- 🎨 **界面优化**: 重构样式系统，支持主题感知的UI组件
- 💾 **偏好存储**: 主题偏好自动保存到本地存储
- ⚡ **平滑过渡**: 主题切换时的动画效果优化
- 🔧 **技术升级**: 采用 Context API 和 CSS 变量系统

### v2.0.0 (2025-06-16)
- 🚀 **重大性能优化**: 切换到 transformers pipeline
- ⏱️ **时间跟踪功能**: 详细的性能监控
- 🔇 **警告优化**: 清洁的控制台输出
- ⚡ **速度提升**: 批处理和硬件加速优化

### v1.0.0
- 🎉 **基础功能**: 音频/视频转字幕
- 🌐 **Web 界面**: React + FastAPI 架构

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

*最后更新：2025年6月16日*

