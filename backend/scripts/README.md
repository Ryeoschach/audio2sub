# 🔧 脚本目录结构

本目录包含 Audio2Sub Backend 项目的所有脚本文件。

## 🏗️ 目录结构

```
scripts/
├── README.md                    # 本文档，说明脚本目录结构
├── deployment/                  # 部署相关脚本
│   ├── deploy_whisper.sh
│   ├── smart_deploy.sh
│   └── smart_deploy_v2.sh
├── development/                 # 开发辅助脚本
│   ├── manage.sh
│   ├── quick_start.sh
│   ├── final_status_report.py
│   └── start_server.py
└── testing/                     # 测试相关脚本
    ├── rebuild_and_test.sh
    ├── performance_test.sh
    ├── run_tests.sh
    ├── test_whisper_detection.sh
    ├── test_chinese_transcription.py
    ├── test_docker_compose_e2e.py
    └── docker_test.py
```

## 🚀 脚本分类说明

### 📦 部署脚本 (`deployment/`)
用于项目部署和环境管理：

- **deploy_whisper.sh**: Whisper 模型部署脚本
- **smart_deploy.sh**: 智能部署脚本（v1）
- **smart_deploy_v2.sh**: 智能部署脚本（v2，推荐）

#### 使用示例：
```bash
# 执行智能部署
./scripts/deployment/smart_deploy_v2.sh

# 部署 Whisper 模型
./scripts/deployment/deploy_whisper.sh
```

### 🛠️ 开发脚本 (`development/`)
用于开发环境的管理和辅助工具：

- **manage.sh**: 项目管理脚本
- **quick_start.sh**: 快速启动脚本
- **final_status_report.py**: 生成项目状态报告
- **start_server.py**: 启动开发服务器

#### 使用示例：
```bash
# 快速启动开发环境
./scripts/development/quick_start.sh

# 启动开发服务器
python scripts/development/start_server.py

# 生成状态报告
python scripts/development/final_status_report.py
```

### 🧪 测试脚本 (`testing/`)
用于各种测试和验证：

#### Shell 脚本：
- **rebuild_and_test.sh**: 重建并测试完整流程
- **performance_test.sh**: 性能测试脚本
- **run_tests.sh**: 运行所有测试
- **test_whisper_detection.sh**: Whisper 检测测试

#### Python 测试脚本：
- **test_chinese_transcription.py**: 中文转录测试
- **test_docker_compose_e2e.py**: Docker Compose 端到端测试
- **docker_test.py**: Docker 容器测试

#### 使用示例：
```bash
# 运行所有测试
./scripts/testing/run_tests.sh

# 性能测试
./scripts/testing/performance_test.sh

# 中文转录测试
python scripts/testing/test_chinese_transcription.py

# Docker 端到端测试
python scripts/testing/test_docker_compose_e2e.py
```

## 🔧 脚本使用说明

### 📋 运行前准备
1. 确保脚本有执行权限：
   ```bash
   chmod +x scripts/**/*.sh
   ```

2. 检查依赖环境：
   ```bash
   # Python 脚本需要虚拟环境
   source .venv/bin/activate
   
   # Shell 脚本可能需要特定工具
   which docker docker-compose
   ```

### ⚡ 快速开始
```bash
# 1. 快速启动开发环境
./scripts/development/quick_start.sh

# 2. 运行基础测试
./scripts/testing/run_tests.sh

# 3. 部署到生产环境
./scripts/deployment/smart_deploy_v2.sh
```

### 🐛 故障排除
如果脚本执行失败，请检查：
1. 脚本执行权限
2. 依赖工具是否安装
3. 环境变量是否正确设置
4. 查看脚本内的注释说明

## 🔗 相关链接

- [主项目 README](../README.md)
- [文档目录说明](../docs/README.md)
- [测试目录说明](../tests/README.md)
