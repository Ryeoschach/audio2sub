#!/usr/bin/env python3
"""
简单的字幕生成问题调试测试
在uv虚拟环境中运行
"""

import sys
import json
from pathlib import Path

# 确保使用当前目录的模块
sys.path.insert(0, '.')

def test_whisper_transcription():
    """测试whisper转录输出格式"""
    print("🔍 测试Whisper转录输出格式")
    
    try:
        from app.whisper_manager import get_whisper_manager
        
        # 测试转录
        manager = get_whisper_manager()
        test_audio = "/Users/creed/workspace/sourceCode/whisper.cpp/111.wav"
        
        if not Path(test_audio).exists():
            print(f"❌ 测试音频文件不存在: {test_audio}")
            return False
        
        print(f"🎙️ 开始转录: {test_audio}")
        result = manager.transcribe(test_audio)
        
        print("📊 转录结果分析:")
        print(f"   - 结果类型: {type(result)}")
        print(f"   - 结果键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        
        # 详细检查segments
        if 'segments' in result:
            segments = result['segments']
            print(f"   - segments类型: {type(segments)}")
            print(f"   - segments数量: {len(segments) if isinstance(segments, list) else 'N/A'}")
            
            if isinstance(segments, list) and len(segments) > 0:
                print(f"   - 第一个segment结构: {segments[0]}")
                print(f"   - segment键: {list(segments[0].keys()) if isinstance(segments[0], dict) else 'N/A'}")
                
                # 检查时间戳格式
                first_seg = segments[0]
                if 'start' in first_seg and 'end' in first_seg:
                    print(f"   - 时间戳格式: start={first_seg['start']}, end={first_seg['end']}")
                    print(f"   - 时间戳类型: start={type(first_seg['start'])}, end={type(first_seg['end'])}")
            else:
                print("   ⚠️ segments为空！")
                return False
        else:
            print("   ❌ 没有segments字段！")
            return False
        
        return True, result
        
    except Exception as e:
        print(f"❌ 转录测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_subtitle_generation_with_real_data(transcription_result):
    """使用真实转录数据测试字幕生成"""
    print("\n🧪 使用真实数据测试字幕生成")
    
    if not transcription_result:
        print("❌ 没有转录数据")
        return False
    
    try:
        from app.tasks import generate_subtitles_from_segments
        import tempfile
        
        segments = transcription_result.get('segments', [])
        print(f"📊 使用segments数量: {len(segments)}")
        
        if not segments:
            print("❌ 没有segments数据")
            return False
        
        # 显示前几个segments的详细信息
        print("📋 前3个segments详情:")
        for i, seg in enumerate(segments[:3]):
            print(f"   Segment {i+1}:")
            print(f"     - start: {seg.get('start')} ({type(seg.get('start'))})")
            print(f"     - end: {seg.get('end')} ({type(seg.get('end'))})")
            print(f"     - text: '{seg.get('text', '')}'")
        
        # 创建临时文件测试
        with tempfile.NamedTemporaryFile(suffix='.srt', delete=False) as srt_file:
            srt_path = Path(srt_file.name)
        
        with tempfile.NamedTemporaryFile(suffix='.vtt', delete=False) as vtt_file:
            vtt_path = Path(vtt_file.name)
        
        print(f"📁 临时文件: SRT={srt_path}, VTT={vtt_path}")
        
        # 调用字幕生成函数
        print("🔄 生成字幕...")
        generate_subtitles_from_segments(segments, srt_path, vtt_path)
        
        # 检查结果
        srt_size = srt_path.stat().st_size if srt_path.exists() else 0
        vtt_size = vtt_path.stat().st_size if vtt_path.exists() else 0
        
        print(f"📄 生成结果:")
        print(f"   - SRT文件大小: {srt_size} 字节")
        print(f"   - VTT文件大小: {vtt_size} 字节")
        
        # 显示文件内容
        if srt_size > 0:
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
                print(f"📄 SRT内容 (前500字符):")
                print(srt_content[:500])
        else:
            print("⚠️ SRT文件为空")
        
        if vtt_size > 8:  # 大于WEBVTT头部
            with open(vtt_path, 'r', encoding='utf-8') as f:
                vtt_content = f.read()
                print(f"📄 VTT内容 (前500字符):")
                print(vtt_content[:500])
        else:
            print("⚠️ VTT文件只有头部或为空")
        
        # 清理临时文件
        try:
            srt_path.unlink()
            vtt_path.unlink()
        except:
            pass
        
        return srt_size > 0 and vtt_size > 8
        
    except Exception as e:
        print(f"❌ 字幕生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_subtitle_generation_with_simple_data():
    """使用简单测试数据测试字幕生成"""
    print("\n🧪 使用简单测试数据测试字幕生成")
    
    try:
        from app.tasks import generate_subtitles_from_segments
        import tempfile
        
        # 创建简单测试数据
        test_segments = [
            {
                "start": 0.0,
                "end": 3.0,
                "text": "Hello everyone, this is a test.",
                "words": []
            },
            {
                "start": 3.0,
                "end": 6.0,
                "text": "This is another test segment.",
                "words": []
            },
            {
                "start": 6.0,
                "end": 9.0,
                "text": "Final test segment for verification.",
                "words": []
            }
        ]
        
        print(f"📊 测试segments数量: {len(test_segments)}")
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.srt', delete=False) as srt_file:
            srt_path = Path(srt_file.name)
        
        with tempfile.NamedTemporaryFile(suffix='.vtt', delete=False) as vtt_file:
            vtt_path = Path(vtt_file.name)
        
        print("🔄 生成字幕...")
        generate_subtitles_from_segments(test_segments, srt_path, vtt_path)
        
        # 检查结果
        srt_size = srt_path.stat().st_size if srt_path.exists() else 0
        vtt_size = vtt_path.stat().st_size if vtt_path.exists() else 0
        
        print(f"📄 生成结果:")
        print(f"   - SRT文件大小: {srt_size} 字节")
        print(f"   - VTT文件大小: {vtt_size} 字节")
        
        if srt_size > 0:
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
                print(f"📄 SRT内容:")
                print(srt_content)
        
        if vtt_size > 8:
            with open(vtt_path, 'r', encoding='utf-8') as f:
                vtt_content = f.read()
                print(f"📄 VTT内容:")
                print(vtt_content)
        
        # 清理
        try:
            srt_path.unlink()
            vtt_path.unlink()
        except:
            pass
        
        return srt_size > 0 and vtt_size > 8
        
    except Exception as e:
        print(f"❌ 简单数据字幕生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_recent_results():
    """检查最近的结果文件"""
    print("\n🔍 检查最近的结果文件")
    
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
    print(f"📁 最新任务目录: {latest_task}")
    
    # 检查文件
    files = list(latest_task.iterdir())
    for file in files:
        size = file.stat().st_size
        print(f"   - {file.name}: {size} 字节")
        
        # 如果是字幕文件且非空，显示内容
        if file.suffix in ['.srt', '.vtt'] and size > 0:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"     内容预览: {content[:100]}...")

def main():
    """主测试函数"""
    print("🎯 字幕生成问题调试测试")
    print("=" * 50)
    print(f"🐍 Python路径: {sys.executable}")
    print(f"📁 工作目录: {Path.cwd()}")
    
    # 1. 测试转录功能
    success, transcription_result = test_whisper_transcription()
    if not success:
        print("❌ 转录测试失败，终止测试")
        return False
    
    # 2. 使用真实数据测试字幕生成
    real_data_success = test_subtitle_generation_with_real_data(transcription_result)
    
    # 3. 使用简单数据测试字幕生成
    simple_data_success = test_subtitle_generation_with_simple_data()
    
    # 4. 检查最近的结果文件
    check_recent_results()
    
    print("\n" + "=" * 50)
    print("📊 测试结果:")
    print(f"   - 转录功能: {'✅' if success else '❌'}")
    print(f"   - 真实数据字幕生成: {'✅' if real_data_success else '❌'}")
    print(f"   - 简单数据字幕生成: {'✅' if simple_data_success else '❌'}")
    
    if real_data_success and simple_data_success:
        print("\n🎉 字幕生成功能正常！")
        return True
    else:
        print("\n❌ 字幕生成存在问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
