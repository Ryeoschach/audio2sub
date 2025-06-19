# Audio2Sub Backend - Whisper.cpp Integration

## 概述

这个版本的Audio2Sub Backend已经从原来的transformers/torch实现迁移到whisper.cpp，提供更好的性能和设备兼容性。

## 主要改进

### ✅ 已完成的迁移

1. **依赖迁移** - 从torch/transformers迁移到whisper.cpp
2. **配置重构** - 新的whisper.cpp专用配置参数
3. **核心逻辑重写** - tasks.py使用whisper.cpp进行语音识别
4. **多设备支持** - CPU、GPU、MPS专用Docker配置
5. **模型管理** - 自动下载和管理whisper.cpp模型

### 🏗️ 新架构

- **WhisperManager**: 管理whisper.cpp模型和推理
- **多Dockerfile支持**: CPU、GPU、MPS专用容器
- **自动设备检测**: 根据系统自动选择最佳设备
- **模型下载**: 自动下载所需的whisper.cpp模型

## 快速开始

### 1. 使用uv运行（推荐）

```bash
# 安装依赖
uv sync

# 启动服务
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 使用Docker部署

#### 自动检测设备
```bash
./deploy_whisper.sh auto
```

#### 指定设备类型
```bash
# CPU专用
./deploy_whisper.sh cpu

# NVIDIA GPU
./deploy_whisper.sh gpu

# Apple Silicon MPS
./deploy_whisper.sh mps
```

### 3. 手动Docker部署

```bash
# CPU版本
docker-compose -f docker-compose.cpu.yml up --build

# GPU版本（需要NVIDIA Docker）
docker-compose -f docker-compose.gpu.yml up --build

# MPS版本（Apple Silicon）
docker-compose -f docker-compose.mps.yml up --build
```

## 配置说明

### 环境变量

```bash
# Whisper.cpp 配置
WHISPER_DEVICE=auto          # auto, cpu, cuda, metal
WHISPER_THREADS=0            # 0 = 自动检测
WHISPER_LANGUAGE=auto        # auto 或指定语言代码
WHISPER_TASK=transcribe      # transcribe 或 translate
MODEL_NAME=base              # tiny, base, small, medium, large-v1/v2/v3

# 音频处理参数
WHISPER_TEMPERATURE=0.0      # 采样温度
WHISPER_BEST_OF=5           # 候选数量
WHISPER_BEAM_SIZE=5         # 束搜索大小
WHISPER_WORD_TIMESTAMPS=true # 词级时间戳

# 字幕生成参数
MAX_SUBTITLE_DURATION=4      # 最大字幕持续时间（秒）
MAX_WORDS_PER_SUBTITLE=8     # 每条字幕最大词数
MAX_CHARS_PER_SUBTITLE=50    # 每条字幕最大字符数
```

### 设备配置

| 设备类型 | 配置 | 适用场景 |
|---------|------|----------|
| CPU | `WHISPER_DEVICE=cpu` | 兼容所有系统，较慢 |
| CUDA | `WHISPER_DEVICE=cuda` | NVIDIA GPU加速 |
| Metal | `WHISPER_DEVICE=metal` | Apple Silicon加速 |

## API接口

### 健康检查
```bash
curl http://localhost:8000/ping
```

### 上传文件进行转录
```bash
curl -X POST "http://localhost:8000/upload/" \
  -F "file=@your_audio.mp3"
```

### 查询任务状态
```bash
curl http://localhost:8000/status/{task_id}
```

### 下载结果文件
```bash
curl http://localhost:8000/results/{file_id}/{filename}
```

## Docker配置详解

### 1. CPU版本 (Dockerfile.cpu)
- 基于 `python:3.11-slim`
- 适用于所有系统
- 最佳兼容性，性能较慢

### 2. GPU版本 (Dockerfile.gpu)
- 基于 `nvidia/cuda:12.1-devel-ubuntu22.04`
- 需要NVIDIA Docker运行时
- 高性能CUDA加速

### 3. MPS版本 (Dockerfile.mps)
- 基于 `python:3.11-slim`
- 针对Apple Silicon优化
- 使用Metal Performance Shaders

## 模型支持

支持的whisper.cpp模型：

| 模型 | 大小 | 用途 |
|------|------|------|
| tiny | ~39MB | 快速转录，准确性较低 |
| base | ~142MB | 平衡性能和准确性（推荐） |
| small | ~466MB | 更高准确性 |
| medium | ~1.5GB | 高准确性 |
| large-v1/v2/v3 | ~2.9GB | 最高准确性 |

模型会自动下载到 `models/` 目录。

## 性能对比

| 设备 | 相对速度 | 内存使用 | 适用场景 |
|------|----------|----------|----------|
| CPU | 1x | 低 | 开发、测试、小文件 |
| CUDA GPU | 5-10x | 中等 | 生产环境、大文件 |
| Apple Silicon MPS | 3-5x | 中等 | Mac开发、中等文件 |

## 故障排除

### 1. whisper.cpp未找到
```bash
# 安装whisper.cpp
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp
make
```

### 2. 模型下载失败
- 检查网络连接
- 手动下载模型到 `models/` 目录
- 检查磁盘空间

### 3. GPU不可用
```bash
# 检查NVIDIA驱动
nvidia-smi

# 检查Docker GPU支持
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### 4. 内存不足
- 使用更小的模型（tiny/base）
- 增加系统内存
- 调整Docker内存限制

## 监控和日志

### Flower监控界面
```bash
# 访问 http://localhost:5555
# 查看Celery任务状态和性能
```

### 查看日志
```bash
# Docker日志
docker-compose -f docker-compose.cpu.yml logs -f

# 特定服务日志
docker-compose -f docker-compose.cpu.yml logs -f backend
docker-compose -f docker-compose.cpu.yml logs -f celery-worker
```

## 开发指南

### 本地开发
```bash
# 安装开发依赖
uv sync

# 启动开发服务器
uv run uvicorn app.main:app --reload

# 启动Celery worker
uv run celery -A celery_app worker --loglevel=info
```

### 测试
```bash
# 运行测试
uv run python -m pytest

# 测试API
uv run python test_api.py
```

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 许可证

MIT License

## 更新日志

### v0.2.0 - Whisper.cpp集成
- ✅ 迁移到whisper.cpp
- ✅ 多设备Docker支持
- ✅ 自动模型管理
- ✅ 性能优化
- ✅ 部署脚本
