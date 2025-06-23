# 📋 Audio2Sub Backend 项目概览

## 🗂️ 整理后的目录结构

```
backend/
├── 📁 app/                      # 核心应用代码
│   ├── main.py                  # FastAPI 主应用入口
│   ├── config.py               # 全局配置管理
│   ├── tasks.py                # Celery 异步任务
│   ├── whisper_manager.py      # Whisper 引擎管理
│   └── ...                     # 其他业务逻辑
│
├── 📖 docs/                     # 项目文档（已整理）
│   ├── README.md               # 文档目录说明
│   ├── config/                 # 配置相关文档
│   │   └── whisper-precision-configuration.md
│   ├── deployment/             # 部署相关文档
│   │   ├── DOCKER_FIXES_SUMMARY.md
│   │   ├── FINAL_DEPLOYMENT_REPORT.md
│   │   ├── README_DEPLOYMENT.md
│   │   └── README_UPDATE_20250616.md
│   └── migration/              # 迁移升级文档
│       ├── MIGRATION_FINAL_SUMMARY.md
│       ├── PROJECT_STATUS_FINAL.md
│       ├── README_WHISPER_CPP.md
│       ├── WHISPER_CPP_MIGRATION_COMPLETED.md
│       ├── WHISPER_CPP_MIGRATION_FINAL_REPORT.md
│       └── WHISPER_CPP_MIGRATION_SUMMARY.md
│
├── 🔧 scripts/                  # 脚本工具（已整理）
│   ├── README.md               # 脚本目录说明
│   ├── deployment/             # 部署脚本
│   │   ├── deploy_whisper.sh
│   │   ├── smart_deploy.sh
│   │   └── smart_deploy_v2.sh
│   ├── development/            # 开发辅助脚本
│   │   ├── manage.sh
│   │   ├── quick_start.sh
│   │   ├── final_status_report.py
│   │   └── start_server.py
│   └── testing/                # 测试脚本
│       ├── rebuild_and_test.sh
│       ├── performance_test.sh
│       ├── run_tests.sh
│       ├── test_whisper_detection.sh
│       ├── test_chinese_transcription.py
│       ├── test_docker_compose_e2e.py
│       └── docker_test.py
│
├── 🧪 tests/                    # 测试代码
│   ├── README.md
│   ├── units/                  # 单元测试
│   ├── debug/                  # 调试测试
│   └── ...                     # 集成测试
│
├── 🤖 models/                   # AI 模型存储
├── 📤 uploads/                  # 文件上传目录
├── 📥 results/                  # 结果输出目录
│
├── 🐳 Docker 配置文件
│   ├── Dockerfile.cpu          # CPU 版本构建
│   ├── Dockerfile.gpu          # GPU 版本构建
│   ├── Dockerfile.mps          # Apple Silicon 版本
│   ├── docker-compose.cpu.yml  # CPU 部署配置
│   ├── docker-compose.gpu.yml  # GPU 部署配置
│   └── ...                     # 其他部署配置
│
└── 📋 配置文件
    ├── README.md               # 主说明文档（已更新）
    ├── pyproject.toml          # Python 项目配置
    ├── requirements.txt        # Python 依赖
    ├── .gitignore             # Git 忽略规则（新建）
    └── celery_app.py          # Celery 配置
```

## 📊 整理成果统计

### 📖 文档整理
- **配置文档**: 1个文件 → `docs/config/`
- **部署文档**: 4个文件 → `docs/deployment/`
- **迁移文档**: 6个文件 → `docs/migration/`
- **总计**: 11个 Markdown 文档已分类整理

### 🔧 脚本整理
- **部署脚本**: 3个文件 → `scripts/deployment/`
- **开发脚本**: 4个文件 → `scripts/development/`
- **测试脚本**: 7个文件 → `scripts/testing/`
- **总计**: 14个脚本文件已分类整理

## 🎯 目录作用说明

### 📖 docs/ - 文档中心
| 子目录 | 作用 | 主要内容 |
|--------|------|----------|
| `config/` | 配置说明 | Whisper 精度配置等 |
| `deployment/` | 部署指南 | Docker 部署、修复记录 |
| `migration/` | 迁移记录 | Whisper.cpp 迁移历史 |

### 🔧 scripts/ - 脚本工具
| 子目录 | 作用 | 主要内容 |
|--------|------|----------|
| `deployment/` | 自动化部署 | 智能部署、模型部署 |
| `development/` | 开发辅助 | 快速启动、服务器管理 |
| `testing/` | 测试验证 | 性能测试、功能测试 |

### 🧪 tests/ - 测试代码
| 子目录 | 作用 | 主要内容 |
|--------|------|----------|
| `units/` | 单元测试 | 组件级别测试 |
| `debug/` | 调试测试 | 问题排查测试 |
| 根目录 | 集成测试 | 端到端功能测试 |

## 🚀 快速导航

### 🔍 查找文档
```bash
# 查看所有文档
find docs/ -name "*.md" -type f

# 查找部署相关文档
ls docs/deployment/

# 查找配置文档
ls docs/config/
```

### ⚡ 执行脚本
```bash
# 快速启动开发环境
./scripts/development/quick_start.sh

# 运行所有测试
./scripts/testing/run_tests.sh

# 智能部署
./scripts/deployment/smart_deploy_v2.sh
```

### 🧪 运行测试
```bash
# 单元测试
pytest tests/units/

# 集成测试
python tests/test_comprehensive.py

# 性能测试
./scripts/testing/performance_test.sh
```

## 📝 更新说明

### ✅ 已完成
1. **文档分类整理**: 将散落的 MD 文件按功能分类到 `docs/` 子目录
2. **脚本统一管理**: 将各种脚本按用途分类到 `scripts/` 子目录
3. **目录说明文档**: 为每个主要目录创建 README.md 说明文档
4. **主 README 更新**: 更新项目主说明文档，包含完整的使用指南
5. **Git 配置**: 创建 `.gitignore` 文件，规范版本控制

### 📋 目录对照表
| 原位置 | 新位置 | 类型 |
|--------|--------|------|
| `DOCKER_FIXES_SUMMARY.md` | `docs/deployment/` | 文档 |
| `FINAL_DEPLOYMENT_REPORT.md` | `docs/deployment/` | 文档 |
| `README_DEPLOYMENT.md` | `docs/deployment/` | 文档 |
| `README_UPDATE_20250616.md` | `docs/deployment/` | 文档 |
| `MIGRATION_FINAL_SUMMARY.md` | `docs/migration/` | 文档 |
| `PROJECT_STATUS_FINAL.md` | `docs/migration/` | 文档 |
| `README_WHISPER_CPP.md` | `docs/migration/` | 文档 |
| `WHISPER_CPP_*.md` | `docs/migration/` | 文档 |
| `whisper-precision-configuration.md` | `docs/config/` | 文档 |
| `deploy_whisper.sh` | `scripts/deployment/` | 脚本 |
| `smart_deploy*.sh` | `scripts/deployment/` | 脚本 |
| `manage.sh` | `scripts/development/` | 脚本 |
| `quick_start.sh` | `scripts/development/` | 脚本 |
| `final_status_report.py` | `scripts/development/` | 脚本 |
| `start_server.py` | `scripts/development/` | 脚本 |
| `*test*.sh` | `scripts/testing/` | 脚本 |
| `*test*.py` | `scripts/testing/` | 脚本 |

现在项目结构更加清晰，文档和脚本都有了统一的组织方式！🎉
