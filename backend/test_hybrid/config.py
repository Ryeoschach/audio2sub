"""
测试环境配置文件
支持混合Whisper架构：transformers + MPS，faster-whisper + CPU
"""
import os
import torch
from pathlib import Path

# 测试文件配置
TEST_AUDIO_PATH = Path("~/Desktop/111.m4a").expanduser()
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# 本地模型路径配置
HUGGINGFACE_CACHE = Path("~/.cache/huggingface/hub").expanduser()
FASTER_WHISPER_MODEL_PATH = HUGGINGFACE_CACHE / "models--Systran--faster-whisper-base"

# 设备配置
def get_device_config():
    """获取设备配置信息"""
    config = {
        "torch_available": torch.cuda.is_available() or hasattr(torch.backends, 'mps') and torch.backends.mps.is_available(),
        "cuda_available": torch.cuda.is_available(),
        "mps_available": hasattr(torch.backends, 'mps') and torch.backends.mps.is_available(),
        "cpu_count": os.cpu_count(),
    }
    
    # 推荐设备配置
    if config["mps_available"]:
        config["transformers_device"] = "mps"
        config["faster_whisper_device"] = "cpu"  # faster-whisper在MPS上有兼容性问题
        config["faster_whisper_compute_type"] = "int8"
    elif config["cuda_available"]:
        config["transformers_device"] = "cuda"
        config["faster_whisper_device"] = "cuda"
        config["faster_whisper_compute_type"] = "float16"
    else:
        config["transformers_device"] = "cpu"
        config["faster_whisper_device"] = "cpu"
        config["faster_whisper_compute_type"] = "int8"
    
    return config

# 字幕分段配置
SUBTITLE_CONFIG = {
    "max_chars_per_line": 20,      # 每行最大字符数
    "max_lines_per_subtitle": 2,   # 每个字幕最大行数
    "max_duration": 7.0,           # 单个字幕最大持续时间(秒)
    "min_duration": 0.5,           # 单个字幕最小持续时间(秒)
    "gap_threshold": 1.0,          # 静音间隔阈值(秒)
}

# 模型配置
MODEL_CONFIG = {
    "whisper_model": "base",
    "language": "zh",
    "task": "transcribe",
    "temperature": 0.0,
    "no_speech_threshold": 0.6,
    "logprob_threshold": -1.0,
    "compression_ratio_threshold": 2.4,
}

# 打印配置信息
if __name__ == "__main__":
    print("=== 测试环境配置 ===")
    device_config = get_device_config()
    for key, value in device_config.items():
        print(f"{key}: {value}")
    
    print(f"\n测试音频文件: {TEST_AUDIO_PATH}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"faster-whisper本地模型: {FASTER_WHISPER_MODEL_PATH}")
    print(f"模型存在: {FASTER_WHISPER_MODEL_PATH.exists()}")
