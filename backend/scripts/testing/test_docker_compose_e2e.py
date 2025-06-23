#!/usr/bin/env python3
"""
Audio2Sub Docker Compose 端到端测试
测试完整的上传→转录→下载流程
"""

import requests
import time
import json
from pathlib import Path

def test_docker_compose_e2e():
    """测试Docker Compose部署的端到端功能"""
    print("🐳 Audio2Sub Docker Compose 端到端测试")
    print("=" * 50)
    
    # 测试音频文件路径
    test_audio_path = "/Users/creed/workspace/sourceCode/whisper.cpp/111.wav"
    if not Path(test_audio_path).exists():
        print(f"❌ 测试音频文件不存在: {test_audio_path}")
        return False
    
    base_url = "http://localhost:8000"
    
    # 1. 健康检查
    print("🔸 步骤1: 服务健康检查")
    try:
        health_response = requests.get(f"{base_url}/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ 服务状态: {health_data['status']}")
            print(f"🎙️ Whisper.cpp: {health_data['whisper_cpp']}")
            print(f"📡 Redis: {health_data['redis']}")
            print(f"🖥️ 设备: {health_data['device']}")
            print(f"📦 模型: {health_data['model']}")
        else:
            print(f"❌ 健康检查失败: {health_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False
        
    # 2. 根端点测试  
    print("\n🔸 步骤2: 根端点测试")
    try:
        root_response = requests.get(f"{base_url}/", timeout=10)
        if root_response.status_code == 200:
            root_data = root_response.json()
            print(f"✅ 应用名称: {root_data['app']}")
            print(f"📝 版本: {root_data['version']}")
            print("📋 可用端点:")
            for endpoint, path in root_data.get('endpoints', {}).items():
                print(f"   - {endpoint}: {path}")
        else:
            print(f"❌ 根端点测试失败: {root_response.status_code}")
    except Exception as e:
        print(f"❌ 根端点测试异常: {e}")
        
    # 3. 上传文件并开始转录
    print("\n🔸 步骤3: 上传音频文件")
    try:
        with open(test_audio_path, "rb") as audio_file:
            files = {"file": ("test_audio.wav", audio_file, "audio/wav")}
            upload_response = requests.post(f"{base_url}/upload/", files=files, timeout=30)
        
        if upload_response.status_code == 202:
            upload_data = upload_response.json()
            task_id = upload_data["task_id"]
            file_id = upload_data["file_id"]
            print(f"✅ 文件上传成功")
            print(f"📋 任务ID: {task_id}")
            print(f"📁 文件ID: {file_id}")
        else:
            print(f"❌ 文件上传失败: {upload_response.status_code}")
            print(f"响应内容: {upload_response.text}")
            return False
    except Exception as e:
        print(f"❌ 文件上传异常: {e}")
        return False
        
    # 4. 轮询任务状态
    print("\n🔸 步骤4: 轮询任务状态")
    max_attempts = 30  # 最多等待5分钟
    attempt = 0
    
    while attempt < max_attempts:
        try:
            status_response = requests.get(f"{base_url}/status/{task_id}", timeout=10)
            if status_response.status_code == 200:
                status_data = status_response.json()
                current_state = status_data.get("state", "UNKNOWN")
                
                print(f"🔄 第{attempt + 1}次检查 - 状态: {current_state}")
                
                if "result" in status_data:
                    result = status_data["result"]
                    if "progress" in result:
                        print(f"   进度: {result['progress']}")
                    if "message" in result:
                        print(f"   消息: {result['message']}")
                
                if current_state == "SUCCESS":
                    print("✅ 转录任务完成!")
                    result = status_data.get("result", {})
                    if "srt_file" in result:
                        print(f"📄 SRT文件: {result['srt_file']}")
                    if "vtt_file" in result:
                        print(f"📄 VTT文件: {result['vtt_file']}")
                    break
                elif current_state == "FAILURE":
                    print("❌ 转录任务失败!")
                    if "traceback" in status_data:
                        print(f"错误详情: {status_data['traceback']}")
                    return False
                elif current_state in ["PENDING", "PROGRESS"]:
                    # 继续等待
                    pass
                else:
                    print(f"⚠️ 未知状态: {current_state}")
                    
            else:
                print(f"❌ 状态查询失败: {status_response.status_code}")
                print(f"响应内容: {status_response.text}")
                
        except Exception as e:
            print(f"❌ 状态查询异常: {e}")
            
        attempt += 1
        if attempt < max_attempts:
            time.sleep(10)  # 等待10秒
    
    if attempt >= max_attempts:
        print("⏰ 任务等待超时")
        return False
        
    print("\n🎉 Docker Compose 端到端测试完成!")
    return True

def main():
    """主函数"""
    success = test_docker_compose_e2e()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
