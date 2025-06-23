#!/usr/bin/env python3
"""
调试Celery任务中的数据流转问题
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, '.')

def debug_transcription_data_flow():
    """调试转录数据流转"""
    print("🔍 调试转录数据流转")
    
    try:
        from app.tasks import transcribe_with_whisper
        
        # 1. 直接调用transcribe_with_whisper函数
        test_audio = "/Users/creed/workspace/sourceCode/whisper.cpp/111.wav"
        if not Path(test_audio).exists():
            print(f"❌ 测试音频文件不存在: {test_audio}")
            return False
        
        print(f"🎙️ 调用transcribe_with_whisper: {test_audio}")
        transcription_data = transcribe_with_whisper(test_audio)
        
        print("📊 transcribe_with_whisper返回数据分析:")
        print(f"   - 类型: {type(transcription_data)}")
        print(f"   - 键: {list(transcription_data.keys()) if isinstance(transcription_data, dict) else 'N/A'}")
        
        # 2. 检查segments数据
        segments = transcription_data.get("segments", [])
        print(f"   - segments类型: {type(segments)}")
        print(f"   - segments数量: {len(segments) if isinstance(segments, list) else 'N/A'}")
        
        if isinstance(segments, list) and len(segments) > 0:
            print(f"   - 第一个segment: {segments[0]}")
            print("✅ segments数据正常")
        else:
            print("❌ segments数据为空或异常!")
            
            # 检查是否有text数据作为fallback
            full_text = transcription_data.get("text", "").strip()
            if full_text:
                print(f"   - 找到text数据: {len(full_text)}字符")
                print(f"   - text预览: {full_text[:100]}...")
                
                # 模拟fallback逻辑
                fallback_segments = [{
                    "text": full_text,
                    "start": 0.0,
                    "end": 30.0
                }]
                print(f"   - 创建fallback segment: {fallback_segments[0]}")
                
                # 测试fallback是否能生成字幕
                return test_fallback_subtitle_generation(fallback_segments)
            else:
                print("❌ 也没有text数据!")
                return False
        
        # 3. 测试真实segments生成字幕
        return test_real_segments_subtitle_generation(segments)
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_real_segments_subtitle_generation(segments):
    """测试真实segments生成字幕"""
    print("\n🧪 测试真实segments生成字幕")
    
    try:
        from app.tasks import generate_subtitles_from_segments
        import tempfile
        
        if not segments:
            print("❌ segments为空")
            return False
        
        print(f"📊 使用{len(segments)}个segments测试")
        
        # 显示前3个segments详情
        for i, seg in enumerate(segments[:3]):
            print(f"   Segment {i+1}: start={seg.get('start')}, end={seg.get('end')}, text='{seg.get('text', '')[:50]}...'")
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.srt', delete=False) as srt_file:
            srt_path = Path(srt_file.name)
        
        with tempfile.NamedTemporaryFile(suffix='.vtt', delete=False) as vtt_file:
            vtt_path = Path(vtt_file.name)
        
        # 生成字幕
        generate_subtitles_from_segments(segments, srt_path, vtt_path)
        
        # 检查结果
        srt_size = srt_path.stat().st_size if srt_path.exists() else 0
        vtt_size = vtt_path.stat().st_size if vtt_path.exists() else 0
        
        print(f"📄 结果: SRT={srt_size}字节, VTT={vtt_size}字节")
        
        if srt_size > 0:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"📄 SRT内容(前300字符): {content[:300]}")
        
        # 清理
        try:
            srt_path.unlink()
            vtt_path.unlink()
        except:
            pass
        
        return srt_size > 0 and vtt_size > 8
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_subtitle_generation(fallback_segments):
    """测试fallback segments生成字幕"""
    print("\n🧪 测试fallback segments生成字幕")
    
    try:
        from app.tasks import generate_subtitles_from_segments
        import tempfile
        
        print(f"📊 使用fallback segment: {fallback_segments[0]}")
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.srt', delete=False) as srt_file:
            srt_path = Path(srt_file.name)
        
        with tempfile.NamedTemporaryFile(suffix='.vtt', delete=False) as vtt_file:
            vtt_path = Path(vtt_file.name)
        
        # 生成字幕
        generate_subtitles_from_segments(fallback_segments, srt_path, vtt_path)
        
        # 检查结果
        srt_size = srt_path.stat().st_size if srt_path.exists() else 0
        vtt_size = vtt_path.stat().st_size if vtt_path.exists() else 0
        
        print(f"📄 结果: SRT={srt_size}字节, VTT={vtt_size}字节")
        
        if srt_size > 0:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"📄 SRT内容: {content}")
        
        # 清理
        try:
            srt_path.unlink()
            vtt_path.unlink()
        except:
            pass
        
        return srt_size > 0 and vtt_size > 8
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_whisper_manager_output():
    """直接检查WhisperManager输出"""
    print("\n🔍 直接检查WhisperManager输出")
    
    try:
        from app.whisper_manager import get_whisper_manager
        
        manager = get_whisper_manager()
        test_audio = "/Users/creed/workspace/sourceCode/whisper.cpp/111.wav"
        
        print(f"🎙️ WhisperManager转录: {test_audio}")
        result = manager.transcribe(test_audio)
        
        print("📊 WhisperManager原始输出:")
        print(f"   - 类型: {type(result)}")
        print(f"   - 键: {list(result.keys())}")
        
        # 保存完整结果到文件以便检查
        debug_file = Path("debug_whisper_output.json")
        with open(debug_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"📄 完整输出已保存到: {debug_file}")
        
        return result
        
    except Exception as e:
        print(f"❌ WhisperManager测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主调试函数"""
    print("🎯 Celery任务数据流转问题调试")
    print("=" * 50)
    print(f"🐍 Python: {sys.executable}")
    
    # 1. 检查WhisperManager原始输出
    whisper_result = check_whisper_manager_output()
    
    # 2. 检查transcribe_with_whisper处理后的数据
    data_flow_success = debug_transcription_data_flow()
    
    print("\n" + "=" * 50)
    print("📊 调试结果:")
    print(f"   - WhisperManager: {'✅' if whisper_result else '❌'}")
    print(f"   - 数据流转: {'✅' if data_flow_success else '❌'}")
    
    if whisper_result and data_flow_success:
        print("\n🎉 数据流转正常！")
    else:
        print("\n❌ 数据流转存在问题")
    
    return whisper_result and data_flow_success

if __name__ == "__main__":
    main()
