#!/usr/bin/env python3
"""
完整的模型测试脚本 - 测试多个模型和参数组合
"""
import requests
import time
import json

def test_model_configuration(model, language, output_format, description):
    """测试特定的模型配置"""
    base_url = "http://localhost:8000"
    
    print(f"\n🧪 测试配置: {description}")
    print(f"   模型: {model}")
    print(f"   语言: {language}")
    print(f"   输出格式: {output_format}")
    
    # 创建测试内容
    test_content = f"Hello, this is a test for {model} model with {language} language."
    
    # 上传文件
    files = {'file': ('test_audio.mp3', test_content.encode(), 'audio/mpeg')}
    data = {
        'model': model,
        'language': language,
        'output_format': output_format,
        'task': 'transcribe'
    }
    
    try:
        upload_response = requests.post(f"{base_url}/upload/", files=files, data=data)
        
        if upload_response.status_code == 200:
            result = upload_response.json()
            task_id = result['task_id']
            
            print(f"✅ 上传成功，任务ID: {task_id}")
            print(f"   预估时间: {result['estimated_time']}秒")
            
            # 监控任务
            max_attempts = 20
            for attempt in range(1, max_attempts + 1):
                status_response = requests.get(f"{base_url}/status/{task_id}")
                if status_response.status_code == 200:
                    status = status_response.json()
                    state = status.get('state', 'UNKNOWN')
                    
                    if state == 'SUCCESS':
                        result = status.get('result', {})
                        print(f"✅ 任务完成!")
                        
                        # 显示结果
                        if 'timing' in result:
                            timing = result['timing']
                            print(f"   处理时间: {timing.get('total_time', 'N/A')}秒")
                        
                        if 'files' in result:
                            files = result['files']
                            print(f"   生成文件: {len(files)} 个")
                            for file_info in files:
                                print(f"     - {file_info['filename']} ({file_info['type']})")
                        
                        return True
                        
                    elif state == 'FAILURE':
                        error_msg = status.get('result', {})
                        print(f"❌ 任务失败: {error_msg}")
                        return False
                    
                    elif state in ['PROGRESS', 'STARTED']:
                        if attempt % 3 == 0:  # 每3次显示一次进度
                            print(f"   处理中... (尝试 {attempt}/{max_attempts})")
                
                time.sleep(2)
            
            print("⏰ 任务超时")
            return False
            
        else:
            print(f"❌ 上传失败: {upload_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 Audio2Sub API 完整模型测试")
    print("=" * 50)
    
    # 测试配置列表
    test_configs = [
        {
            "model": "tiny",
            "language": "auto",
            "output_format": "srt",
            "description": "最快速度模型 + 自动语言检测 + SRT输出"
        },
        {
            "model": "base",
            "language": "zh",
            "output_format": "vtt",
            "description": "推荐模型 + 中文 + VTT输出"
        },
        {
            "model": "small",
            "language": "en",
            "output_format": "both",
            "description": "高质量模型 + 英文 + 双格式输出"
        },
        {
            "model": "base",
            "language": "auto",
            "output_format": "both",
            "description": "平衡配置 + 自动检测 + 双格式"
        }
    ]
    
    # 运行测试
    results = []
    for i, config in enumerate(test_configs, 1):
        print(f"\n--- 测试 {i}/{len(test_configs)} ---")
        success = test_model_configuration(
            config["model"],
            config["language"], 
            config["output_format"],
            config["description"]
        )
        
        results.append({
            "config": config,
            "success": success
        })
        
        print("-" * 40)
    
    # 打印总结
    print(f"\n📊 测试总结")
    print("=" * 30)
    
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    
    print(f"总测试数: {total_count}")
    print(f"成功: {success_count}")
    print(f"失败: {total_count - success_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    print(f"\n详细结果:")
    for i, result in enumerate(results, 1):
        config = result["config"]
        status = "✅ 成功" if result["success"] else "❌ 失败"
        print(f"{i}. {config['model']} + {config['language']} + {config['output_format']}: {status}")
    
    if success_count == total_count:
        print(f"\n🎉 所有测试都成功! 动态模型选择功能完全正常!")
        return True
    else:
        print(f"\n⚠️  部分测试失败，请检查配置")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
