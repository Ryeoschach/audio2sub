#!/usr/bin/env python3
"""
简单测试whisper转录和字幕生成
"""
import sys
from pathlib import Path

# 确保使用当前目录的模块
sys.path.insert(0, '.')

def test_whisper_transcription():
    """测试whisper转录功能"""
    print("🎙️ 测试whisper转录功能")
    print("-" * 40)
    
    try:
        from app.whisper_manager import get_whisper_manager
        
        # 获取whisper manager
        manager = get_whisper_manager()
        print(f"✅ WhisperManager初始化成功")
        print(f"🔧 whisper.cpp路径: {manager.whisper_cpp_path}")
        
        # 测试音频文件路径
        test_audio = "/Users/creed/workspace/sourceCode/whisper.cpp/111.wav"
        if not Path(test_audio).exists():
            print(f"❌ 测试音频文件不存在: {test_audio}")
            return None
        
        print(f"📁 音频文件: {test_audio}")
        
        # 执行转录
        print("🔄 开始转录...")
        result = manager.transcribe(test_audio)
        
        # 分析转录结果
        print("\n📊 转录结果分析:")
        print(f"   - 结果类型: {type(result)}")
        print(f"   - 结果键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        
        # 检查文本
        if 'text' in result:
            text = result['text']
            print(f"   - 文本长度: {len(text)}")
            if text:
                preview = text[:100] + "..." if len(text) > 100 else text
                print(f"   - 文本预览: {preview}")
        
        # 检查segments
        if 'segments' in result:
            segments = result['segments']
            print(f"   - segments类型: {type(segments)}")
            print(f"   - segments数量: {len(segments) if isinstance(segments, list) else 'N/A'}")
            
            if isinstance(segments, list) and len(segments) > 0:
                first_segment = segments[0]
                print(f"   - 第一个segment: {first_segment}")
                print(f"   - segment键: {list(first_segment.keys()) if isinstance(first_segment, dict) else 'N/A'}")
            else:
                print("   ⚠️ segments为空或不是列表!")
        else:
            print("   ❌ 转录结果中没有segments!")
        
        return result
        
    except Exception as e:
        print(f"❌ 转录测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_subtitle_generation(transcription_result):
    """测试字幕生成功能"""
    print("\n📄 测试字幕生成功能")
    print("-" * 40)
    
    if not transcription_result:
        print("❌ 没有转录结果，跳过字幕生成测试")
        return False
    
    try:
        from app.tasks import generate_subtitles_from_segments
        import tempfile
        
        # 获取segments
        segments = transcription_result.get('segments', [])
        print(f"📊 可用段落数量: {len(segments)}")
        
        if not segments:
            print("⚠️ 没有segments，创建测试segments...")
            # 使用转录文本创建一个基本segment
            text = transcription_result.get('text', '')
            if text:
                segments = [{
                    "start": 0.0,
                    "end": 30.0,
                    "text": text.strip()
                }]
                print(f"✅ 创建了 {len(segments)} 个测试segment")
            else:
                print("❌ 没有可用的文本数据")
                return False
        
        # 显示前几个segments的结构
        for i, segment in enumerate(segments[:3]):
            print(f"   Segment {i+1}: {segment}")
        
        # 创建临时文件测试字幕生成
        with tempfile.NamedTemporaryFile(suffix='.srt', delete=False) as srt_file:
            srt_path = Path(srt_file.name)
        
        with tempfile.NamedTemporaryFile(suffix='.vtt', delete=False) as vtt_file:
            vtt_path = Path(vtt_file.name)
        
        print(f"📁 临时SRT文件: {srt_path}")
        print(f"📁 临时VTT文件: {vtt_path}")
        
        # 调用字幕生成函数
        print("🔄 生成字幕文件...")
        generate_subtitles_from_segments(segments, srt_path, vtt_path)
        
        # 检查生成结果
        print("\n📄 字幕生成结果:")
        
        if srt_path.exists():
            srt_size = srt_path.stat().st_size
            print(f"   ✅ SRT文件: {srt_size} 字节")
            
            if srt_size > 0:
                with open(srt_path, 'r', encoding='utf-8') as f:
                    srt_content = f.read()
                    print("   📝 SRT内容:")
                    # 显示前几行
                    lines = srt_content.split('\n')
                    for i, line in enumerate(lines[:10], 1):
                        print(f"      {i:2d}: {line}")
                    if len(lines) > 10:
                        print(f"      ... (总共{len(lines)}行)")
            else:
                print("   ⚠️ SRT文件为空")
        else:
            print("   ❌ SRT文件未生成")
        
        if vtt_path.exists():
            vtt_size = vtt_path.stat().st_size
            print(f"   ✅ VTT文件: {vtt_size} 字节")
            
            if vtt_size > 8:  # 大于"WEBVTT\n\n"
                with open(vtt_path, 'r', encoding='utf-8') as f:
                    vtt_content = f.read()
                    print("   📝 VTT内容:")
                    # 显示前几行
                    lines = vtt_content.split('\n')
                    for i, line in enumerate(lines[:10], 1):
                        print(f"      {i:2d}: {line}")
                    if len(lines) > 10:
                        print(f"      ... (总共{len(lines)}行)")
            else:
                print("   ⚠️ VTT文件只有头部")
        else:
            print("   ❌ VTT文件未生成")
        
        # 清理临时文件
        try:
            srt_path.unlink()
            vtt_path.unlink()
            print("   🗑️ 临时文件已清理")
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ 字幕生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_simple_segments():
    """使用简单的测试segments测试字幕生成"""
    print("\n🧪 使用简单测试数据测试字幕生成")
    print("-" * 40)
    
    try:
        from app.tasks import generate_subtitles_from_segments
        import tempfile
        
        # 创建简单的测试segments
        test_segments = [
            {
                "start": 0.0,
                "end": 3.0,
                "text": "Hello everyone, we have talked about a U-Way."
            },
            {
                "start": 3.0,
                "end": 8.0,
                "text": "Hello everyone, we have talked about the use of U-Way in the middle of the painting."
            },
            {
                "start": 8.0,
                "end": 12.0,
                "text": "We will use the details of our device."
            }
        ]
        
        print(f"📊 测试段落数量: {len(test_segments)}")
        for i, segment in enumerate(test_segments, 1):
            print(f"   {i}. {segment['start']:.1f}s-{segment['end']:.1f}s: {segment['text']}")
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.srt', delete=False) as srt_file:
            srt_path = Path(srt_file.name)
        
        with tempfile.NamedTemporaryFile(suffix='.vtt', delete=False) as vtt_file:
            vtt_path = Path(vtt_file.name)
        
        # 生成字幕
        print("🔄 生成字幕...")
        generate_subtitles_from_segments(test_segments, srt_path, vtt_path)
        
        # 检查结果
        print("\n📄 简单测试结果:")
        
        if srt_path.exists():
            srt_size = srt_path.stat().st_size
            print(f"   SRT文件大小: {srt_size} 字节")
            
            if srt_size > 0:
                with open(srt_path, 'r', encoding='utf-8') as f:
                    srt_content = f.read()
                    print("   SRT完整内容:")
                    print("   " + "─" * 30)
                    for line in srt_content.split('\n'):
                        print(f"   {line}")
                    print("   " + "─" * 30)
        
        if vtt_path.exists():
            vtt_size = vtt_path.stat().st_size
            print(f"   VTT文件大小: {vtt_size} 字节")
            
            if vtt_size > 8:
                with open(vtt_path, 'r', encoding='utf-8') as f:
                    vtt_content = f.read()
                    print("   VTT完整内容:")
                    print("   " + "─" * 30)
                    for line in vtt_content.split('\n'):
                        print(f"   {line}")
                    print("   " + "─" * 30)
        
        # 清理
        try:
            srt_path.unlink()
            vtt_path.unlink()
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ 简单测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🔍 Audio2Sub Backend 字幕生成调试测试")
    print("=" * 60)
    
    # 测试1: whisper转录
    transcription_result = test_whisper_transcription()
    
    # 测试2: 使用转录结果生成字幕
    if transcription_result:
        test_subtitle_generation(transcription_result)
    
    # 测试3: 使用简单测试数据
    test_with_simple_segments()
    
    print("\n" + "=" * 60)
    print("🔍 测试完成")

if __name__ == "__main__":
    main()
