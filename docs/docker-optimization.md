# Audio2Sub Docker 配置优化文档

## 🔧 问题分析

### 原始问题
1. **Docker Compose 语法错误**: 服务名包含中文注释导致YAML解析失败
2. **uv配置不一致**: Dockerfile使用uv但配置不够优化
3. **Python版本不匹配**: pyproject.toml要求Python >= 3.12，但Dockerfile使用3.9
4. **依赖管理混乱**: 同时存在requirements.txt和pyproject.toml

## ✅ 解决方案

### 1. 修复Docker Compose语法
- 移除了中文注释作为服务名
- 确保YAML格式正确

### 2. 优化uv使用
创建了两个Dockerfile：

#### `Dockerfile` (生产环境)
```dockerfile
# 多阶段构建，优化镜像大小
FROM python:3.12-slim as builder
# 使用官方uv镜像
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
# 使用uv sync进行依赖安装
RUN uv sync --frozen --no-cache
```

#### `Dockerfile.dev` (开发环境)
```dockerfile
# 单阶段构建，支持热重载
FROM python:3.12-slim
# 使用--system标志，适合容器环境
RUN uv sync --frozen --no-cache --system
```

### 3. 分离开发和生产环境

#### 开发环境 (`docker-compose.yml`)
- 使用`Dockerfile.dev`
- 挂载代码目录实现热重载
- 启用uvicorn的--reload模式

#### 生产环境 (`docker-compose.prod.yml`)
- 使用优化的`Dockerfile`
- 多worker配置
- 添加restart策略
- 不挂载源代码

### 4. 添加.dockerignore
优化构建性能，排除不必要的文件：
- 开发工具配置
- 测试文件
- 缓存目录
- 临时文件

## 🚀 使用方法

### 开发环境
```bash
# 启动开发环境
docker-compose up --build

# 重新构建并启动
docker-compose up --build --force-recreate
```

### 生产环境
```bash
# 启动生产环境
docker-compose -f docker-compose.prod.yml up --build -d

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

## 📋 配置对比

| 特性 | 开发环境 | 生产环境 |
|------|----------|----------|
| Dockerfile | Dockerfile.dev | Dockerfile |
| 构建策略 | 单阶段，快速构建 | 多阶段，优化大小 |
| 代码挂载 | ✅ 支持热重载 | ❌ 代码打包到镜像 |
| Uvicorn | --reload模式 | 多worker模式 |
| 重启策略 | 手动 | unless-stopped |
| 容器名后缀 | 无 | _prod |

## 🔍 uv最佳实践

### 1. 依赖锁定
```bash
# 生成/更新uv.lock文件
uv lock

# 同步依赖（安装）
uv sync
```

### 2. 容器中的uv使用
- **开发环境**: 使用`--system`标志直接安装到系统Python
- **生产环境**: 使用虚拟环境，通过多阶段构建复制

### 3. 缓存优化
- 使用`--no-cache`在Docker中避免缓存问题
- 使用`--frozen`确保使用精确的锁定版本

## 🐛 故障排除

### 常见问题

1. **权限问题**
```bash
# 确保Docker有权限访问目录
sudo chown -R $USER:$USER ./backend
```

2. **端口冲突**
```bash
# 检查端口占用
lsof -i :8000
lsof -i :6379
```

3. **构建缓存问题**
```bash
# 清理Docker缓存
docker system prune -f
docker builder prune -f
```

### 验证部署

1. **检查服务状态**
```bash
docker-compose ps
```

2. **查看日志**
```bash
docker-compose logs backend
docker-compose logs celery_worker
```

3. **测试API**
```bash
curl http://localhost:8000/docs
```

## 📚 相关资源

- [uv官方文档](https://docs.astral.sh/uv/)
- [Docker多阶段构建](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI部署指南](https://fastapi.tiangolo.com/deployment/)
- [Celery部署最佳实践](https://docs.celeryq.dev/en/stable/userguide/deploying.html)
