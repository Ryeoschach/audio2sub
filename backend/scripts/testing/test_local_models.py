#!/usr/bin/env python3
"""
测试本地可用的四个模型：tiny, base, small, large-v3-turbo
"""
import requests
import time
import json

def test_local_models():
    """测试本地可用的模型"""
    base_url = "http://localhost:8000"
    
    # 本地可用的模型
    available_models = ['tiny', 'base', 'small', 'large-v3-turbo']
    
    print("🎯 测试本地可用的 Whisper 模型")
    print("=" * 50)
    
    # 1. 健康检查
    print("🔍 API 健康检查...")
    try:
        health = requests.get(f"{base_url}/health").json()
        print(f"✅ API 状态: {health['status']}")
        print(f"   部署模式: {health['deployment']['mode']}")
        print(f"   设备: {health['deployment']['device']}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False
    
    # 2. 获取模型列表
    print("\n📋 获取支持的模型列表...")
    try:
        models_response = requests.get(f"{base_url}/models/").json()
        print(f"✅ 总共支持 {len(models_response['models'])} 个模型")
        print(f"   默认模型: {models_response['default_model']}")
    except Exception as e:
        print(f"❌ 获取模型列表失败: {e}")
        return False
    
    # 3. 创建测试内容
    test_content = """
    Hello, this is a comprehensive test for Audio2Sub dynamic model selection.
    We are testing four locally available models: tiny, base, small, and large-v3-turbo.
    Each model has different characteristics in terms of speed and accuracy.
    This test will help us compare their performance.
    Testing Chinese: 你好，这是一个测试文件，用于验证中文转录效果。
    Testing numbers: 1, 2, 3, 4, 5, 10, 100, 1000.
    Testing time: It's currently 2025, and we're testing on June 19th.
    """.strip()
    
    print(f"\n📁 测试内容已准备 ({len(test_content)} 字符)")
    
    # 4. 测试每个模型
    test_results = []
    
    for i, model in enumerate(available_models, 1):
        print(f"\n{'='*20} 测试 {i}/{len(available_models)}: {model.upper()} 模型 {'='*20}")
        
        # 根据模型选择不同的测试参数
        test_configs = {
            'tiny': {'language': 'auto', 'output_format': 'srt'},
            'base': {'language': 'zh', 'output_format': 'vtt'},
            'small': {'language': 'en', 'output_format': 'both'},
            'large-v3-turbo': {'language': 'auto', 'output_format': 'both'}
        }
        
        config = test_configs[model]
        print(f"🔧 配置: 语言={config['language']}, 输出={config['output_format']}")
        
        # 测试开始时间
        test_start = time.time()
        
        try:
            # 上传文件
            files = {'file': (f'test_{model}.mp3', test_content.encode(), 'audio/mpeg')}
            data = {
                'model': model,
                'language': config['language'],
                'output_format': config['output_format'],
                'task': 'transcribe'
            }
            
            print("🚀 上传文件...")
            upload_response = requests.post(f"{base_url}/upload/", files=files, data=data)
            
            if upload_response.status_code != 200:
                print(f"❌ 上传失败: {upload_response.status_code}")
                print(f"   错误: {upload_response.text}")
                test_results.append({
                    'model': model,
                    'success': False,
                    'error': f"Upload failed: {upload_response.status_code}",
                    'total_time': time.time() - test_start
                })
                continue
            
            upload_result = upload_response.json()
            task_id = upload_result['task_id']
            
            print(f"✅ 上传成功!")
            print(f"   任务ID: {task_id}")
            print(f"   预估时间: {upload_result.get('estimated_time', 'N/A')}秒")
            
            # 监控任务状态
            print("⏳ 监控任务进度...")
            success, result = monitor_task(base_url, task_id, model, max_wait=180)  # 3分钟超时
            
            total_time = time.time() - test_start
            
            if success:
                print(f"✅ {model} 模型测试成功! (总耗时: {total_time:.1f}s)")
                
                # 提取详细信息
                test_results.append({
                    'model': model,
                    'success': True,
                    'total_time': total_time,
                    'processing_time': result.get('timing', {}).get('total_time', 'N/A'),
                    'transcription_time': result.get('timing', {}).get('transcription_time', 'N/A'),
                    'files_generated': len(result.get('files', [])),
                    'transcription_preview': result.get('full_text', '')[:100] + '...' if result.get('full_text') else 'N/A',
                    'config': config
                })
            else:
                print(f"❌ {model} 模型测试失败! (总耗时: {total_time:.1f}s)")
                test_results.append({
                    'model': model,
                    'success': False,
                    'error': result,
                    'total_time': total_time
                })
                
        except Exception as e:
            total_time = time.time() - test_start
            print(f"🚨 {model} 模型测试出错: {e}")
            test_results.append({
                'model': model,
                'success': False,
                'error': str(e),
                'total_time': total_time
            })
        
        print(f"⏱️  {model} 模型总耗时: {time.time() - test_start:.1f}秒")
        print("-" * 60)
    
    # 5. 显示测试总结
    print_test_summary(test_results)
    
    return test_results

def monitor_task(base_url, task_id, model_name, max_wait=300):
    """监控任务状态直到完成"""
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{base_url}/status/{task_id}")
            if response.status_code == 200:
                status_data = response.json()
                current_status = status_data.get('state', 'UNKNOWN')
                
                if current_status != last_status:
                    print(f"   📊 状态: {current_status}")
                    last_status = current_status
                
                if current_status == 'SUCCESS':
                    result = status_data.get('result', {})
                    
                    # 显示成功信息
                    if 'timing' in result:
                        timing = result['timing']
                        print(f"   ⏱️  处理时间: {timing.get('total_time', 'N/A')}s")
                        print(f"   🎙️  转录时间: {timing.get('transcription_time', 'N/A')}s")
                    
                    if 'files' in result:
                        files = result['files']
                        print(f"   📄 生成文件: {len(files)} 个")
                        for file_info in files:
                            print(f"      - {file_info['filename']} ({file_info['type']})")
                    
                    return True, result
                    
                elif current_status == 'FAILURE':
                    error_msg = status_data.get('status', '未知错误')
                    print(f"   🚨 失败原因: {error_msg}")
                    return False, error_msg
                
                elif current_status == 'PROGRESS':
                    # 显示进度信息
                    result = status_data.get('result', {})
                    if isinstance(result, dict) and 'status' in result:
                        print(f"   🔄 进度: {result['status']}")
                
                time.sleep(2)  # 每2秒检查一次
            else:
                print(f"   ⚠️  状态查询失败: {response.status_code}")
                time.sleep(5)
                
        except Exception as e:
            print(f"   ❌ 状态查询错误: {e}")
            time.sleep(3)
    
    print(f"   ⏰ 任务超时 (等待了 {max_wait}s)")
    return False, "Timeout"

def print_test_summary(results):
    """打印测试结果总结"""
    print("\n" + "="*80)
    print("📊 模型性能测试总结报告")
    print("="*80)
    
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    print(f"\n📈 总体统计:")
    print(f"   测试模型数: {total_count}")
    print(f"   成功测试: {success_count}")
    print(f"   失败测试: {total_count - success_count}")
    print(f"   成功率: {success_count/total_count*100:.1f}%")
    
    print(f"\n🏆 模型性能排行榜:")
    print("-" * 80)
    print(f"{'模型':<15} {'状态':<8} {'总耗时':<10} {'处理时间':<10} {'文件数':<8} {'配置'}")
    print("-" * 80)
    
    for result in results:
        model = result['model']
        status = "✅ 成功" if result['success'] else "❌ 失败"
        total_time = f"{result['total_time']:.1f}s"
        
        if result['success']:
            processing_time = f"{result['processing_time']}s" if result['processing_time'] != 'N/A' else 'N/A'
            files_count = str(result['files_generated'])
            config_str = f"{result['config']['language']}/{result['config']['output_format']}"
        else:
            processing_time = "N/A"
            files_count = "0"
            config_str = "N/A"
        
        print(f"{model:<15} {status:<8} {total_time:<10} {processing_time:<10} {files_count:<8} {config_str}")
    
    # 显示成功的转录预览
    print(f"\n📝 转录结果预览:")
    for result in results:
        if result['success'] and 'transcription_preview' in result:
            print(f"\n🔹 {result['model'].upper()} 模型:")
            print(f"   {result['transcription_preview']}")
    
    # 显示失败的错误信息
    failed_results = [r for r in results if not r['success']]
    if failed_results:
        print(f"\n🚨 失败原因分析:")
        for result in failed_results:
            print(f"   • {result['model']}: {result['error']}")
    
    print("\n" + "="*80)
    
    if success_count == total_count:
        print("🎉 恭喜！所有模型测试都成功完成！")
    elif success_count > 0:
        print(f"⚠️  部分测试成功，建议检查失败的模型配置。")
    else:
        print("❌ 所有测试都失败了，请检查系统配置。")

if __name__ == "__main__":
    print("🚀 开始测试本地可用的 Whisper 模型...")
    print(f"📅 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        results = test_local_models()
        
        # 保存测试结果到文件
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        result_file = f"model_test_results_{timestamp}.json"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 测试结果已保存到: {result_file}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n🚨 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
