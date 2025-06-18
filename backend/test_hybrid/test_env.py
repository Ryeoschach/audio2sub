#!/usr/bin/env python3
"""
环境验证测试 - 不处理实际音频文件
"""
import sys
import warnings
from pathlib import Path

# 抑制资源泄漏警告
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

sys.path.append(str(Path(__file__).parent.parent))

def test_environment():
    """验证环境是否正常"""
    print("=== 环境验证测试 ===")
    
    # 1. 测试导入
    try:
        from faster_whisper import WhisperModel
        print("✅ faster-whisper 导入成功")
    except Exception as e:
        print(f"❌ faster-whisper 导入失败: {e}")
        return False
    
    # 2. 测试模型加载
    try:
        print("正在加载模型...")
        model = WhisperModel("base", device="cpu", compute_type="float32", num_workers=1)
        print("✅ 模型加载成功")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return False
    
    # 3. 测试基本功能（使用虚拟音频）
    try:
        import numpy as np
        
        # 创建一个5秒的虚拟音频（16kHz采样率，单声道）
        sample_rate = 16000
        duration = 5.0
        samples = int(sample_rate * duration)
        
        # 生成简单的正弦波作为测试音频
        t = np.linspace(0, duration, samples, False)
        frequency = 440.0  # A4音符
        audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
        print("正在转录虚拟音频...")
        segments, info = model.transcribe(audio_data, language="zh")
        
        # 收集结果
        segment_list = list(segments)
        
        print("✅ 虚拟音频转录成功")
        print(f"📊 检测到的分段数: {len(segment_list)}")
        print(f"🈳 检测语言: {info.language}")
        print(f"⏱️ 音频时长: {info.duration:.2f}秒")
        
        if segment_list:
            print("📝 转录结果:")
            for i, segment in enumerate(segment_list[:3], 1):
                print(f"  {i}. [{segment.start:.1f}s-{segment.end:.1f}s] '{segment.text}'")
        else:
            print("📝 虚拟音频未检测到语音内容（这是正常的）")
        
    except Exception as e:
        print(f"❌ 虚拟音频转录失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理资源
        try:
            del model
            import gc
            gc.collect()
        except:
            pass
    
    print("🎉 环境验证完成，faster-whisper 工作正常！")
    return True

def test_audio_file():
    """测试实际音频文件"""
    print("\n=== 音频文件测试 ===")
    
    from config import TEST_AUDIO_PATH
    
    if not TEST_AUDIO_PATH.exists():
        print(f"❌ 音频文件不存在: {TEST_AUDIO_PATH}")
        return False
    
    print(f"✅ 音频文件: {TEST_AUDIO_PATH}")
    
    # 首先检查文件大小
    file_size = TEST_AUDIO_PATH.stat().st_size
    print(f"📊 文件大小: {file_size / (1024*1024):.2f} MB")
    
    if file_size > 50 * 1024 * 1024:  # 超过50MB
        print("⚠️ 文件较大，可能导致处理问题")
    
    try:
        from faster_whisper import WhisperModel
        
        print("正在加载模型...")
        model = WhisperModel("base", device="cpu", compute_type="float32", num_workers=1)
        
        print("开始转录音频文件（仅前30秒）...")
        import time
        start_time = time.time()
        
        # 只转录前30秒避免长时间处理
        segments, info = model.transcribe(
            str(TEST_AUDIO_PATH),
            language="zh",
            vad_filter=False,
            word_timestamps=False,
            condition_on_previous_text=False,
            # 限制处理时长
            clip_timestamps=[0, 30]  # 只处理前30秒
        )
        
        # 收集前3个分段
        segment_list = []
        for i, segment in enumerate(segments):
            if i >= 3:
                break
            segment_list.append(segment)
        
        total_time = time.time() - start_time
        
        print(f"✅ 转录成功！耗时: {total_time:.2f}秒")
        print(f"📊 音频时长: {info.duration:.2f}秒")
        print(f"🈳 检测语言: {info.language}")
        print(f"📝 前{len(segment_list)}段:")
        
        for i, segment in enumerate(segment_list, 1):
            print(f"  {i}. [{segment.start:.1f}s-{segment.end:.1f}s] {segment.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ 音频文件转录失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            del model
            import gc
            gc.collect()
        except:
            pass

if __name__ == "__main__":
    print("🚀 开始测试 faster-whisper 环境")
    
    # 先验证环境
    env_ok = test_environment()
    
    if env_ok:
        # 环境正常，测试实际音频文件
        audio_ok = test_audio_file()
        
        if audio_ok:
            print("\n🎉 所有测试通过！faster-whisper 运行正常")
        else:
            print("\n⚠️ 环境正常但音频文件处理有问题")
    else:
        print("\n❌ 环境有问题，需要检查依赖安装")
