#!/usr/bin/env python3
"""
直接测试转写功能，不通过Celery
"""

import os
import sys
import subprocess
from pathlib import Path

# 添加app目录到Python路径
sys.path.append(str(Path(__file__).parent / "app"))

from faster_whisper import WhisperModel

def test_whisper_directly():
    """直接测试Whisper转写功能"""
    print("🚀 Testing Whisper directly...")
    
    # 创建测试音频文件
    test_audio_path = "test_direct.wav"
    
    try:
        # 生成一个5秒包含简单音频的测试文件
        subprocess.run([
            "ffmpeg", "-f", "lavfi", "-i", "anullsrc=channel_layout=mono:sample_rate=16000",
            "-t", "5", "-ar", "16000", "-ac", "1", "-y", test_audio_path
        ], check=True, capture_output=True)
        
        print(f"✅ Created test audio file: {test_audio_path}")
        
        # 加载模型
        print("📥 Loading Whisper model...")
        model = WhisperModel("base", device="cpu", compute_type="int8", num_workers=1)
        print("✅ Model loaded successfully")
        
        # 转写音频
        print("🎤 Transcribing audio...")
        segments, info = model.transcribe(test_audio_path, beam_size=5)
        
        print(f"📊 Detected language: {info.language} (probability: {info.language_probability:.2f})")
        
        # 输出结果
        segments_list = list(segments)
        print(f"📝 Found {len(segments_list)} segments:")
        
        for i, segment in enumerate(segments_list):
            print(f"  Segment {i+1}: {segment.start:.2f}s - {segment.end:.2f}s: '{segment.text.strip()}'")
        
        if not segments_list:
            print("⚠️  No speech detected in the audio (this is expected for simple tones)")
        
        print("✅ Transcription completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False
    finally:
        # 清理测试文件
        if os.path.exists(test_audio_path):
            os.remove(test_audio_path)
            print(f"🧹 Cleaned up test file: {test_audio_path}")

if __name__ == "__main__":
    test_whisper_directly()
