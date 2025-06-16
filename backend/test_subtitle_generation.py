#!/usr/bin/env python3
"""
Test script to verify subtitle generation logic
"""

import sys
import os
sys.path.append('/Users/creed/Workspace/OpenSource/audio2sub/backend')

from app.tasks import generate_subtitles_from_segments, format_timestamp
from app.config import settings
from pathlib import Path
import tempfile

# Test data: simulate word segments
test_segments = []

# Create a long paragraph to test segmentation
long_text = """
大家好 欢迎 来到 我的 频道 今天 我们 聊 一个 在 Python 中 有 超级 重要 的 概念 函数 
大家 有没有 遇到 这样 的 情况 就是 一段 代码 需要 在 程序 的 不同 地方 重复 使用 好几次 
比如 可以 用 一个 多次 计算 两个 数 的 平均值 或者 多次 打印 一些 可视化 的 输出 
如果 每次 把 相同 的 代码 复制 粘贴 一遍 不仅 看起来 还 容易 而且 一旦 需要 修改 就得 修改 好几个 地方
""".strip().split()

# Create test segments with realistic timing
words_per_second = 2.0
for i, word in enumerate(long_text):
    start_time = i / words_per_second
    end_time = (i + 1) / words_per_second
    
    test_segments.append({
        "word": word,
        "start": start_time,
        "end": end_time
    })

print(f"Created {len(test_segments)} test segments")
print(f"Total duration: {test_segments[-1]['end']:.1f} seconds")

# Test subtitle generation
with tempfile.TemporaryDirectory() as temp_dir:
    srt_path = Path(temp_dir) / "test.srt"
    vtt_path = Path(temp_dir) / "test.vtt"
    
    print(f"\nGenerating subtitles with settings:")
    print(f"- MAX_SUBTITLE_DURATION: {settings.MAX_SUBTITLE_DURATION}s")
    print(f"- MAX_WORDS_PER_SUBTITLE: {settings.MAX_WORDS_PER_SUBTITLE}")
    print(f"- MAX_CHARS_PER_SUBTITLE: {settings.MAX_CHARS_PER_SUBTITLE}")
    
    generate_subtitles_from_segments(test_segments, srt_path, vtt_path)
    
    # Read and display the generated SRT
    print(f"\nGenerated SRT content:")
    print("=" * 50)
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content[:1000])  # Show first 1000 characters
        
        # Count subtitle entries
        entries = content.strip().split('\n\n')
        print(f"\nTotal subtitle entries: {len(entries)}")
        
        # Check for long duration entries
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '-->' in line:
                times = line.split(' --> ')
                if len(times) == 2:
                    start_parts = times[0].split(':')
                    end_parts = times[1].split(':')
                    
                    start_seconds = (int(start_parts[0]) * 3600 + 
                                   int(start_parts[1]) * 60 + 
                                   float(start_parts[2].replace(',', '.')))
                    end_seconds = (int(end_parts[0]) * 3600 + 
                                 int(end_parts[1]) * 60 + 
                                 float(end_parts[2].replace(',', '.')))
                    
                    duration = end_seconds - start_seconds
                    if duration > settings.MAX_SUBTITLE_DURATION:
                        print(f"⚠️  WARNING: Long subtitle found: {duration:.1f}s")
                        print(f"   Line {i+1}: {line}")

print("\nTest completed!")
