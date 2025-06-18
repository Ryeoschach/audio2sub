#!/usr/bin/env python3
"""
简单测试whisper.cpp CPU转录功能
"""

import requests
import time
import sys
from pathlib import Path

def test_simple_transcription():
    """简单测试音频转录"""
    print("🎯 测试whisper.cpp CPU转录功能")
    print("=" * 40)
    
    # 检查服务是否运行
    try:
        response = requests.get("http://localhost:8000/ping", timeout=5)
        if response.status_code != 200:
            print("❌ API服务未运行")
            return False
    except:
        print("❌ 无法连接API服务")
        return False
    
    print("✅ API服务正常")
    
    # 准备测试音频
    test_audio = Path("/Users/creed/workspace/sourceCode/whisper.cpp/111.wav")
    if not test_audio.exists():
        print("❌ 测试音频文件不存在")
        return False
    
    print(f"✅ 找到测试音频: {test_audio}")
    
    # 上传文件
    try:
        with open(test_audio, 'rb') as f:
            files = {'file': (test_audio.name, f, 'audio/wav')}
            print("🔄 正在上传音频文件...")
            response = requests.post("http://localhost:8000/upload/", files=files, timeout=30)
        
        if response.status_code in [200, 202]:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ 文件上传成功，任务ID: {task_id}")
            
            # 等待任务完成
            print("🔄 等待转录完成...")
            max_wait = 180  # 最多等待3分钟
            wait_time = 0
            
            while wait_time < max_wait:
                try:
                    status_response = requests.get(f"http://localhost:8000/status/{task_id}", timeout=10)
                    if status_response.status_code == 200:
                        status_result = status_response.json()
                        state = status_result.get('state', 'Unknown')
                        status_msg = status_result.get('status', 'No status')
                        
                        print(f"📊 [{wait_time}s] 状态: {state} - {status_msg}")
                        
                        if state == 'SUCCESS':
                            print("🎉 转录成功完成！")
                            result_data = status_result.get('result', {})
                            print(f"📝 转录文本预览: {str(result_data.get('transcription_text', ''))[:100]}...")
                            return True
                        elif state == 'FAILURE':
                            print(f"❌ 转录失败: {status_msg}")
                            return False
                        
                    time.sleep(5)
                    wait_time += 5
                    
                except Exception as e:
                    print(f"⚠️ 状态检查错误: {e}")
                    time.sleep(5)
                    wait_time += 5
            
            print("⏰ 等待超时")
            return False
            
        else:
            print(f"❌ 上传失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_transcription()
    sys.exit(0 if success else 1)
