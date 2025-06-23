# Audio2Sub 智能部署架构

## 🎯 设计目标

解决Docker容器中无法充分利用硬件加速的问题，提供多种部署模式以适应不同的环境和性能需求。

## 📋 部署模式对比

| 模式 | 适用场景 | 性能 | 复杂度 | GPU/MPS支持 |
|------|----------|------|--------|-------------|
| **Native** | 开发环境 | 最佳 | 低 | ✅ 完全支持 |
| **Hybrid** | 生产推荐 | 很好 | 中 | ✅ 宿主机支持 |
| **GPU** | 云部署 | 很好 | 高 | ✅ CUDA支持 |
| **CPU** | 通用部署 | 一般 | 低 | ❌ 仅CPU |

## 🚀 快速开始

### 智能部署（推荐）

```bash
# 自动检测最佳部署模式
./smart_deploy.sh

# 或指定特定模式
./smart_deploy.sh hybrid
```

### 手动部署

#### 1. Native模式（开发推荐）

**优势**: 最佳性能，支持所有硬件加速
**适用**: 开发环境，macOS with Apple Silicon

```bash
# 启动Redis
docker-compose -f docker-compose.native.yml up -d

# 设置环境变量
export DEPLOYMENT_MODE=native
export REDIS_HOST=127.0.0.1
export REDIS_PORT=16379

# 直接运行应用
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 或运行worker
celery -A celery_app worker --loglevel=info
```

#### 2. Hybrid模式（生产推荐）

**优势**: 容器化管理 + 宿主机性能
**适用**: 生产环境，有宿主机whisper.cpp

```bash
# 确保宿主机有whisper.cpp
ls -la /usr/local/bin/whisper-cli

# 启动混合部署
docker-compose -f docker-compose.hybrid.yml up -d
```

#### 3. GPU模式（云部署）

**优势**: CUDA加速，完全容器化
**适用**: Linux + NVIDIA GPU

```bash
# 需要nvidia-docker2
docker-compose -f docker-compose.gpu-new.yml up -d
```

#### 4. CPU模式（通用部署）

**优势**: 兼容性最好，无特殊要求
**适用**: 任何Docker环境

```bash
docker-compose -f docker-compose.cpu.yml up -d
```

## 🔧 配置详解

### 动态设备检测

新的配置系统会自动检测并选择最佳设备：

```python
# 自动检测结果示例
{
    "deployment_mode": "hybrid",
    "device": "mps",           # macOS Apple Silicon
    "threads": 0,              # 使用所有CPU核心
    "processors": 1,           # Metal只需1个处理器
    "compute_type": "float32", # MPS优化精度
    "platform": "Darwin",
    "cpu_count": 8
}
```

### 环境变量覆盖

可以通过环境变量强制指定配置：

```bash
export DEPLOYMENT_MODE=hybrid
export WHISPER_DEVICE=mps
export WHISPER_COMPUTE_TYPE=float32
export HOST_WHISPER_CPP_PATH=/usr/local/bin/whisper-cli
```

## 📊 性能测试

运行性能基准测试：

```bash
# 使用默认测试文件
./performance_test.sh

# 使用自定义测试文件
./performance_test.sh /path/to/your/audio.wav
```

测试结果示例：
```
| 部署模式 | 耗时(秒) | 相对性能 |
|----------|----------|----------|
| hybrid   | 15       | 1.00x    |
| cpu      | 45       | 3.00x    |
| gpu      | 12       | 0.80x    |
```

## 🏗️ 架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Native Mode   │    │  Hybrid Mode    │    │   GPU Mode      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ ✅ 应用(宿主机)  │    │ 🐳 应用(容器)    │    │ 🐳 应用(容器)    │
│ ✅ Whisper(宿主) │    │ ✅ Whisper(宿主) │    │ 🐳 Whisper(容器) │
│ 🐳 Redis(容器)  │    │ 🐳 Redis(容器)   │    │ 🐳 Redis(容器)   │
│                │    │                │    │                │
│ 🚀 最佳性能     │    │ ⚖️ 平衡方案      │    │ 🔥 CUDA加速     │
│ 🛠️ 开发友好     │    │ 📦 生产就绪      │    │ ☁️ 云原生       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔍 健康检查

每种模式都提供详细的健康检查信息：

```bash
curl http://localhost:8000/health
```

返回示例：
```json
{
  "status": "healthy",
  "whisper_cpp": "available",
  "model": "available", 
  "redis": "connected",
  "deployment": {
    "deployment_mode": "hybrid",
    "device": "mps",
    "threads": 0,
    "processors": 1,
    "compute_type": "float32",
    "whisper_path": "/usr/local/bin/whisper-cli",
    "model_path": "/app/models/ggml-base.bin",
    "platform": "Darwin",
    "cpu_count": 8,
    "in_docker": true
  }
}
```

## 🐛 故障排除

### 1. Hybrid模式问题

**问题**: 容器无法访问宿主机whisper.cpp
```bash
# 检查文件存在
ls -la /usr/local/bin/whisper-cli

# 检查权限
chmod +x /usr/local/bin/whisper-cli

# 检查挂载路径
docker exec -it audio2sub_backend_hybrid ls -la /usr/local/bin/whisper-cli
```

### 2. GPU模式问题

**问题**: NVIDIA Docker不可用
```bash
# 安装nvidia-docker2
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# 测试GPU访问
docker run --rm --gpus all nvidia/cuda:11.8-base nvidia-smi
```

### 3. 性能问题

**问题**: 转录速度慢
```bash
# 检查设备使用情况
curl http://localhost:8000/health | jq '.deployment'

# 运行性能测试
./performance_test.sh

# 调整配置
export WHISPER_THREADS=0  # 使用所有核心
export WHISPER_COMPUTE_TYPE=int8  # CPU优化
```

## 📝 开发指南

### 添加新的部署模式

1. 创建新的Dockerfile（如`Dockerfile.newmode`）
2. 创建对应的docker-compose文件
3. 在`smart_deploy.sh`中添加检测逻辑
4. 更新配置文件的设备检测函数

### 自定义设备检测

```python
# 在config.py中添加新的检测函数
def _detect_custom_device(self) -> str:
    # 自定义检测逻辑
    if self._check_custom_hardware():
        return "custom"
    return "cpu"
```

## 📚 参考资料

- [whisper.cpp 官方文档](https://github.com/ggerganov/whisper.cpp)
- [Docker GPU 支持](https://docs.docker.com/config/containers/resource_constraints/#gpu)
- [Apple Metal Performance Shaders](https://developer.apple.com/documentation/metalperformanceshaders)
- [NVIDIA Docker 安装指南](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
