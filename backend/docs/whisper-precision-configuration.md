# Whisper 模型精度配置指南

本文档详细介绍了 `faster-whisper` 模型在 Audio2Sub 项目中的精度配置选项，帮助你根据不同需求优化转写效果。

## 目录

1. [概览](#概览)
2. [计算类型配置](#计算类型配置)
3. [模型大小选择](#模型大小选择)
4. [推理参数优化](#推理参数优化)
5. [预设配置方案](#预设配置方案)
6. [代码实现示例](#代码实现示例)
7. [环境变量配置](#环境变量配置)
8. [性能对比](#性能对比)
9. [故障排除](#故障排除)

## 概览

Whisper 模型的精度配置主要影响三个方面：
- **转写准确性**：更高精度的配置通常产生更准确的转写结果
- **处理速度**：精度和速度往往成反比关系
- **资源消耗**：高精度配置需要更多内存和计算资源

## 计算类型配置

### compute_type 参数

这是影响模型推理精度的最重要参数：

```python
# 可选的计算类型
COMPUTE_TYPE_OPTIONS = {
    "float32": {
        "精度": "最高",
        "速度": "最慢", 
        "内存": "最大",
        "适用": "追求最高精度的场景",
        "设备": "CPU/GPU"
    },
    "float16": {
        "精度": "高",
        "速度": "较快",
        "内存": "中等",
        "适用": "GPU环境下的平衡选择",
        "设备": "GPU（推荐）"
    },
    "int8": {
        "精度": "中等",
        "速度": "快",
        "内存": "小",
        "适用": "CPU环境下的推荐选择",
        "设备": "CPU/GPU"
    },
    "int8_float16": {
        "精度": "中高",
        "速度": "较快",
        "内存": "中小",
        "适用": "混合精度优化",
        "设备": "GPU"
    }
}
```

### 当前项目配置

```python
# app/config.py 中的配置
MODEL_COMPUTE_TYPE: str = "int8"  # CPU 友好的平衡选择
MODEL_DEVICE: str = "cpu"         # 使用 CPU
```

## 模型大小选择

### 模型规格对比

| 模型名称 | 参数量 | 精度等级 | 处理速度 | 内存需求 | 适用场景 |
|---------|--------|----------|----------|----------|----------|
| `tiny` | 39M | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | 实时转写、快速原型 |
| `base` | 74M | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | **推荐默认选择** |
| `small` | 244M | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 高质量转写 |
| `medium` | 769M | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | 专业级转写 |
| `large-v1` | 1550M | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | 最高精度需求 |
| `large-v2` | 1550M | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | 改进版最高精度 |
| `large-v3` | 1550M | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | 最新最高精度 |

### 模型选择建议

```python
# 根据使用场景选择模型
SCENARIO_MODEL_MAPPING = {
    "开发测试": "tiny",      # 快速迭代
    "日常使用": "base",      # 当前默认
    "内容创作": "small",     # 视频制作者
    "专业转写": "medium",    # 会议记录
    "学术研究": "large-v3",  # 最高精度要求
    "多语言": "large-v2",    # 更好的多语言支持
}
```

## 推理参数优化

### 核心参数说明

```python
def transcribe_with_precision_control(
    model, 
    audio_path, 
    precision_mode="balanced"
):
    """
    根据精度模式调整转写参数
    """
    base_params = {
        "beam_size": 5,              # 搜索宽度 (1-10)
        "best_of": 3,                # 候选数量 (1-5) 
        "patience": 1.0,             # 耐心参数 (0.0-2.0)
        "temperature": 0.0,          # 温度参数 (0.0-1.0)
        "repetition_penalty": 1.1,   # 重复惩罚 (1.0-2.0)
        "word_timestamps": True,     # 词级时间戳
        "condition_on_previous_text": True,  # 基于前文
        
        # 高级参数
        "compression_ratio_threshold": 2.4,  # 压缩比阈值
        "log_prob_threshold": -1.0,         # 日志概率阈值
        "no_speech_threshold": 0.6,         # 无语音阈值
        "length_penalty": 1.0,              # 长度惩罚
        "suppress_blank": True,             # 抑制空白
        "suppress_tokens": [-1],            # 抑制特定token
        "without_timestamps": False,        # 禁用时间戳
        "max_initial_timestamp": 1.0,      # 最大初始时间戳
        "prepend_punctuations": "\"'"¿([{-",
        "append_punctuations": "\"'.。,，!！?？:：")]}、"
    }
    
    return model.transcribe(audio_path, **base_params)
```

### 参数详细说明

#### beam_size (搜索宽度)
- **范围**: 1-10
- **作用**: 控制解码时的搜索宽度
- **影响**: 
  - 增大 → 更准确但更慢
  - 减小 → 更快但可能不够准确
- **建议**: 
  - 快速模式: 1-2
  - 平衡模式: 5
  - 精确模式: 8-10

#### best_of (候选数量)
- **范围**: 1-5
- **作用**: 生成多个候选结果并选择最佳
- **影响**: 
  - 增大 → 更准确但成倍增加计算时间
  - 减小 → 更快但精度降低
- **建议**:
  - 快速: 1
  - 平衡: 3
  - 精确: 5

#### temperature (温度参数)
- **范围**: 0.0-1.0
- **作用**: 控制输出的随机性
- **影响**:
  - 0.0 → 确定性输出（贪婪解码）
  - >0.0 → 增加随机性和多样性
- **建议**: 大多数情况使用 0.0

#### repetition_penalty (重复惩罚)
- **范围**: 1.0-2.0
- **作用**: 减少重复文本的生成
- **建议**: 1.1-1.2

#### no_speech_threshold (无语音阈值)
- **范围**: 0.0-1.0
- **作用**: 检测静音片段的敏感度
- **影响**:
  - 降低 → 更容易检测到语音（可能误判噪音）
  - 提高 → 更严格的语音检测（可能漏掉轻微语音）
- **建议**: 0.5-0.7

## 预设配置方案

### 1. 快速模式 (Fast Mode)

适用于：实时转写、快速预览、开发测试

```python
FAST_CONFIG = {
    "model_name": "tiny",
    "compute_type": "int8",
    "device": "cpu",
    "transcribe_params": {
        "beam_size": 1,                 # 贪婪搜索
        "best_of": 1,                   # 单一候选
        "temperature": 0.0,             # 确定性输出
        "word_timestamps": False,       # 禁用词级时间戳
        "condition_on_previous_text": False,
        "no_speech_threshold": 0.7,     # 较严格的语音检测
    }
}
```

### 2. 平衡模式 (Balanced Mode) - 推荐

适用于：日常使用、内容创作、一般转写需求

```python
BALANCED_CONFIG = {
    "model_name": "base",               # 当前默认
    "compute_type": "int8",             # 当前默认
    "device": "cpu",                    # 当前默认
    "transcribe_params": {
        "beam_size": 5,                 # 当前默认
        "best_of": 3,
        "patience": 1.0,
        "temperature": 0.0,
        "repetition_penalty": 1.1,
        "word_timestamps": True,        # 当前默认
        "condition_on_previous_text": True,
        "no_speech_threshold": 0.6,
        "compression_ratio_threshold": 2.4,
        "log_prob_threshold": -1.0,
    }
}
```

### 3. 高精度模式 (High Precision Mode)

适用于：专业转写、学术研究、重要会议记录

```python
HIGH_PRECISION_CONFIG = {
    "model_name": "large-v3",
    "compute_type": "float16",          # 需要GPU
    "device": "cuda",                   # 需要GPU
    "transcribe_params": {
        "beam_size": 10,                # 最大搜索宽度
        "best_of": 5,                   # 最多候选
        "patience": 2.0,                # 最大耐心
        "temperature": 0.0,             # 确定性输出
        "repetition_penalty": 1.2,      # 更强重复惩罚
        "word_timestamps": True,
        "condition_on_previous_text": True,
        "no_speech_threshold": 0.5,     # 更敏感的语音检测
        "compression_ratio_threshold": 2.4,
        "log_prob_threshold": -1.0,
        "length_penalty": 1.0,
        "suppress_blank": True,
    }
}
```

## 代码实现示例

### 1. 扩展配置类

```python
# app/config.py
from typing import Dict, Any
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # 精度配置
    PRECISION_MODE: str = "balanced"  # "fast", "balanced", "high"
    
    # 转写参数配置
    BEAM_SIZE: int = 5
    BEST_OF: int = 3
    PATIENCE: float = 1.0
    TEMPERATURE: float = 0.0
    REPETITION_PENALTY: float = 1.1
    NO_SPEECH_THRESHOLD: float = 0.6
    COMPRESSION_RATIO_THRESHOLD: float = 2.4
    LOG_PROB_THRESHOLD: float = -1.0
    
    # 高级配置
    ENABLE_WORD_TIMESTAMPS: bool = True
    CONDITION_ON_PREVIOUS_TEXT: bool = True
    MAX_INITIAL_TIMESTAMP: float = 1.0
    
    def get_precision_config(self) -> Dict[str, Any]:
        """根据精度模式返回配置"""
        if self.PRECISION_MODE == "fast":
            return {
                "model_name": "tiny",
                "compute_type": "int8",
                "transcribe_params": {
                    "beam_size": 1,
                    "best_of": 1,
                    "temperature": 0.0,
                    "word_timestamps": False,
                    "condition_on_previous_text": False,
                }
            }
        elif self.PRECISION_MODE == "high":
            return {
                "model_name": "large-v3",
                "compute_type": "float16" if self.MODEL_DEVICE == "cuda" else "int8",
                "transcribe_params": {
                    "beam_size": 10,
                    "best_of": 5,
                    "patience": 2.0,
                    "temperature": 0.0,
                    "repetition_penalty": 1.2,
                    "word_timestamps": True,
                    "condition_on_previous_text": True,
                    "no_speech_threshold": 0.5,
                }
            }
        else:  # balanced
            return {
                "model_name": self.MODEL_NAME,
                "compute_type": self.MODEL_COMPUTE_TYPE,
                "transcribe_params": {
                    "beam_size": self.BEAM_SIZE,
                    "best_of": self.BEST_OF,
                    "patience": self.PATIENCE,
                    "temperature": self.TEMPERATURE,
                    "repetition_penalty": self.REPETITION_PENALTY,
                    "word_timestamps": self.ENABLE_WORD_TIMESTAMPS,
                    "condition_on_previous_text": self.CONDITION_ON_PREVIOUS_TEXT,
                    "no_speech_threshold": self.NO_SPEECH_THRESHOLD,
                    "compression_ratio_threshold": self.COMPRESSION_RATIO_THRESHOLD,
                    "log_prob_threshold": self.LOG_PROB_THRESHOLD,
                }
            }
```

### 2. 更新模型加载函数

```python
# app/tasks.py
def get_whisper_model():
    """根据配置加载Whisper模型"""
    global model
    if model is None:
        try:
            config = settings.get_precision_config()
            model_name = config.get("model_name", settings.MODEL_NAME)
            compute_type = config.get("compute_type", settings.MODEL_COMPUTE_TYPE)
            
            print(f"Loading Whisper model: {model_name} on {settings.MODEL_DEVICE} with {compute_type}")
            
            os.environ['TOKENIZERS_PARALLELISM'] = 'false'
            
            model = WhisperModel(
                model_name,
                device=settings.MODEL_DEVICE,
                compute_type=compute_type,
                num_workers=1,
                download_root=None,
                local_files_only=False
            )
            print("Whisper model loaded successfully.")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to load Whisper model: {e}")
    return model
```

### 3. 更新转写函数

```python
# app/tasks.py
def transcribe_audio(model, audio_path: str) -> tuple:
    """使用配置的精度参数进行转写"""
    config = settings.get_precision_config()
    transcribe_params = config.get("transcribe_params", {})
    
    print(f"Transcribing with params: {transcribe_params}")
    
    try:
        segments, info = model.transcribe(str(audio_path), **transcribe_params)
        return segments, info
    except Exception as e:
        print(f"Transcription error: {e}")
        # 降级到基础参数重试
        print("Retrying with basic parameters...")
        segments, info = model.transcribe(
            str(audio_path),
            beam_size=1,
            word_timestamps=False
        )
        return segments, info
```

## 环境变量配置

### .env 文件示例

```bash
# 基础配置
APP_NAME=Audio2Sub Backend
DEBUG=true

# Redis配置
REDIS_HOST=127.0.0.1
REDIS_PORT=16379
REDIS_PASSWORD=

# Whisper模型配置
MODEL_NAME=base
MODEL_DEVICE=cpu
MODEL_COMPUTE_TYPE=int8

# 精度配置
PRECISION_MODE=balanced

# 详细转写参数（可选）
BEAM_SIZE=5
BEST_OF=3
PATIENCE=1.0
TEMPERATURE=0.0
REPETITION_PENALTY=1.1
NO_SPEECH_THRESHOLD=0.6
COMPRESSION_RATIO_THRESHOLD=2.4
LOG_PROB_THRESHOLD=-1.0

# 高级配置
ENABLE_WORD_TIMESTAMPS=true
CONDITION_ON_PREVIOUS_TEXT=true
MAX_INITIAL_TIMESTAMP=1.0
```

### 不同场景的配置示例

#### 开发环境 (.env.development)
```bash
PRECISION_MODE=fast
MODEL_NAME=tiny
DEBUG=true
```

#### 生产环境 (.env.production)
```bash
PRECISION_MODE=balanced
MODEL_NAME=base
DEBUG=false
```

#### 高精度环境 (.env.high_precision)
```bash
PRECISION_MODE=high
MODEL_NAME=large-v3
MODEL_DEVICE=cuda
MODEL_COMPUTE_TYPE=float16
```

## 性能对比

### 处理时间对比（5分钟音频）

| 配置 | 模型 | 设备 | 处理时间 | 内存使用 | 准确率 |
|------|------|------|----------|----------|--------|
| 快速 | tiny | CPU | ~30秒 | ~500MB | 85% |
| 平衡 | base | CPU | ~60秒 | ~1GB | 92% |
| 高精度 | large-v3 | GPU | ~45秒 | ~4GB | 97% |
| 高精度 | large-v3 | CPU | ~300秒 | ~6GB | 97% |

### 资源需求

| 模型 | 磁盘空间 | 最小内存 | 推荐内存 | GPU显存 |
|------|----------|----------|----------|---------|
| tiny | ~39MB | 512MB | 1GB | 可选 |
| base | ~74MB | 1GB | 2GB | 可选 |
| small | ~244MB | 2GB | 4GB | 推荐 |
| medium | ~769MB | 4GB | 8GB | 推荐 |
| large-v3 | ~1.5GB | 8GB | 16GB | 4GB+ |

## 故障排除

### 常见问题

#### 1. 模型加载失败
```bash
# 症状
Error loading Whisper model: ...

# 解决方案
- 检查网络连接（首次下载需要）
- 确认磁盘空间足够
- 降级到更小的模型
- 检查compute_type与设备兼容性
```

#### 2. 内存不足
```bash
# 症状
CUDA out of memory / RAM insufficient

# 解决方案
- 使用更小的模型
- 降低compute_type（如float16→int8）
- 调整num_workers=1
- 分段处理长音频
```

#### 3. 转写速度慢
```bash
# 解决方案
- 降低beam_size
- 设置best_of=1
- 使用更小的模型
- 禁用word_timestamps
- 使用GPU加速
```

#### 4. 转写精度不够
```bash
# 解决方案
- 使用更大的模型
- 增加beam_size
- 提高best_of值
- 启用condition_on_previous_text
- 调整no_speech_threshold
```

### 调试命令

```bash
# 测试不同配置
cd backend
export PRECISION_MODE=fast && uv run python test_whisper_direct.py
export PRECISION_MODE=balanced && uv run python test_whisper_direct.py
export PRECISION_MODE=high && uv run python test_whisper_direct.py

# 查看模型信息
uv run python -c "from faster_whisper import WhisperModel; model = WhisperModel('base'); print(model)"

# 监控资源使用
htop  # 查看CPU和内存
nvidia-smi  # 查看GPU使用（如果有）
```

### 性能优化建议

1. **开发阶段**: 使用 `tiny` 模型快速迭代
2. **测试阶段**: 使用 `base` 模型验证功能
3. **生产环境**: 根据实际需求选择合适模型
4. **硬件投资**: 考虑GPU加速显著提升性能
5. **分布式部署**: 大规模应用可考虑多机部署

---

## 总结

选择合适的精度配置需要在以下因素间平衡：

- **准确性需求**: 字幕质量要求
- **处理速度**: 用户等待时间
- **硬件资源**: CPU/GPU/内存限制
- **成本考虑**: 硬件和电力成本

建议从 `balanced` 配置开始，根据实际使用情况进行调整。对于大多数应用场景，当前的默认配置（base模型 + int8精度）提供了很好的平衡点。

更新日期: 2025年6月16日
版本: 1.0.0
