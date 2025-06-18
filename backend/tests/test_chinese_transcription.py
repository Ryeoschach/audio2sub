#!/usr/bin/env python3
"""
测试中文语音转录功能
"""

import sys
from pathlib import Path

# 确保使用当前目录的模块
sys.path.insert(0, '.')

def test_chinese_transcription():
    """测试中文语音转录"""
    print("🎌 测试中文语音转录功能")
    print("=" * 50)
    
    try:
        from app.config import settings
        from app.whisper_manager import get_whisper_manager
        
        # 显示当前配置
        print("📋 当前配置:")
        print(f"   - 语言设置: {settings.WHISPER_LANGUAGE}")
        print(f"   - 任务类型: {settings.WHISPER_TASK}")
        print(f"   - 模型名称: {settings.MODEL_NAME}")
        
        # 获取whisper manager
        manager = get_whisper_manager()
        print(f"✅ WhisperManager初始化成功")
        
        # 测试音频文件
        test_audio = "/Users/creed/workspace/sourceCode/whisper.cpp/111.wav"
        if not Path(test_audio).exists():
            print(f"❌ 测试音频文件不存在: {test_audio}")
            return False
        
        print(f"📁 音频文件: {test_audio}")
        
        # 执行转录
        print("🔄 开始转录...")
        result = manager.transcribe(test_audio)
        
        # 显示转录结果
        print("\n📊 转录结果:")
        print(f"   - 转录时间: {result.get('transcription_time', 0):.2f}秒")
        print(f"   - 检测语言: {result.get('language', 'unknown')}")
        print(f"   - 文本长度: {len(result.get('text', ''))}")
        print(f"   - 段落数量: {len(result.get('segments', []))}")
        
        # 显示转录文本
        full_text = result.get('text', '')
        if full_text:
            print(f"\n📝 转录文本:")
            print(f"   {full_text}")
        else:
            print("\n❌ 没有转录到任何文本")
        
        # 显示前几个段落
        segments = result.get('segments', [])
        if segments:
            print(f"\n📋 前3个段落:")
            for i, segment in enumerate(segments[:3]):
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                text = segment.get('text', '')
                print(f"   段落 {i+1}: [{start:.2f}s - {end:.2f}s] {text}")
        
        # 检查是否为中文内容
        if full_text:
            # 简单检查是否包含中文字符
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in full_text)
            if has_chinese:
                print("\n✅ 检测到中文内容，转录正常")
                return True
            else:
                print("\n⚠️ 未检测到中文内容，可能是翻译或英文音频")
                print("💡 提示: 如果音频是中文但结果是英文，请检查配置中的WHISPER_TASK设置")
                return False
        else:
            print("\n❌ 转录失败，没有生成任何文本")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print(f"🐍 Python: {sys.executable}")
    
    success = test_chinese_transcription()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 中文转录测试成功!")
    else:
        print("❌ 中文转录测试失败")
        print("\n🔧 可能的解决方案:")
        print("1. 确保config.py中WHISPER_LANGUAGE设置为'zh'")
        print("2. 确保config.py中WHISPER_TASK设置为'transcribe'")
        print("3. 确认音频文件确实包含中文语音")
    
    return success

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)
