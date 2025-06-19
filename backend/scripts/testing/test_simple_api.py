#!/usr/bin/env python3
"""
简单的 API 功能测试脚本
"""
import requests
import time
import json

def test_simple_upload():
    """简单的上传测试"""
    base_url = "http://localhost:8000"
    
    # 1. 健康检查
    print("🔍 健康检查...")
    health = requests.get(f"{base_url}/health").json()
    print(f"状态: {health['status']}")
    
    # 2. 获取模型列表
    print("\n📋 获取模型列表...")
    models = requests.get(f"{base_url}/models/").json()
    print(f"可用模型数量: {len(models['models'])}")
    print(f"默认模型: {models['default_model']}")
    
    # 3. 创建一个简单的"音频"文件（实际上是文本，但会被当作音频处理）
    print("\n📁 创建测试文件...")
    test_content = "Hello, this is a test audio content for transcription."
    
    # 4. 测试上传 - 使用 tiny 模型
    print("\n🚀 测试上传 (tiny 模型)...")
    files = {'file': ('test_audio.mp3', test_content.encode(), 'audio/mpeg')}
    data = {
        'model': 'tiny',
        'language': 'auto',
        'output_format': 'srt',
        'task': 'transcribe'
    }
    
    upload_response = requests.post(f"{base_url}/upload/", files=files, data=data)
    
    if upload_response.status_code == 200:
        result = upload_response.json()
        task_id = result['task_id']
        print(f"✅ 上传成功!")
        print(f"   任务ID: {task_id}")
        print(f"   模型: {result['model_used']}")
        print(f"   预估时间: {result['estimated_time']}秒")
        
        # 5. 监控任务状态
        print(f"\n⏳ 监控任务状态...")
        max_attempts = 30
        attempt = 1
        
        while attempt <= max_attempts:
            try:
                status_response = requests.get(f"{base_url}/status/{task_id}")
                if status_response.status_code == 200:
                    status = status_response.json()
                    state = status.get('state', 'UNKNOWN')
                    
                    print(f"尝试 {attempt}/{max_attempts} - 状态: {state}")
                    
                    if state == 'SUCCESS':
                        print("✅ 任务完成!")
                        result = status.get('result', {})
                        
                        # 显示结果详情
                        if 'timing' in result:
                            timing = result['timing']
                            print(f"   处理时间: {timing.get('total_time', 'N/A')}秒")
                        
                        if 'transcription_params' in result:
                            params = result['transcription_params']
                            print(f"   使用模型: {params.get('model', 'N/A')}")
                        
                        if 'files' in result:
                            files = result['files']
                            print(f"   生成文件: {len(files)} 个")
                            for file_info in files:
                                print(f"     - {file_info['filename']} ({file_info['type']})")
                        
                        if 'full_text' in result:
                            text = result['full_text']
                            preview = text[:100] + "..." if len(text) > 100 else text
                            print(f"   转录内容: {preview}")
                        
                        return True
                        
                    elif state == 'FAILURE':
                        print("❌ 任务失败!")
                        error_msg = status.get('result', {}).get('status', '未知错误')
                        print(f"   错误: {error_msg}")
                        return False
                    
                    elif state == 'PROGRESS':
                        result = status.get('result', {})
                        if isinstance(result, dict) and 'status' in result:
                            print(f"   进度: {result['status']}")
                    
                    time.sleep(3)
                else:
                    print(f"❌ 状态查询失败: {status_response.status_code}")
                    
            except Exception as e:
                print(f"❌ 状态查询错误: {e}")
            
            attempt += 1
        
        print("⏰ 任务监控超时")
        return False
        
    else:
        print(f"❌ 上传失败: {upload_response.status_code}")
        print(f"错误: {upload_response.text}")
        return False

if __name__ == "__main__":
    print("🎯 Audio2Sub API 简单功能测试")
    print("=" * 40)
    
    try:
        success = test_simple_upload()
        if success:
            print("\n🎉 测试成功完成!")
        else:
            print("\n❌ 测试失败")
    except Exception as e:
        print(f"\n🚨 测试出错: {e}")
