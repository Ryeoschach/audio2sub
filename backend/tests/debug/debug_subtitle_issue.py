#!/usr/bin/env python3
"""
调试字幕生成问题 - 分析为什么SRT/VTT文件为空
"""
import sys
import json
from pathlib import Path
import time

sys.path.insert(0, '.')

def debug_subtitle_generation():
    """调试字幕生成逻辑"""
    print("🔍 调试字幕生成问题")
    
    # 1. 检查结果目录
    results_dir = Path("results")
    if not results_dir.exists():
        print("❌ results目录不存在")
        return
    
    # 找到最新的任务目录
    task_dirs = [d for d in results_dir.iterdir() if d.is_dir()]
    if not task_dirs:
        print("❌ 没有找到任务目录")
        return
    
    latest_task = max(task_dirs, key=lambda x: x.stat().st_mtime)
    print(f"📁 检查任务目录: {latest_task}")
    
    # 列出目录内容
    files = list(latest_task.iterdir())
    print(f"📄 目录文件: {[f.name for f in files]}")
    
    # 2. 检查JSON转录文件
    json_files = [f for f in files if f.suffix == '.json' and 'transcription' in f.name]
    if json_files:
        json_file = json_files[0]
        print(f"\n📋 检查JSON文件: {json_file}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"🔍 JSON结构分析:")
            print(f"   - 根键: {list(data.keys())}")
            
            # 详细分析转录数据结构
            if 'transcription' in data:
                transcription = data['transcription']
                print(f"   - 转录类型: {type(transcription)}")
                
                if isinstance(transcription, dict):
                    print(f"   - 转录字典键: {list(transcription.keys())}")
                    
                    # 检查segments
                    if 'segments' in transcription:
                        segments = transcription['segments']
                        print(f"   - segments类型: {type(segments)}")
                        print(f"   - segments长度: {len(segments) if isinstance(segments, list) else 'N/A'}")
                        
                        if isinstance(segments, list) and len(segments) > 0:
                            print(f"   - 第一个segment: {segments[0]}")
                            print(f"   - segment键: {list(segments[0].keys()) if isinstance(segments[0], dict) else 'N/A'}")
                    
                    # 检查text
                    if 'text' in transcription:
                        text = transcription['text']
                        print(f"   - 文本长度: {len(text)}")
                        print(f"   - 文本预览: {text[:100]}...")
                
                elif isinstance(transcription, list):
                    print(f"   - 转录数组长度: {len(transcription)}")
                    if len(transcription) > 0:
                        first_item = transcription[0]
                        print(f"   - 第一个转录项: {first_item}")
                        print(f"   - 转录项键: {list(first_item.keys()) if isinstance(first_item, dict) else 'N/A'}")
        
        except Exception as e:
            print(f"❌ JSON文件读取失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 3. 检查SRT/VTT文件
    srt_files = [f for f in files if f.suffix == '.srt']
    vtt_files = [f for f in files if f.suffix == '.vtt']
    
    print(f"\n📄 字幕文件检查:")
    for srt_file in srt_files:
        size = srt_file.stat().st_size
        print(f"   - SRT文件: {srt_file.name} (大小: {size} 字节)")
        if size > 0:
            with open(srt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"     内容预览: {content[:200]}...")
        else:
            print(f"     ⚠️ 文件为空")
    
    for vtt_file in vtt_files:
        size = vtt_file.stat().st_size
        print(f"   - VTT文件: {vtt_file.name} (大小: {size} 字节)")
        if size > 0:
            with open(vtt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"     内容预览: {content[:200]}...")
        else:
            print(f"     ⚠️ 文件为空")

def test_subtitle_generation_directly():
    """直接测试字幕生成函数"""
    print("\n🧪 直接测试字幕生成函数")
    
    try:
        from app.tasks import generate_subtitles_from_segments
        
        # 创建测试段落数据
        test_segments = [
            {
                "start": 0.0,
                "end": 3.0,
                "text": "Hello everyone, we have talked about a U-Way.",
                "words": []
            },
            {
                "start": 3.0,
                "end": 8.0,
                "text": "Hello everyone, we have talked about the use of U-Way in the middle of the painting.",
                "words": []
            },
            {
                "start": 8.0,
                "end": 12.0,
                "text": "We will use the details of our device.",
                "words": []
            }
        ]
        
        print(f"📊 测试段落数量: {len(test_segments)}")
        
        # 创建临时输出文件
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.srt', delete=False) as srt_file:
            srt_path = Path(srt_file.name)
        
        with tempfile.NamedTemporaryFile(suffix='.vtt', delete=False) as vtt_file:
            vtt_path = Path(vtt_file.name)
        
        print(f"📁 临时SRT文件: {srt_path}")
        print(f"📁 临时VTT文件: {vtt_path}")
        
        # 调用字幕生成函数
        print("🔄 调用字幕生成函数...")
        generate_subtitles_from_segments(test_segments, srt_path, vtt_path)
        
        # 检查生成结果
        if srt_path.exists():
            srt_size = srt_path.stat().st_size
            print(f"✅ SRT文件生成: {srt_size} 字节")
            if srt_size > 0:
                with open(srt_path, 'r', encoding='utf-8') as f:
                    srt_content = f.read()
                    print("📄 SRT内容:")
                    print(srt_content)
            else:
                print("⚠️ SRT文件为空")
        
        if vtt_path.exists():
            vtt_size = vtt_path.stat().st_size
            print(f"✅ VTT文件生成: {vtt_size} 字节")
            if vtt_size > 0:
                with open(vtt_path, 'r', encoding='utf-8') as f:
                    vtt_content = f.read()
                    print("📄 VTT内容:")
                    print(vtt_content)
            else:
                print("⚠️ VTT文件为空")
        
        # 清理临时文件
        try:
            srt_path.unlink()
            vtt_path.unlink()
        except:
            pass
            
    except Exception as e:
        print(f"❌ 字幕生成函数测试失败: {e}")
        import traceback
        traceback.print_exc()

def analyze_whisper_output():
    """分析whisper.cpp的原始输出"""
    print("\n🔍 分析whisper.cpp原始输出")
    
    # 检查whisper.cpp临时输出文件
    temp_json = Path("/tmp/whisper_output.json")
    if temp_json.exists():
        print(f"📋 找到临时JSON文件: {temp_json}")
        try:
            with open(temp_json, 'r', encoding='utf-8') as f:
                whisper_data = json.load(f)
            
            print("🔍 Whisper.cpp输出结构:")
            print(f"   - 根键: {list(whisper_data.keys())}")
            
            if 'transcription' in whisper_data:
                transcription = whisper_data['transcription']
                print(f"   - 转录项数量: {len(transcription)}")
                
                if len(transcription) > 0:
                    first_item = transcription[0]
                    print(f"   - 第一项结构: {first_item}")
                    
                    # 检查时间戳格式
                    if 'offsets' in first_item:
                        offsets = first_item['offsets']
                        print(f"   - 时间戳格式: {offsets}")
                        print(f"   - from: {offsets.get('from')} ms")
                        print(f"   - to: {offsets.get('to')} ms")
        
        except Exception as e:
            print(f"❌ 临时JSON文件读取失败: {e}")
    else:
        print("⚠️ 没有找到whisper.cpp临时输出文件")

def check_task_execution():
    """检查任务执行流程"""
    print("\n🔍 检查任务执行流程")
    
    try:
        from app.whisper_manager import get_whisper_manager
        from app.tasks import generate_subtitles_from_segments
        
        # 1. 测试whisper转录
        print("🎙️ 测试whisper转录...")
        manager = get_whisper_manager()
        
        test_audio = "/Users/creed/workspace/sourceCode/whisper.cpp/111.wav"
        if Path(test_audio).exists():
            result = manager.transcribe(test_audio)
            
            print("📊 转录结果分析:")
            print(f"   - 类型: {type(result)}")
            print(f"   - 键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            
            if 'segments' in result:
                segments = result['segments']
                print(f"   - segments类型: {type(segments)}")
                print(f"   - segments数量: {len(segments) if isinstance(segments, list) else 'N/A'}")
                
                if isinstance(segments, list) and len(segments) > 0:
                    print(f"   - 第一个segment: {segments[0]}")
                    
                    # 测试字幕生成
                    print("\n🔄 测试字幕生成...")
                    import tempfile
                    
                    with tempfile.NamedTemporaryFile(suffix='.srt', delete=False) as srt_file:
                        srt_path = Path(srt_file.name)
                    
                    with tempfile.NamedTemporaryFile(suffix='.vtt', delete=False) as vtt_file:
                        vtt_path = Path(vtt_file.name)
                    
                    generate_subtitles_from_segments(segments, srt_path, vtt_path)
                    
                    # 检查结果
                    srt_size = srt_path.stat().st_size if srt_path.exists() else 0
                    vtt_size = vtt_path.stat().st_size if vtt_path.exists() else 0
                    
                    print(f"📄 生成结果:")
                    print(f"   - SRT大小: {srt_size} 字节")
                    print(f"   - VTT大小: {vtt_size} 字节")
                    
                    if srt_size > 0:
                        with open(srt_path, 'r', encoding='utf-8') as f:
                            print(f"   - SRT内容预览: {f.read()[:300]}...")
                    
                    # 清理
                    try:
                        srt_path.unlink()
                        vtt_path.unlink()
                    except:
                        pass
                else:
                    print("⚠️ segments为空或格式错误")
            else:
                print("⚠️ 转录结果中没有segments")
        else:
            print(f"⚠️ 测试音频文件不存在: {test_audio}")
            
    except Exception as e:
        print(f"❌ 任务执行检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 Audio2Sub Backend 字幕生成问题调试")
    print("=" * 60)
    
    # 运行所有调试步骤
    debug_subtitle_generation()
    test_subtitle_generation_directly()
    analyze_whisper_output()
    check_task_execution()
    
    print("\n" + "=" * 60)
    print("🔍 调试完成")
