#!/usr/bin/env python3
"""
测试修复后的Celery任务
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

# Import the task function
from app.tasks import create_transcription_task

def test_fixed_celery_task():
    """测试修复后的Celery任务直接调用"""
    
    # Test parameters
    audio_file = "/Users/creed/workspace/sourceCode/whisper.cpp/111.wav"
    file_id = "test-fixed-88111b23"
    original_filename = "111.wav"
    
    print("=" * 60)
    print("🧪 测试修复后的Celery任务直接调用")
    print("=" * 60)
    
    print(f"📁 音频文件: {audio_file}")
    print(f"🆔 文件ID: {file_id}")
    print(f"📝 原始文件名: {original_filename}")
    
    if not os.path.exists(audio_file):
        print(f"❌ 错误: 音频文件不存在: {audio_file}")
        return
    
    try:
        # Create a mock task object to simulate bind=True
        class MockTask:
            def __init__(self):
                self.request = type('MockRequest', (), {'id': None})()  # Mock request with no id
        
        print("\n🚀 开始执行任务...")
        
        # Call the task function directly using .run() method
        result = create_transcription_task.run(audio_file, file_id, original_filename)
        
        print("\n✅ 任务执行成功!")
        print(f"📊 结果状态: {result.get('status', 'Unknown')}")
        
        # Check file sizes
        results_dir = Path("results") / file_id
        srt_file = results_dir / f"{Path(original_filename).stem}.srt"
        vtt_file = results_dir / f"{Path(original_filename).stem}.vtt"
        
        if srt_file.exists():
            srt_size = srt_file.stat().st_size
            print(f"📄 SRT文件: {srt_file} ({srt_size} 字节)")
            
            # Show first few lines
            with open(srt_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:6]  # First subtitle entry
                if lines:
                    print("📝 SRT内容预览:")
                    for line in lines:
                        print(f"   {line.rstrip()}")
                else:
                    print("⚠️  SRT文件为空")
        else:
            print("❌ SRT文件不存在")
        
        if vtt_file.exists():
            vtt_size = vtt_file.stat().st_size
            print(f"📄 VTT文件: {vtt_file} ({vtt_size} 字节)")
            
            # Show first few lines
            with open(vtt_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:8]  # Header + first subtitle
                if lines:
                    print("📝 VTT内容预览:")
                    for line in lines:
                        print(f"   {line.rstrip()}")
                else:
                    print("⚠️  VTT文件为空")
        else:
            print("❌ VTT文件不存在")
        
        # Print timing information
        timing = result.get('timing', {})
        if timing:
            print(f"\n⏱️  性能统计:")
            print(f"   📁 文件处理: {timing.get('ffmpeg_time', 0):.2f}s")
            print(f"   🎙️  转录: {timing.get('transcription_time', 0):.2f}s")
            print(f"   📄 字幕生成: {timing.get('subtitle_generation_time', 0):.2f}s")
            print(f"   🎯 总时间: {timing.get('total_time', 0):.2f}s")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 任务执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_fixed_celery_task()
