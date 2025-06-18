#!/usr/bin/env python3
"""
直接测试WhisperManager类
"""

import sys
import os
sys.path.append('.')

from app.whisper_manager import WhisperManager
from pathlib import Path

def test_whisper_manager():
    """直接测试WhisperManager"""
    print("🎯 直接测试WhisperManager类")
    print("=" * 40)
    
    # 初始化WhisperManager
    try:
        manager = WhisperManager()
        print(f"✅ WhisperManager初始化成功")
        print(f"📍 whisper.cpp路径: {manager.whisper_cpp_path}")
    except Exception as e:
        print(f"❌ WhisperManager初始化失败: {e}")
        return False
    
    # 检查音频文件
    test_audio = Path("/Users/creed/workspace/sourceCode/whisper.cpp/111.wav")
    if not test_audio.exists():
        print(f"❌ 测试音频文件不存在: {test_audio}")
        return False
    
    print(f"✅ 找到测试音频: {test_audio}")
    
    # 执行转录
    try:
        print("🔄 开始转录...")
        result = manager.transcribe(str(test_audio))
        
        print("✅ 转录成功！")
        print(f"📝 转录时间: {result.get('transcription_time', 0):.2f}秒")
        print(f"📄 文本长度: {len(result.get('text', ''))}")
        print(f"📄 文本预览: {result.get('text', '')[:200]}...")
        print(f"🔢 段落数量: {len(result.get('segments', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ 转录失败: {e}")
        return False

if __name__ == "__main__":
    success = test_whisper_manager()
    sys.exit(0 if success else 1)
