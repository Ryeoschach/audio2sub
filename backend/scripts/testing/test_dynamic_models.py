#!/usr/bin/env python3
"""
动态模型选择功能测试脚本
"""
import requests
import json
import time
from pathlib import Path

# 测试配置
API_BASE_URL = "http://localhost:8000"
TEST_AUDIO_FILE = "test_audio.wav"  # 请提供一个测试音频文件

def test_models_api():
    """测试获取模型列表 API"""
    print("🧪 测试模型列表 API...")
    try:
        response = requests.get(f"{API_BASE_URL}/models/")
        if response.status_code == 200:
            models_data = response.json()
            print("✅ 模型列表获取成功:")
            print(f"   默认模型: {models_data['default_model']}")
            print("   支持的模型:")
            for model in models_data['models']:
                print(f"   - {model['name']}: {model['size']} ({model['accuracy']}) - {model['use_case']}")
            return True
        else:
            print(f"❌ 模型列表获取失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def test_transcription_with_model(audio_file_path: str, model: str = "base", language: str = "auto"):
    """测试使用指定模型进行转录"""
    print(f"\n🧪 测试转录 API (模型: {model}, 语言: {language})...")
    
    if not Path(audio_file_path).exists():
        print(f"❌ 音频文件不存在: {audio_file_path}")
        return False
    
    try:
        # 上传文件进行转录
        with open(audio_file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'model': model,
                'language': language,
                'output_format': 'both',
                'task': 'transcribe'
            }
            
            response = requests.post(f"{API_BASE_URL}/upload/", files=files, data=data)
            
        if response.status_code == 200:
            result = response.json()
            task_id = result['task_id']
            print(f"✅ 转录任务已创建:")
            print(f"   任务ID: {task_id}")
            print(f"   使用模型: {result['model_used']}")
            print(f"   预估时间: {result['estimated_time']}秒")
            
            # 监控任务状态
            return monitor_task_status(task_id)
        else:
            print(f"❌ 转录请求失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 转录测试失败: {e}")
        return False

def monitor_task_status(task_id: str, timeout: int = 300):
    """监控任务状态"""
    print(f"\n📊 监控任务状态: {task_id}")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{API_BASE_URL}/status/{task_id}")
            if response.status_code == 200:
                status_data = response.json()
                state = status_data.get('state', 'UNKNOWN')
                
                if state == 'PENDING':
                    print("⏳ 任务等待中...")
                elif state == 'PROGRESS':
                    progress = status_data.get('current', 0)
                    status = status_data.get('status', '')
                    print(f"🔄 任务进行中: {progress}% - {status}")
                elif state == 'SUCCESS':
                    result = status_data.get('result', {})
                    print("✅ 任务完成!")
                    print(f"   使用模型: {result.get('transcription_params', {}).get('model', 'unknown')}")
                    print(f"   处理时间: {result.get('timing', {}).get('total_time_formatted', 'unknown')}")
                    print(f"   生成文件: {len(result.get('files', []))} 个")
                    for file_info in result.get('files', []):
                        print(f"     - {file_info['type'].upper()}: {file_info['filename']}")
                    return True
                elif state == 'FAILURE':
                    print(f"❌ 任务失败: {status_data.get('status', 'Unknown error')}")
                    return False
                
                time.sleep(2)
            else:
                print(f"❌ 状态查询失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 状态监控失败: {e}")
            return False
    
    print("⏰ 任务超时")
    return False

def main():
    """主测试函数"""
    print("🚀 Audio2Sub 动态模型选择功能测试")
    print("=" * 50)
    
    # 测试 1: 获取模型列表
    if not test_models_api():
        print("❌ 模型列表测试失败，停止测试")
        return
    
    # 检查测试文件
    if not Path(TEST_AUDIO_FILE).exists():
        print(f"\n⚠️  测试音频文件不存在: {TEST_AUDIO_FILE}")
        print("请提供一个测试音频文件或修改 TEST_AUDIO_FILE 变量")
        return
    
    # 测试 2: 使用不同模型进行转录
    test_models = ["tiny", "base", "small"]
    
    for model in test_models:
        success = test_transcription_with_model(TEST_AUDIO_FILE, model=model)
        if success:
            print(f"✅ 模型 {model} 测试成功")
        else:
            print(f"❌ 模型 {model} 测试失败")
        
        print("-" * 30)
    
    print("🏁 测试完成!")

if __name__ == "__main__":
    main()
