#!/usr/bin/env python3
"""
Debug script to simulate the actual transcription result and test subtitle generation
"""

import sys
import os
sys.path.append('/Users/creed/Workspace/OpenSource/audio2sub/backend')

from app.tasks import generate_subtitles_from_segments, format_timestamp
from app.config import settings
from pathlib import Path
import tempfile

# 模拟实际的转录结果 - 根据附件SRT推测原始数据可能是这样的
print("🔍 Simulating real transcription data structure...")

# 模拟大块文本（类似于实际的chunks结果）
chunks_data = [
    {
        "text": "大家好,欢迎来到我的频道今天我们聊一个在Python中有超级重要的概念函数大家有没有遇到这样的情况就是一段代码需要在程序的不同地方重复使用好几次比如可以用一个多次计算两个数的平均值或者多次打印一些可视化的输出如果每次把相同的代码复制粘贴一遍不仅看起来还容易而且一旦需要修改就得修改好几个地方",
        "timestamp": [0.0, 60.0]  # 60秒的大块
    },
    {
        "text": "比方说我 我定义一个宠物的名字和年龄",
        "timestamp": [60.0, 65.0]
    },
    {
        "text": "描述宠物的年人名字和年龄的return name age 可以的 这样就可以我们先看一下这个是函数题不",
        "timestamp": [65.0, 85.0]
    }
]

# 模拟我们的分词处理
all_segments = []

for chunk in chunks_data:
    text = chunk["text"]
    start_time = chunk["timestamp"][0]
    end_time = chunk["timestamp"][1]
    
    print(f"\n📦 Processing chunk: {start_time}s-{end_time}s")
    print(f"   Text: '{text[:50]}...'")
    
    # 使用智能分词（与实际代码一致）
    import re
    
    # 第一步：处理标点符号
    text_cleaned = re.sub(r'[，。！？、；：]', ' ', text)
    
    # 第二步：分词
    words = []
    tokens = re.findall(r'[a-zA-Z]+|[0-9]+|[一-龯]', text_cleaned)
    
    if len(tokens) < len(text_cleaned.strip()) * 0.3:
        temp_words = text_cleaned.split()
        for word in temp_words:
            if re.match(r'^[a-zA-Z0-9]+$', word):
                words.append(word)
            else:
                chars = list(word)
                for j in range(0, len(chars), 2):
                    group = ''.join(chars[j:j+2])
                    if group.strip():
                        words.append(group)
    else:
        words = tokens
    
    words = [w.strip() for w in words if w.strip()]
    
    print(f"   Split into {len(words)} words: {words[:10]}...")
    
    chunk_duration = end_time - start_time
    if len(words) > 0:
        time_per_word = max(0.3, min(chunk_duration / len(words), 1.5))
        
        for j, word in enumerate(words):
            word_start = start_time + (j * time_per_word)
            word_end = start_time + ((j + 1) * time_per_word)
            
            all_segments.append({
                "word": word.strip(),
                "start": word_start,
                "end": word_end
            })

print(f"\n📊 Total segments created: {len(all_segments)}")
print(f"📊 Total duration: {all_segments[-1]['end']:.1f} seconds")

# 显示前几个段落用于验证
print("\n🔍 First 10 segments:")
for i, seg in enumerate(all_segments[:10]):
    print(f"  {i+1}: '{seg['word']}' ({seg['start']:.1f}s-{seg['end']:.1f}s)")

# 测试字幕生成
print(f"\n🎬 Testing subtitle generation...")
print(f"Settings: {settings.MAX_SUBTITLE_DURATION}s / {settings.MAX_WORDS_PER_SUBTITLE}w / {settings.MAX_CHARS_PER_SUBTITLE}c")

with tempfile.TemporaryDirectory() as temp_dir:
    srt_path = Path(temp_dir) / "debug_test.srt"
    vtt_path = Path(temp_dir) / "debug_test.vtt"
    
    generate_subtitles_from_segments(all_segments, srt_path, vtt_path)
    
    # 读取并分析生成的SRT
    print(f"\n📄 Generated SRT analysis:")
    print("=" * 60)
    
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # 显示前几个条目
        entries = content.strip().split('\n\n')
        print(f"Total subtitle entries: {len(entries)}")
        
        for i, entry in enumerate(entries[:5]):  # 显示前5个
            lines = entry.strip().split('\n')
            if len(lines) >= 3:
                print(f"\nEntry {i+1}:")
                print(f"  Time: {lines[1]}")
                print(f"  Text: {lines[2][:100]}...")
                
                # 计算时长
                if '-->' in lines[1]:
                    times = lines[1].split(' --> ')
                    if len(times) == 2:
                        try:
                            start_parts = times[0].split(':')
                            end_parts = times[1].split(':')
                            
                            start_seconds = (int(start_parts[0]) * 3600 + 
                                           int(start_parts[1]) * 60 + 
                                           float(start_parts[2].replace(',', '.')))
                            end_seconds = (int(end_parts[0]) * 3600 + 
                                         int(end_parts[1]) * 60 + 
                                         float(end_parts[2].replace(',', '.')))
                            
                            duration = end_seconds - start_seconds
                            print(f"  Duration: {duration:.1f}s")
                            
                            if duration > settings.MAX_SUBTITLE_DURATION:
                                print(f"  ⚠️ EXCEEDS LIMIT! ({duration:.1f}s > {settings.MAX_SUBTITLE_DURATION}s)")
                        except:
                            print(f"  ⚠️ Could not parse time")

print("\n✅ Debug test completed!")
