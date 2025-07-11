# 🎵 Audio2Sub Backend

音频/视频文件转字幕的后端服务，支持多种语言和部署方式。

## 🏗️ 项目结构

```
backend/
├── 📁 app/                      # 主应用代码
│   ├── main.py                  # FastAPI 主应用
│   ├── config.py               # 配置管理
│   ├── tasks.py                # Celery 任务
│   └── whisper_manager.py      # Whisper 管理器
├── 📁 docs/                     # 📖 项目文档
│   ├── config/                 # 配置相关文档
│   ├── deployment/             # 部署相关文档
│   └── migration/              # 迁移和升级文档
├── 📁 scripts/                  # 🔧 脚本工具
│   ├── deployment/             # 部署脚本
│   ├── development/            # 开发辅助脚本
│   └── testing/                # 测试脚本
├── 📁 tests/                    # 🧪 测试代码
│   ├── units/                  # 单元测试
│   └── debug/                  # 调试测试
├── 📁 models/                   # 🤖 AI 模型文件
├── 📁 uploads/                  # 📤 上传文件目录
├── 📁 results/                  # 📥 结果文件目录
├── 🐳 Dockerfile*              # Docker 构建文件
├── 🐳 docker-compose*.yml      # Docker Compose 配置
├── 📋 pyproject.toml           # Python 项目配置
└── 📋 requirements.txt         # Python 依赖
```

## 🚀 快速开始

### 方法二：使用开发脚本

```bash
# 快速启动开发环境
./scripts/development/quick_start.sh

# 或使用项目管理脚本
./scripts/development/manage.sh
```

### 方法三：手动启动

```bash
# 1. 安装依赖
uv sync 

# 2. 启动 Redis
redis-server

# 3. 启动 Celery Worker
celery -A celery_app.celery_app worker --loglevel=info (单进程)
# 或者使用多进程
celery -A celery_app.celery_app worker --loglevel=info --concurrency 4 (4进程)

# 4. 启动 API 服务
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5、 启动前端服务
cd frontend
npm install
npm run dev
```


## 🔧 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `WHISPER_DEVICE` | `auto` | 推理设备 (cpu/cuda/metal) |
| `MODEL_NAME` | `base` | Whisper 模型大小 |
| `REDIS_HOST` | `localhost` | Redis 主机地址 |
| `REDIS_PORT` | `6379` | Redis 端口 |
| `DEBUG` | `False` | 调试模式 |

### 模型支持

- `tiny`: 最快，准确度较低
- `base`: 平衡速度和准确度（推荐）
- `small`: 更高准确度
- `medium`: 高准确度
- `large`: 最高准确度，速度较慢

## 🎯 API 使用

### 上传文件转录
```bash
curl -X POST "http://localhost:8000/transcribe" \
  -F "file=@audio.mp3" \
  -F "output_format=srt"
```

### 获取任务状态
```bash
curl "http://localhost:8000/task/{task_id}/status"
```

### 下载结果
```bash
curl "http://localhost:8000/download/{task_id}.srt"
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 故障排除

### 常见问题

1. **Whisper.cpp 找不到**
   - 检查 Docker 构建日志
   - 验证 `/usr/local/bin/whisper-cli` 是否存在

2. **Redis 连接失败**
   - 检查 Redis 服务是否启动
   - 验证网络配置

3. **模型下载失败**
   - 检查网络连接
   - 手动下载模型到 `models/` 目录

更多问题请查看 [部署文档](docs/deployment/) 或提交 Issue。

## 🔗 相关链接

- [前端项目](../frontend/)
- [移动端项目](../mobile/)
- [Docker Hub](https://hub.docker.com/)
- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp)

## 🗂️ 项目整理说明

本项目已完成目录结构优化整理：

### 📖 文档整理 (`docs/`)
- **配置文档**: `docs/config/` - Whisper 配置说明
- **部署文档**: `docs/deployment/` - Docker 部署指南
- **迁移文档**: `docs/migration/` - 版本迁移记录
- **项目概览**: `docs/PROJECT_OVERVIEW.md` - 完整的项目结构说明
