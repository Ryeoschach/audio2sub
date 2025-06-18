#!/usr/bin/env python3
"""
调试字幕生成问题
"""

import sys
import os
sys.path.append('.')

from app.whisper_manager import WhisperManager
from app.tasks import generate_subtitles_from_segments
from pathlib import Path
import json

def debug_subtitle_generation():
    """调试字幕生成问题"""
    print("🔍 调试字幕生成问题")
    print("=" * 40)
    
    # 1. 获取转录数据
    print("🔄 1. 获取转录数据...")
    manager = WhisperManager()
    test_audio = Path("/Users/creed/workspace/sourceCode/whisper.cpp/111.wav")
    result = manager.transcribe(str(test_audio))
    
    segments = result.get("segments", [])
    print(f"   ✅ 获得 {len(segments)} 个段落")
    
    if len(segments) > 0:
        first_segment = segments[0]
        print(f"   📄 第一个段落示例:")
        print(f"      开始: {first_segment.get('start', 'N/A')}")
        print(f"      结束: {first_segment.get('end', 'N/A')}")
        print(f"      文本: {first_segment.get('text', 'N/A')}")
        print(f"      词语: {len(first_segment.get('words', []))}")
    
    # 2. 测试字幕生成
    print("\n🔄 2. 测试字幕生成...")
    test_dir = Path("/tmp/subtitle_test")
    test_dir.mkdir(exist_ok=True)
    
    srt_path = test_dir / "test.srt"
    vtt_path = test_dir / "test.vtt"
    
    try:
        generate_subtitles_from_segments(segments, srt_path, vtt_path)
        
        # 检查生成的文件
        if srt_path.exists():
            srt_size = srt_path.stat().st_size
            print(f"   ✅ SRT文件已生成: {srt_size} 字节")
            if srt_size > 0:
                with open(srt_path, 'r', encoding='utf-8') as f:
                    content = f.read()[:200]
                    print(f"   📄 SRT内容预览: {content}...")
            else:
                print("   ⚠️ SRT文件为空")
        else:
            print("   ❌ SRT文件未生成")
            
        if vtt_path.exists():
            vtt_size = vtt_path.stat().st_size
            print(f"   ✅ VTT文件已生成: {vtt_size} 字节")
            if vtt_size > 8:  # 大于"WEBVTT\n\n"
                with open(vtt_path, 'r', encoding='utf-8') as f:
                    content = f.read()[:200]
                    print(f"   📄 VTT内容预览: {content}...")
            else:
                print("   ⚠️ VTT文件只有头部")
        else:
            print("   ❌ VTT文件未生成")
            
    except Exception as e:
        print(f"   ❌ 字幕生成失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_subtitle_generation()
