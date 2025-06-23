#!/usr/bin/env python3
"""
Audio2Sub API 动态模型选择测试脚本
测试不同模型的上传、转录和状态监控功能
"""
import requests
import json
import time
import os
from pathlib import Path

class Audio2SubAPITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health(self):
        """测试健康检查"""
        print("🔍 Testing health endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            print(f"✅ Health Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    def get_available_models(self):
        """获取可用模型列表"""
        print("\n📋 Getting available models...")
        try:
            response = self.session.get(f"{self.base_url}/models/")
            if response.status_code == 200:
                models_data = response.json()
                models = models_data.get('models', [])
                default_model = models_data.get('default_model', 'base')
                
                print("✅ Available models:")
                print(f"   Default model: {default_model}")
                for model in models:
                    print(f"   • {model['name']}: {model['use_case']}")
                    print(f"     Size: {model['size']}, Speed: {model['speed']}, Accuracy: {model['accuracy']}")
                return models
            else:
                print(f"❌ Failed to get models: {response.status_code}")
                print(f"   Response: {response.text}")
                return []
        except Exception as e:
            print(f"❌ Error getting models: {e}")
            return []
    
    def create_test_audio(self):
        """创建一个测试音频文件（模拟）"""
        test_content = """
        Hello, this is a test audio file for Audio2Sub API testing.
        We are testing different Whisper models including tiny, base, and small.
        Each model has different speed and accuracy characteristics.
        This test helps validate the dynamic model selection functionality.
        """
        test_file = Path("test_audio_sample.txt")
        test_file.write_text(test_content.strip())
        print(f"📁 Created test file: {test_file} ({test_file.stat().st_size} bytes)")
        return test_file
    
    def upload_with_model(self, audio_file, model="base", language="auto", 
                         output_format="both", task="transcribe"):
        """使用指定模型上传音频文件"""
        print(f"\n🚀 Testing upload with model: {model}")
        print(f"   Language: {language}")
        print(f"   Output format: {output_format}")
        print(f"   Task: {task}")
        
        try:
            # 准备文件和数据
            with open(audio_file, 'rb') as f:
                files = {'file': (audio_file.name, f, 'audio/mpeg')}
                data = {
                    'model': model,
                    'language': language,
                    'output_format': output_format,
                    'task': task
                }
                
                response = self.session.post(
                    f"{self.base_url}/upload/",
                    files=files,
                    data=data
                )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Upload successful!")
                print(f"   Task ID: {result['task_id']}")
                print(f"   File ID: {result['file_id']}")
                print(f"   Model used: {result.get('model_used', 'N/A')}")
                print(f"   Estimated time: {result.get('estimated_time', 'N/A')} seconds")
                print(f"   Message: {result.get('message', 'N/A')}")
                return result
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return None
    
    def check_task_status(self, task_id, max_wait=300):
        """检查任务状态并等待完成"""
        print(f"\n⏳ Monitoring task: {task_id}")
        
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < max_wait:
            try:
                response = self.session.get(f"{self.base_url}/status/{task_id}")
                if response.status_code == 200:
                    status_data = response.json()
                    current_status = status_data.get('state', 'UNKNOWN')
                    
                    if current_status != last_status:
                        print(f"   Status: {current_status}")
                        # 安全地检查嵌套字典
                        result_data = status_data.get('result')
                        if result_data and isinstance(result_data, dict) and 'status' in result_data:
                            print(f"   Details: {result_data['status']}")
                        last_status = current_status
                    
                    if current_status == 'SUCCESS':
                        result = status_data.get('result', {})
                        print("✅ Task completed successfully!")
                        
                        # 显示详细结果
                        if 'timing' in result:
                            timing = result['timing']
                            print(f"   Total time: {timing.get('total_time', 'N/A')}s")
                            print(f"   Transcription time: {timing.get('transcription_time', 'N/A')}s")
                        
                        if 'transcription_params' in result:
                            params = result['transcription_params']
                            print(f"   Model used: {params.get('model', 'N/A')}")
                            print(f"   Language: {params.get('language', 'N/A')}")
                        
                        if 'files' in result:
                            files = result['files']
                            print(f"   Generated files: {len(files)}")
                            for file_info in files:
                                print(f"     - {file_info['filename']} ({file_info['type']})")
                        
                        return result
                        
                    elif current_status == 'FAILURE':
                        print(f"❌ Task failed: {status_data.get('status', 'Unknown error')}")
                        return status_data
                    elif current_status == 'PROGRESS':
                        progress_info = status_data.get('result', {})
                        if isinstance(progress_info, dict) and 'status' in progress_info:
                            print(f"   Progress: {progress_info['status']}")
                    
                    time.sleep(3)
                else:
                    print(f"❌ Status check failed: {response.status_code}")
                    time.sleep(5)
                    
            except Exception as e:
                print(f"❌ Status check error: {e}")
                time.sleep(5)
        
        print("⏰ Timeout waiting for task completion")
        return None
    
    def run_model_comparison_test(self, audio_file):
        """运行不同模型的比较测试"""
        print("\n🔬 Running model comparison tests...")
        
        # 测试不同的模型配置
        test_configs = [
            {
                "model": "tiny",
                "description": "最快速度，适合实时处理",
                "language": "auto",
                "output_format": "srt"
            },
            {
                "model": "base", 
                "description": "平衡速度和质量",
                "language": "zh",
                "output_format": "vtt"
            },
            {
                "model": "small",
                "description": "更好的准确度",
                "language": "auto",
                "output_format": "both"
            }
        ]
        
        results = []
        
        for i, config in enumerate(test_configs, 1):
            print(f"\n--- Test {i}/{len(test_configs)}: {config['model']} model ---")
            print(f"Description: {config['description']}")
            
            # 上传任务
            upload_result = self.upload_with_model(
                audio_file,
                model=config["model"],
                language=config["language"],
                output_format=config["output_format"]
            )
            
            if upload_result:
                # 等待完成
                task_result = self.check_task_status(upload_result['task_id'])
                if task_result:
                    results.append({
                        "model": config["model"],
                        "config": config,
                        "task_id": upload_result['task_id'],
                        "result": task_result
                    })
                    print(f"✅ Test {i} completed")
                else:
                    print(f"❌ Test {i} failed or timed out")
            else:
                print(f"❌ Test {i} upload failed")
            
            print("-" * 50)
        
        return results
    
    def print_test_summary(self, results):
        """打印测试结果汇总"""
        print("\n" + "="*60)
        print("📊 MODEL COMPARISON SUMMARY")
        print("="*60)
        
        if not results:
            print("❌ No successful test results to display")
            return
        
        for result in results:
            model = result["model"]
            task_result = result["result"]
            
            print(f"\n🔹 Model: {model.upper()}")
            
            if 'status' in task_result:
                print(f"   Status: {task_result['status']}")
            
            if 'timing' in task_result:
                timing = task_result['timing']
                print(f"   Processing Time: {timing.get('total_time', 'N/A')}s")
                print(f"   Transcription Time: {timing.get('transcription_time', 'N/A')}s")
            
            if 'transcription_params' in task_result:
                params = task_result['transcription_params']
                print(f"   Parameters:")
                print(f"     - Language: {params.get('language', 'N/A')}")
                print(f"     - Output format: {params.get('output_format', 'N/A')}")
                print(f"     - Task type: {params.get('task_type', 'N/A')}")
            
            if 'files' in task_result:
                files = task_result['files']
                print(f"   Generated Files: {len(files)} files")
                for file_info in files:
                    print(f"     - {file_info['filename']} ({file_info['type']})")
            
            if 'full_text' in task_result:
                text = task_result['full_text']
                preview = text[:100] + "..." if len(text) > 100 else text
                print(f"   Transcription preview: {preview}")

def main():
    """主测试函数"""
    # 创建测试器实例
    tester = Audio2SubAPITester()
    
    print("🎯 Audio2Sub API Model Selection Testing")
    print("=" * 50)
    
    # 1. 健康检查
    if not tester.test_health():
        print("❌ API is not available. Please check if the server is running.")
        print("💡 Startup commands:")
        print("   Backend: uvicorn app.main:app --reload")
        print("   Celery: celery -A celery_app.celery_app worker --loglevel=info")
        return False
    
    # 2. 获取可用模型
    models = tester.get_available_models()
    if not models:
        print("❌ No models available")
        return False
    
    # 3. 创建测试文件
    test_file = tester.create_test_audio()
    
    try:
        # 4. 运行模型比较测试
        results = tester.run_model_comparison_test(test_file)
        
        # 5. 打印结果汇总
        tester.print_test_summary(results)
        
        if results:
            print(f"\n✅ Testing completed! Successfully tested {len(results)} models.")
            return True
        else:
            print("\n❌ No test results to display")
            return False
            
    finally:
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()
            print(f"\n🧹 Cleaned up test file: {test_file}")

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
