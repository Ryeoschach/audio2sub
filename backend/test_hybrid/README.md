# Whisper 混合架构测试

这个测试环境用于对比不同Whisper实现的性能和效果，包括：
- **transformers + MPS**: 利用Apple Silicon的Metal Performance Shaders加速
- **faster-whisper + CPU**: 高效的CPU推理，提供精确的时间戳

## 文件结构

```
test_hybrid/
├── config.py              # 配置文件，包含设备、模型、字幕参数
├── hybrid_whisper.py       # 混合Whisper处理器核心实现
├── subtitle_export.py      # 字幕格式导出模块
├── test_main.py           # 主测试脚本
├── setup_test_env.py      # 环境检查和依赖安装
├── output/                # 测试结果输出目录
└── README.md             # 本文件
```

## 快速开始

### 1. 环境检查

```bash
python setup_test_env.py
```

这会检查：
- 必需的Python包依赖
- 本地Whisper模型缓存
- 测试音频文件
- 设备配置（MPS/CUDA/CPU）

### 2. 运行测试

```bash
python test_main.py
```

测试将：
- 使用两种方法转录同一音频文件
- 对比转录结果的质量和性能
- 生成优化的字幕分段
- 导出多种格式的字幕文件
- 创建详细的分析报告

### 3. 查看结果

测试完成后，在`output/`目录下会生成：

```
output/
├── transformers/
│   ├── raw_transformers.srt
│   ├── raw_transformers.vtt
│   └── raw_transformers.txt
├── faster_whisper/
│   ├── raw_faster_whisper.srt
│   ├── raw_faster_whisper.vtt
│   ├── raw_faster_whisper.txt
│   ├── optimized_faster_whisper.srt
│   ├── optimized_faster_whisper.vtt
│   └── optimized_faster_whisper.txt
└── analysis_report.md
```

## 配置说明

### 测试音频

默认使用 `~/Desktop/uv-script.mp4`，可在 `config.py` 中修改：

```python
TEST_AUDIO_PATH = Path("your_audio_file.mp4").expanduser()
```

### 字幕参数

可在 `config.py` 中调整字幕分段参数：

```python
SUBTITLE_CONFIG = {
    "max_chars_per_line": 20,      # 每行最大字符数
    "max_lines_per_subtitle": 2,   # 每个字幕最大行数
    "max_duration": 7.0,           # 单个字幕最大持续时间(秒)
    "min_duration": 0.5,           # 单个字幕最小持续时间(秒)
    "gap_threshold": 1.0,          # 静音间隔阈值(秒)
}
```

### 模型配置

支持调整Whisper模型参数：

```python
MODEL_CONFIG = {
    "whisper_model": "base",       # tiny, base, small, medium, large
    "language": "zh",              # 语言代码
    "task": "transcribe",          # transcribe 或 translate
    "temperature": 0.0,            # 采样温度
    "no_speech_threshold": 0.6,    # 静音阈值
}
```

## 架构优势对比

### Transformers + MPS
- ✅ 利用Apple Silicon GPU加速
- ✅ 与Hugging Face生态完美集成
- ❌ 基础模型不提供词级时间戳
- ❌ 内存占用较大

### Faster-Whisper + CPU
- ✅ 提供精确的词级时间戳
- ✅ 内存效率高，速度快
- ✅ 支持流式处理
- ❌ 在MPS上有兼容性问题

## 智能字幕分割

测试包含了智能字幕分割算法：

1. **文本长度控制**: 根据字符数限制分行
2. **中文智能分割**: 按标点符号自然断句
3. **时间均匀分配**: 为分割后的字幕分配合理时长
4. **持续时间限制**: 确保字幕不会太长或太短

## 性能分析

测试会生成详细的性能分析报告，包括：
- 转录准确度对比
- 处理速度对比
- 内存使用情况
- 字幕质量评估

## 故障排除

### 常见问题

1. **faster-whisper安装失败**
   ```bash
   pip install faster-whisper
   ```

2. **MPS设备不可用**
   - 确保使用macOS 12.3+
   - 确保PyTorch版本支持MPS

3. **模型下载失败**
   - 检查网络连接
   - 使用本地模型缓存

4. **音频文件格式不支持**
   - 转换为常见格式（mp3, wav, mp4）
   - 使用ffmpeg进行格式转换

### 依赖问题

如果遇到依赖冲突，可以创建独立的虚拟环境：

```bash
python -m venv test_env
source test_env/bin/activate  # Linux/Mac
# 或
test_env\Scripts\activate     # Windows

pip install torch transformers librosa faster-whisper
```

## 扩展功能

### 添加新的Whisper实现

1. 在 `hybrid_whisper.py` 中添加新的处理方法
2. 更新 `process_audio` 方法以包含新实现
3. 在 `subtitle_export.py` 中添加对应的导出逻辑

### 自定义字幕格式

1. 在 `subtitle_export.py` 中添加新的格式化函数
2. 更新导出流程以包含新格式

### 批量测试

可以修改 `test_main.py` 来支持批量音频文件测试：

```python
audio_files = [
    "audio1.mp3",
    "audio2.wav", 
    "audio3.mp4"
]

for audio_file in audio_files:
    results = processor.process_audio(audio_file)
    # 处理结果...
```

## 贡献

欢迎提交改进建议和bug报告！
