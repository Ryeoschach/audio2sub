#!/usr/bin/env python3
"""
简单的API测试脚本，用于验证后端服务是否正常工作
"""

import requests
import time
import json

# API基础URL
BASE_URL = "http://localhost:8000"

def test_ping():
    """测试ping接口"""
    try:
        response = requests.get(f"{BASE_URL}/ping")
        print(f"✅ Ping test: {response.status_code} - {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Ping test failed: {e}")
        return False

def test_upload_with_sample_audio():
    """测试上传一个简单的音频文件"""
    # 首先创建一个简单的测试音频文件（使用ffmpeg生成一个短的静音音频）
    import subprocess
    import os
    
    test_audio_path = "test_silence.wav"
    
    try:
        # 生成一个3秒的静音测试音频
        subprocess.run([
            "ffmpeg", "-f", "lavfi", "-i", "anullsrc=channel_layout=mono:sample_rate=16000",
            "-t", "3", "-y", test_audio_path
        ], check=True, capture_output=True)
        
        print(f"✅ Created test audio file: {test_audio_path}")
        
        # 上传文件
        with open(test_audio_path, 'rb') as f:
            files = {'file': (test_audio_path, f, 'audio/wav')}
            response = requests.post(f"{BASE_URL}/upload/", files=files)
        
        if response.status_code in [200, 202]:  # 202 means accepted
            result = response.json()
            print(f"✅ Upload successful: {result}")
            
            # 获取任务ID
            task_id = result.get('task_id')
            if task_id:
                # 等待任务完成
                print(f"⏳ Waiting for task {task_id} to complete...")
                for i in range(30):  # 最多等待30秒
                    status_response = requests.get(f"{BASE_URL}/status/{task_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status', 'Unknown')
                        print(f"📊 Task status: {status}")
                        
                        if status == 'SUCCESS':
                            print(f"✅ Task completed successfully: {status_data}")
                            return True
                        elif status == 'FAILURE':
                            print(f"❌ Task failed: {status_data}")
                            return False
                    
                    time.sleep(1)
                
                print("⏰ Task timed out after 30 seconds")
                return False
            
            return True
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create test audio: {e}")
        return False
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        return False
    finally:
        # 清理测试文件
        if os.path.exists(test_audio_path):
            os.remove(test_audio_path)
            print(f"🧹 Cleaned up test file: {test_audio_path}")

def main():
    """运行所有测试"""
    print("🚀 Starting API tests...")
    print("=" * 50)
    
    # 测试ping
    if not test_ping():
        print("❌ Basic connectivity failed. Make sure the server is running.")
        return
    
    print("\n" + "=" * 50)
    
    # 测试上传
    test_upload_with_sample_audio()
    
    print("\n" + "=" * 50)
    print("🏁 API tests completed!")

if __name__ == "__main__":
    main()
