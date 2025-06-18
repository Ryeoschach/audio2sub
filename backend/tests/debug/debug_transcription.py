#!/usr/bin/env python3
"""
调试转录结果数据结构
"""

import sys
import os
sys.path.append('.')

from app.whisper_manager import WhisperManager
from pathlib import Path
import json

def debug_transcription_data():
    """调试转录数据结构"""
    print("🔍 调试转录结果数据结构")
    print("=" * 40)
    
    # 初始化WhisperManager
    manager = WhisperManager()
    test_audio = Path("/Users/creed/workspace/sourceCode/whisper.cpp/111.wav")
    
    # 执行转录
    print("🔄 执行转录...")
    result = manager.transcribe(str(test_audio))
    
    print(f"📄 完整结果结构:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print(f"\n📊 段落详情:")
    segments = result.get("segments", [])
    print(f"   段落总数: {len(segments)}")
    
    for i, segment in enumerate(segments[:5]):  # 只显示前5个
        print(f"\n   段落 {i+1}:")
        print(f"     开始时间: {segment.get('start', 'N/A')}")
        print(f"     结束时间: {segment.get('end', 'N/A')}")
        print(f"     文本: {segment.get('text', 'N/A')}")
        print(f"     词语数量: {len(segment.get('words', []))}")

if __name__ == "__main__":
    debug_transcription_data()
