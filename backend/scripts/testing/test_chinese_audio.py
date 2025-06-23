#!/usr/bin/env python3
"""
使用真实音频文件测试中文转录功能
"""
import requests
import time
import json
import shutil
from pathlib import Path

def test_chinese_audio():
    """测试中文音频转录"""
    base_url = "http://localhost:8000"
    audio_file_path = "/Users/creed/Desktop/audio.mp3"
    
    print("🎯 测试中文音频转录功能")
    print("=" * 50)
    
    # 检查音频文件是否存在
    if not Path(audio_file_path).exists():
        print(f"❌ 音频文件不存在: {audio_file_path}")
        return False
    
    file_size = Path(audio_file_path).stat().st_size
    print(f"📁 音频文件: {audio_file_path}")
    print(f"📊 文件大小: {file_size / 1024 / 1024:.2f} MB")
    
    # 检查是否有测试音频文件
    test_files = [
        "test_chinese.mp3",
        "test_chinese.wav", 
        "test.mp3",
        "test.wav",
        "chinese_audio.mp3",
        "chinese_audio.wav"
    ]
    
    audio_file = None
    for test_file in test_files:
        if Path(test_file).exists():
            audio_file = test_file
            print(f"✅ 找到测试文件: {audio_file}")
            break
    
    if not audio_file:
        print("❌ 没有找到测试音频文件")
        print("请将一个中文音频文件重命名为以下任一名称:")
        for name in test_files:
            print(f"  - {name}")
        return False
    
    # 测试不同的语言配置
    test_configs = [
        {
            "name": "自动检测",
            "language": "auto",
            "model": "base",
            "task": "transcribe"
        },
        {
            "name": "指定中文",
            "language": "zh",
            "model": "base", 
            "task": "transcribe"
        },
        {
            "name": "中文翻译为英文",
            "language": "zh",
            "model": "base",
            "task": "translate"
        }
    ]
    
    results = []
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n{'='*20} 测试 {i}/{len(test_configs)}: {config['name']} {'='*20}")
        print(f"🔧 配置: 语言={config['language']}, 模型={config['model']}, 任务={config['task']}")
        
        try:
            # 上传文件
            with open(audio_file, 'rb') as f:
                files = {'file': (audio_file, f, 'audio/mpeg')}
                data = {
                    'model': config['model'],
                    'language': config['language'],
                    'output_format': 'both',
                    'task': config['task']
                }
                
                print("🚀 上传文件...")
                upload_response = requests.post(f"{base_url}/upload/", files=files, data=data)
                
                if upload_response.status_code != 200:
                    print(f"❌ 上传失败: {upload_response.status_code}")
                    continue
                
                upload_result = upload_response.json()
                task_id = upload_result['task_id']
                
                print(f"✅ 上传成功! 任务ID: {task_id}")
                
                # 监控任务状态
                success, result = monitor_task(base_url, task_id, config['name'])
                
                if success:
                    results.append({
                        'config': config,
                        'result': result,
                        'success': True
                    })
                    
                    # 显示转录结果
                    print(f"🎙️  转录结果:")
                    full_text = result.get('full_text', '')
                    if full_text:
                        print(f"   文本: {full_text}")
                        
                        # 分析结果
                        chinese_chars = sum(1 for c in full_text if '\u4e00' <= c <= '\u9fff')
                        english_chars = sum(1 for c in full_text if c.isalpha() and c.isascii())
                        
                        print(f"   分析: 中文字符 {chinese_chars} 个, 英文字符 {english_chars} 个")
                        
                        if config['language'] == 'zh' and config['task'] == 'transcribe':
                            if chinese_chars > english_chars:
                                print("   ✅ 正确：中文语音转录为中文文本")
                            else:
                                print("   ❌ 异常：中文语音但转录结果主要是英文")
                        elif config['task'] == 'translate':
                            if english_chars > chinese_chars:
                                print("   ✅ 正确：成功翻译为英文")
                            else:
                                print("   ❌ 异常：翻译任务但结果不是英文")
                    else:
                        print("   ❌ 转录结果为空")
                        
                else:
                    print(f"❌ 任务失败: {result}")
                    
        except Exception as e:
            print(f"🚨 测试出错: {e}")
        
        print("-" * 60)
    
    # 显示对比结果
    if results:
        print_comparison_results(results)
    
    return len(results) > 0

def monitor_task(base_url, task_id, test_name, max_wait=180):
    """监控任务状态"""
    print("⏳ 监控任务进度...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{base_url}/status/{task_id}")
            if response.status_code == 200:
                status_data = response.json()
                state = status_data.get('state', 'UNKNOWN')
                
                if state == 'SUCCESS':
                    result = status_data.get('result', {})
                    print(f"✅ {test_name} 转录完成!")
                    
                    # 显示详细信息
                    if 'timing' in result:
                        timing = result['timing']
                        print(f"   处理时间: {timing.get('total_time', 'N/A')}s")
                    
                    if 'transcription_params' in result:
                        params = result['transcription_params']
                        print(f"   实际参数: 模型={params.get('model')}, 语言={params.get('language')}, 任务={params.get('task_type')}")
                    
                    return True, result
                    
                elif state == 'FAILURE':
                    error_msg = status_data.get('status', '未知错误')
                    print(f"❌ {test_name} 转录失败: {error_msg}")
                    return False, error_msg
                
                elif state in ['PROGRESS', 'STARTED']:
                    print(f"   📊 {state}...")
                
                time.sleep(3)
            else:
                print(f"   ⚠️  状态查询失败: {response.status_code}")
                time.sleep(5)
                
        except Exception as e:
            print(f"   ❌ 状态查询错误: {e}")
            time.sleep(3)
    
    print(f"   ⏰ 任务超时")
    return False, "Timeout"

def print_comparison_results(results):
    """打印对比结果"""
    print("\n" + "="*80)
    print("📊 中文转录测试结果对比")
    print("="*80)
    
    for i, item in enumerate(results, 1):
        config = item['config']
        result = item['result']
        
        print(f"\n🔹 测试 {i}: {config['name']}")
        print(f"   配置: language={config['language']}, task={config['task']}")
        
        full_text = result.get('full_text', '')
        if full_text:
            chinese_chars = sum(1 for c in full_text if '\u4e00' <= c <= '\u9fff')
            english_chars = sum(1 for c in full_text if c.isalpha() and c.isascii())
            
            print(f"   结果: {full_text[:100]}{'...' if len(full_text) > 100 else ''}")
            print(f"   统计: 中文字符 {chinese_chars} 个, 英文字符 {english_chars} 个")
            
            # 实际使用的参数
            if 'transcription_params' in result:
                params = result['transcription_params']
                print(f"   实际参数: language={params.get('language')}, task={params.get('task_type')}")
        else:
            print("   结果: 无转录文本")

if __name__ == "__main__":
    print("🚀 开始中文语音转录测试...")
    print(f"📅 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        success = create_real_audio_test()
        if success:
            print("\n🎉 测试完成!")
        else:
            print("\n❌ 测试未能完成")
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n🚨 测试出错: {e}")
        import traceback
        traceback.print_exc()
