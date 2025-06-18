#!/usr/bin/env python3
"""
简化版测试脚本 - 只使用faster-whisper
避免网络下载问题，快速验证混合架构的faster-whisper部分
"""
import sys
import time
from pathlib import Path

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

def main():
    """简化版测试函数"""
    print("=== 简化版 Whisper 测试开始 ===")
    
    # 导入配置
    from config import TEST_AUDIO_PATH, OUTPUT_DIR, get_device_config, FASTER_WHISPER_MODEL_PATH, MODEL_CONFIG
    
    # 检查设备配置
    device_config = get_device_config()
    print(f"\n设备配置:")
    for key, value in device_config.items():
        print(f"  {key}: {value}")
    
    # 检查测试音频文件
    if not TEST_AUDIO_PATH.exists():
        print(f"\n❌ 测试音频文件不存在: {TEST_AUDIO_PATH}")
        print("请确保文件路径正确，或修改config.py中的TEST_AUDIO_PATH")
        return
    
    print(f"\n✅ 测试音频文件: {TEST_AUDIO_PATH}")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    
    # 检查faster-whisper模型
    print(f"\n--- 检查faster-whisper模型 ---")
    # 直接使用模型名称，让faster-whisper自动处理缓存
    model_path = MODEL_CONFIG['whisper_model']
    print(f"使用模型: {model_path}")
    
    if FASTER_WHISPER_MODEL_PATH.exists():
        print(f"✅ HuggingFace缓存存在: {FASTER_WHISPER_MODEL_PATH}")
    else:
        print(f"❌ HuggingFace缓存不存在: {FASTER_WHISPER_MODEL_PATH}")
        print("将从网络下载模型")
    
    # 初始化faster-whisper模型
    print(f"\n--- 初始化faster-whisper模型 ---")
    try:
        from faster_whisper import WhisperModel
        
        model = WhisperModel(
            model_path,
            device=device_config["faster_whisper_device"],
            compute_type=device_config["faster_whisper_compute_type"]
        )
        print(f"✅ 模型加载成功，设备: {device_config['faster_whisper_device']}")
        
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return
    
    # 执行转录
    print(f"\n--- 开始音频转录 ---")
    start_time = time.time()
    
    try:
        segments, info = model.transcribe(
            str(TEST_AUDIO_PATH),
            language="zh",
            vad_filter=False,  # 关闭VAD过滤避免潜在问题
            word_timestamps=False  # 关闭词级时间戳避免潜在问题
        )
        
        # 收集所有分段
        all_segments = list(segments)
        total_time = time.time() - start_time
        
        print(f"\n⏱️ 转录完成，耗时: {total_time:.2f}秒")
        print(f"🎵 音频信息:")
        print(f"  - 时长: {info.duration:.2f}秒")
        print(f"  - 语言: {info.language} (置信度: {info.language_probability:.2f})")
        
        print(f"\n📝 转录结果:")
        print(f"  - 分段数量: {len(all_segments)}")
        
        if all_segments:
            print(f"  - 前5段内容:")
            for i, segment in enumerate(all_segments[:5], 1):
                print(f"    {i}. [{segment.start:.1f}s-{segment.end:.1f}s] {segment.text}")
        
        # 保存结果到文件
        output_file = OUTPUT_DIR / "faster_whisper_result.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"音频文件: {TEST_AUDIO_PATH}\n")
            f.write(f"转录时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"处理耗时: {total_time:.2f}秒\n")
            f.write(f"音频时长: {info.duration:.2f}秒\n")
            f.write(f"语言: {info.language} (置信度: {info.language_probability:.2f})\n")
            f.write(f"分段数量: {len(all_segments)}\n\n")
            
            f.write("=== 详细转录内容 ===\n")
            for i, segment in enumerate(all_segments, 1):
                f.write(f"{i:3d}. [{segment.start:6.1f}s-{segment.end:6.1f}s] {segment.text}\n")
        
        print(f"\n✅ 结果已保存到: {output_file}")
        
        # 生成SRT字幕文件
        srt_file = OUTPUT_DIR / "faster_whisper_result.srt"
        with open(srt_file, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(all_segments, 1):
                start_time = format_timestamp(segment.start)
                end_time = format_timestamp(segment.end)
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{segment.text.strip()}\n\n")
        
        print(f"📹 SRT字幕已保存到: {srt_file}")
        
    except Exception as e:
        print(f"❌ 转录过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

def format_timestamp(seconds):
    """格式化时间戳为SRT格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
