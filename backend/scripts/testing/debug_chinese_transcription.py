#!/usr/bin/env python3
"""
调试中文语音转录问题
"""
import requests
import time
import json

def debug_chinese_transcription():
    """调试中文转录"""
    base_url = "http://localhost:8000"
    
    print("🔍 调试中文语音转录问题")
    print("=" * 50)
    
    # 创建中文测试内容
    chinese_content = """
    你好，我是一个中文语音测试文件。
    今天是2025年6月19日，天气很好。
    我们正在测试Audio2Sub的中文转录功能。
    希望这个测试能够正确识别中文语音。
    数字测试：一、二、三、四、五。
    时间测试：现在是晚上九点十分。
    """.strip()
    
    print(f"📁 中文测试内容: {chinese_content[:50]}...")
    
    # 测试不同的语言参数组合
    test_cases = [
        {
            "name": "自动检测 + 转录",
            "params": {"model": "base", "language": "auto", "task": "transcribe"}
        },
        {
            "name": "指定中文 + 转录", 
            "params": {"model": "base", "language": "zh", "task": "transcribe"}
        },
        {
            "name": "指定中文 + 翻译",
            "params": {"model": "base", "language": "zh", "task": "translate"}
        },
        {
            "name": "自动检测 + 翻译",
            "params": {"model": "base", "language": "auto", "task": "translate"}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*20} 测试 {i}: {test_case['name']} {'='*20}")
        
        params = test_case['params']
        print(f"🔧 参数: {params}")
        
        try:
            # 上传文件
            files = {'file': ('chinese_test.mp3', chinese_content.encode(), 'audio/mpeg')}
            data = {
                'model': params['model'],
                'language': params['language'],
                'output_format': 'srt',
                'task': params['task']
            }
            
            print("🚀 发送请求...")
            print(f"   请求数据: {data}")
            
            upload_response = requests.post(f"{base_url}/upload/", files=files, data=data)
            
            if upload_response.status_code != 200:
                print(f"❌ 上传失败: {upload_response.status_code}")
                print(f"   错误: {upload_response.text}")
                continue
            
            upload_result = upload_response.json()
            task_id = upload_result['task_id']
            
            print(f"✅ 上传成功! 任务ID: {task_id}")
            print(f"   使用模型: {upload_result.get('model_used', 'N/A')}")
            
            # 监控任务
            print("⏳ 等待转录结果...")
            max_attempts = 30
            
            for attempt in range(1, max_attempts + 1):
                time.sleep(2)
                
                status_response = requests.get(f"{base_url}/status/{task_id}")
                if status_response.status_code == 200:
                    status = status_response.json()
                    state = status.get('state', 'UNKNOWN')
                    
                    if state == 'SUCCESS':
                        result = status.get('result', {})
                        print(f"✅ 转录完成!")
                        
                        # 显示关键信息
                        transcription_params = result.get('transcription_params', {})
                        print(f"   实际使用参数:")
                        print(f"     模型: {transcription_params.get('model', 'N/A')}")
                        print(f"     语言: {transcription_params.get('language', 'N/A')}")
                        print(f"     任务: {transcription_params.get('task_type', 'N/A')}")
                        
                        # 显示转录结果
                        full_text = result.get('full_text', '')
                        if full_text:
                            print(f"   转录结果:")
                            print(f"     原文: {chinese_content[:100]}...")
                            print(f"     转录: {full_text[:100]}...")
                            
                            # 分析结果
                            if any(char >= '\u4e00' and char <= '\u9fff' for char in full_text):
                                print(f"   ✅ 结果包含中文字符")
                            else:
                                print(f"   ❌ 结果不包含中文字符 (可能是英文)")
                                
                            if len(full_text) < 10:
                                print(f"   ⚠️  转录结果很短，可能识别失败")
                        else:
                            print(f"   ❌ 没有转录结果")
                        
                        break
                        
                    elif state == 'FAILURE':
                        error_msg = status.get('status', '未知错误')
                        print(f"   ❌ 转录失败: {error_msg}")
                        break
                    
                    elif attempt % 5 == 0:  # 每10秒显示一次进度
                        print(f"   🔄 状态: {state} (尝试 {attempt}/{max_attempts})")
                
                if attempt == max_attempts:
                    print(f"   ⏰ 超时")
                    break
                    
        except Exception as e:
            print(f"🚨 测试出错: {e}")
        
        print("-" * 60)
    
    print("\n🔍 调试建议:")
    print("1. 检查转录结果中的语言检测")
    print("2. 确认 whisper.cpp 命令行参数")
    print("3. 验证模型是否支持中文")
    print("4. 检查音频文件格式和质量")

if __name__ == "__main__":
    debug_chinese_transcription()
