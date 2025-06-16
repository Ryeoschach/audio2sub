# 🎵 Audio2Sub - 音频转字幕系统

基于 FastAPI + Celery + React 的音频转字幕系统，使用 Whisper AI 模型进行高精度语音识别。

## 🚀 快速开始

### 前置要求
- Docker 和 Docker Compose
- Git

### 一键部署

```bash
# 克隆项目
git clone <your-repo-url>
cd audio2sub

# 启动开发环境
./deploy.sh dev

# 或启动生产环境
./deploy.sh prod
```

## 📋 目录结构

```
audio2sub/
├── backend/                 # Python FastAPI 后端
│   ├── Dockerfile          # 生产环境镜像
│   ├── Dockerfile.dev      # 开发环境镜像
│   ├── pyproject.toml      # uv 依赖管理
│   └── app/                # 应用代码
├── frontend/               # React 前端
│   ├── Dockerfile          # 前端镜像
│   └── src/                # 前端代码
├── docker-compose.yml      # 开发环境配置
├── docker-compose.prod.yml # 生产环境配置
├── deploy.sh              # 部署脚本
└── docs/                  # 文档
```

## 🛠️ 技术栈

### 后端
- **FastAPI** - 现代 Python Web 框架
- **Celery** - 分布式任务队列
- **Redis** - 消息队列和缓存
- **Faster-Whisper** - 高效的 Whisper 模型实现
- **uv** - 快速的 Python 包管理器

### 前端
- **React** - 用户界面库
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Tailwind CSS** - 样式框架

### 基础设施
- **Docker** - 容器化
- **Docker Compose** - 多容器编排

## 🔧 部署脚本使用

```bash
# 显示帮助信息
./deploy.sh help

# 启动开发环境（支持热重载）
./deploy.sh dev

# 启动生产环境（多 worker，重启策略）
./deploy.sh prod

# 查看服务状态
./deploy.sh status

# 查看服务日志
./deploy.sh logs

# 运行系统测试
./deploy.sh test

# 停止所有服务
./deploy.sh stop

# 清理 Docker 资源
./deploy.sh clean
```

## 🏗️ Docker 配置说明

### 开发环境 (`docker-compose.yml`)
- **特点**: 支持热重载，代码挂载，快速迭代
- **Dockerfile**: `Dockerfile.dev`
- **uvicorn**: `--reload` 模式
- **挂载**: 源代码目录挂载到容器

### 生产环境 (`docker-compose.prod.yml`)
- **特点**: 优化性能，多 worker，自动重启
- **Dockerfile**: `Dockerfile` (多阶段构建)
- **uvicorn**: `--workers 4` 多进程
- **重启策略**: `unless-stopped`

## 🎯 uv 优化亮点

### 为什么使用 uv？
1. **速度快**: 比 pip 快 10-100 倍
2. **锁定文件**: 确保依赖版本一致性
3. **现代化**: 支持 pyproject.toml 标准
4. **Docker 友好**: 优化的缓存和构建

### Docker 中的 uv 最佳实践

#### 生产环境 (多阶段构建)
```dockerfile
# 构建阶段 - 安装依赖到虚拟环境
FROM python:3.12-slim as builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
RUN uv sync --frozen --no-cache

# 运行阶段 - 复制虚拟环境
FROM python:3.12-slim
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
```

#### 开发环境 (单阶段构建)
```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
RUN uv sync --frozen --no-cache --system
```

## 🔍 服务访问

启动后可以访问以下服务：

| 服务 | 开发环境 | 生产环境 | 说明 |
|------|----------|----------|------|
| 后端 API | http://localhost:8000 | http://localhost:8000 | FastAPI 服务 |
| API 文档 | http://localhost:8000/docs | http://localhost:8000/docs | Swagger UI |
| 前端 | http://localhost:5173 | http://localhost:5173 | React 应用 |
| Redis | localhost:6379 | localhost:6379 | 密码: redispassword |

## 📊 监控和调试

### 查看容器状态
```bash
docker ps --filter "name=audio2sub"
```

### 查看容器日志
```bash
# 所有服务日志
./deploy.sh logs

# 特定服务日志
docker logs audio2sub_backend -f
docker logs audio2sub_celery_worker -f
```

### 进入容器调试
```bash
# 进入后端容器
docker exec -it audio2sub_backend bash

# 进入 Redis 容器
docker exec -it audio2sub_redis redis-cli -a redispassword
```

### 资源使用情况
```bash
docker stats --filter "name=audio2sub"
```

## 🧪 测试

### 自动化测试
```bash
./deploy.sh test
```

### 手动测试
```bash
# API 健康检查
curl http://localhost:8000/docs

# Redis 连接测试
docker exec audio2sub_redis redis-cli -a redispassword ping

# 上传音频文件测试
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.wav"
```

## 🔧 故障排除

### 常见问题

1. **端口被占用**
```bash
# 检查端口占用
lsof -i :8000
lsof -i :5173
lsof -i :6379

# 停止占用端口的进程
kill -9 <PID>
```

2. **权限问题**
```bash
# 修复文件权限
sudo chown -R $USER:$USER ./backend
sudo chown -R $USER:$USER ./frontend
```

3. **Docker 空间不足**
```bash
# 清理 Docker 资源
./deploy.sh clean

# 或手动清理
docker system prune -a -f
```

4. **依赖问题**
```bash
# 重新构建镜像
docker-compose build --no-cache
```

### 日志分析

```bash
# 查看构建日志
docker-compose build

# 查看运行时日志
docker-compose logs --tail=100 backend

# 查看 Celery 任务日志
docker-compose logs --tail=100 celery_worker
```

## 📚 开发指南

### 本地开发设置

1. **启动开发环境**
```bash
./deploy.sh dev
```

2. **代码修改**
   - 后端代码修改会自动重载（uvicorn --reload）
   - 前端代码修改会自动重载（Vite HMR）

3. **添加新的依赖**
```bash
# 进入后端容器
docker exec -it audio2sub_backend bash

# 使用 uv 添加依赖
uv add package-name

# 退出容器后重新构建
docker-compose build backend
```

### 生产部署

1. **环境变量配置**
   - 修改 `docker-compose.prod.yml` 中的环境变量
   - 建议使用 `.env` 文件管理敏感信息

2. **性能优化**
   - 调整 uvicorn workers 数量
   - 配置 Celery concurrency
   - 优化 Redis 内存设置

3. **安全加固**
   - 更改默认密码
   - 配置防火墙规则
   - 使用 HTTPS

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Whisper](https://github.com/openai/whisper) - OpenAI 的语音识别模型
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架
- [uv](https://github.com/astral-sh/uv) - 快速的 Python 包管理器
