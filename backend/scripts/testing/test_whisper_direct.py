#!/usr/bin/env python3
"""
直接测试 whisper.cpp 的输出和解析
"""
import subprocess
import json
import tempfile
import os
from pathlib import Path

def test_whisper_cpp_directly():
    """直接测试 whisper.cpp"""
    
    # 检查是否有可用的音频文件
    test_audio_files = [
        "/Users/creed/Workspace/OpenSource/audio2sub/backend/uploads/test.wav",
        "/Users/creed/Workspace/OpenSource/audio2sub/backend/uploads/test.mp3",
        "/System/Library/Sounds/Ping.aiff",  # macOS 系统音频
        "/System/Library/Sounds/Glass.aiff"
    ]
    
    audio_file = None
    for test_file in test_audio_files:
        if os.path.exists(test_file):
            audio_file = test_file
            break
    
    if not audio_file:
        print("❌ 没有找到可用的音频文件")
        print("💡 建议:")
        print("1. 上传一个真实的音频文件到 uploads/ 目录")
        print("2. 或者使用录音软件录制一段中文语音")
        return
    
    print(f"🎵 使用音频文件: {audio_file}")
    
    # whisper.cpp 路径
    whisper_cpp_paths = [
        "/usr/local/bin/whisper-cli",
        "/opt/homebrew/bin/whisper-cli", 
        "./whisper.cpp/main",
        "/usr/local/bin/main"
    ]
    
    whisper_cpp = None
    for path in whisper_cpp_paths:
        if os.path.exists(path):
            whisper_cpp = path
            break
    
    if not whisper_cpp:
        print("❌ 没有找到 whisper.cpp 可执行文件")
        print("💡 请确保 whisper.cpp 已正确安装")
        return
    
    print(f"🔧 使用 whisper.cpp: {whisper_cpp}")
    
    # 模型文件
    model_file = "/Users/creed/Workspace/OpenSource/audio2sub/backend/models/ggml-base.bin"
    if not os.path.exists(model_file):
        print(f"❌ 模型文件不存在: {model_file}")
        return
    
    print(f"🤖 使用模型: {model_file}")
    
    # 测试不同的参数组合
    test_cases = [
        {
            "name": "自动检测语言",
            "args": ["-f", audio_file, "-m", model_file, "-oj", "-of", "/tmp/test_auto"]
        },
        {
            "name": "指定中文",
            "args": ["-f", audio_file, "-m", model_file, "-oj", "-of", "/tmp/test_zh", "-l", "zh"]
        },
        {
            "name": "翻译为英文",
            "args": ["-f", audio_file, "-m", model_file, "-oj", "-of", "/tmp/test_translate", "--translate"]
        },
        {
            "name": "中文 + 翻译",
            "args": ["-f", audio_file, "-m", model_file, "-oj", "-of", "/tmp/test_zh_translate", "-l", "zh", "--translate"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*20} 测试 {i}: {test_case['name']} {'='*20}")
        
        cmd = [whisper_cpp] + test_case['args']
        print(f"🚀 执行命令: {' '.join(cmd)}")
        
        try:
            # 运行命令
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            print(f"📊 返回码: {result.returncode}")
            
            if result.returncode == 0:
                print("✅ 执行成功")
                
                # 查看 stdout
                if result.stdout.strip():
                    print(f"📤 stdout (前200字符):")
                    print(f"   {result.stdout[:200]}...")
                
                # 查看 JSON 输出文件
                json_file = f"/tmp/test_{test_case['name'].split()[0].lower()}.json"
                if os.path.exists(json_file):
                    print(f"📄 JSON 文件存在: {json_file}")
                    with open(json_file, 'r', encoding='utf-8') as f:
                        try:
                            json_content = json.load(f)
                            print(f"   JSON 结构: {list(json_content.keys())}")
                            
                            # 提取转录内容
                            if 'transcription' in json_content:
                                transcription = json_content['transcription']
                                if transcription:
                                    full_text = " ".join([seg.get('text', '').strip() for seg in transcription])
                                    print(f"   转录结果: {full_text[:100]}...")
                                    
                                    # 检查语言
                                    if any(char >= '\u4e00' and char <= '\u9fff' for char in full_text):
                                        print(f"   ✅ 包含中文字符")
                                    else:
                                        print(f"   ❌ 不包含中文字符")
                                else:
                                    print(f"   ❌ transcription 数组为空")
                            
                            if 'result' in json_content:
                                result_info = json_content['result']
                                detected_lang = result_info.get('language', 'unknown')
                                print(f"   检测到的语言: {detected_lang}")
                                
                        except json.JSONDecodeError as e:
                            print(f"   ❌ JSON 解析失败: {e}")
                            print(f"   文件内容 (前100字符): {open(json_file).read()[:100]}...")
                    
                    # 清理文件
                    os.unlink(json_file)
                else:
                    print(f"❌ JSON 文件不存在: {json_file}")
                
            else:
                print("❌ 执行失败")
                if result.stderr:
                    print(f"📥 stderr: {result.stderr[:200]}...")
                    
        except subprocess.TimeoutExpired:
            print("⏰ 执行超时")
        except Exception as e:
            print(f"🚨 执行出错: {e}")
        
        print("-" * 60)
    
    print("\n📝 总结:")
    print("1. 如果所有测试都失败，可能是 whisper.cpp 安装或配置问题")
    print("2. 如果能转录但语言不对，可能是语言检测或参数问题")  
    print("3. 如果转录为空，可能是音频格式或质量问题")
    print("4. 建议使用真实的中文语音文件进行测试")

if __name__ == "__main__":
    test_whisper_cpp_directly()
