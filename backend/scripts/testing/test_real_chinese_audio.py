#!/usr/bin/env python3
"""
使用真实音频文件测试中文转录功能
"""
import requests
import time
import json
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
    
    # 1. 健康检查
    print("\n🔍 API 健康检查...")
    try:
        health = requests.get(f"{base_url}/health").json()
        print(f"✅ API 状态: {health['status']}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False
    
    # 2. 测试配置组合
    test_configs = [
        {
            "name": "自动检测 + SRT",
            "model": "base",
            "language": "auto", 
            "output_format": "srt",
            "task": "transcribe"
        },
        {
            "name": "指定中文 + VTT",
            "model": "base",
            "language": "zh",
            "output_format": "vtt", 
            "task": "transcribe"
        },
        {
            "name": "自动检测 + 翻译英文",
            "model": "base",
            "language": "auto",
            "output_format": "srt",
            "task": "translate"
        }
    ]
    
    results = []
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n{'='*20} 测试 {i}/{len(test_configs)}: {config['name']} {'='*20}")
        print(f"🔧 配置: 模型={config['model']}, 语言={config['language']}, 格式={config['output_format']}, 任务={config['task']}")
        
        test_start = time.time()
        
        try:
            # 上传文件
            with open(audio_file_path, 'rb') as f:
                files = {'file': ('audio.mp3', f, 'audio/mpeg')}
                data = {
                    'model': config['model'],
                    'language': config['language'],
                    'output_format': config['output_format'],
                    'task': config['task']
                }
                
                print("🚀 上传音频文件...")
                upload_response = requests.post(f"{base_url}/upload/", files=files, data=data)
            
            if upload_response.status_code != 200:
                print(f"❌ 上传失败: {upload_response.status_code}")
                print(f"   错误: {upload_response.text}")
                continue
            
            upload_result = upload_response.json()
            task_id = upload_result['task_id']
            
            print(f"✅ 上传成功!")
            print(f"   任务ID: {task_id}")
            print(f"   模型: {upload_result.get('model_used', 'N/A')}")
            print(f"   预估时间: {upload_result.get('estimated_time', 'N/A')}秒")
            
            # 监控任务状态
            print("⏳ 开始转录...")
            success, result = monitor_transcription_task(base_url, task_id, config['name'])
            
            total_time = time.time() - test_start
            
            if success:
                print(f"✅ {config['name']} 测试成功! (总耗时: {total_time:.1f}s)")
                
                # 分析转录结果
                analyze_transcription_result(result, config)
                
                results.append({
                    'config': config,
                    'success': True,
                    'total_time': total_time,
                    'result': result
                })
            else:
                print(f"❌ {config['name']} 测试失败! (总耗时: {total_time:.1f}s)")
                print(f"   错误: {result}")
                
                results.append({
                    'config': config,
                    'success': False,
                    'total_time': total_time,
                    'error': result
                })
                
        except Exception as e:
            total_time = time.time() - test_start
            print(f"🚨 {config['name']} 测试出错: {e}")
            results.append({
                'config': config,
                'success': False,
                'total_time': total_time,
                'error': str(e)
            })
        
        print("-" * 60)
    
    # 显示最终结果
    print_final_summary(results)
    
    return results

def monitor_transcription_task(base_url, task_id, test_name, max_wait=300):
    """监控转录任务"""
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
                    
                    # 显示进度信息
                    result = status_data.get('result', {})
                    if isinstance(result, dict) and 'status' in result:
                        print(f"   🔄 进度: {result['status']}")
                    
                    last_status = current_status
                
                if current_status == 'SUCCESS':
                    result = status_data.get('result', {})
                    return True, result
                    
                elif current_status == 'FAILURE':
                    error_msg = status_data.get('status', '未知错误')
                    return False, error_msg
                
                time.sleep(3)
            else:
                print(f"   ⚠️  状态查询失败: {response.status_code}")
                time.sleep(5)
                
        except Exception as e:
            print(f"   ❌ 状态查询错误: {e}")
            time.sleep(3)
    
    return False, "超时"

def analyze_transcription_result(result, config):
    """分析转录结果"""
    print("\n📋 转录结果分析:")
    
    # 处理时间
    if 'timing' in result:
        timing = result['timing']
        print(f"   ⏱️  处理时间: {timing.get('total_time', 'N/A')}s")
        print(f"   🎙️  转录时间: {timing.get('transcription_time', 'N/A')}s")
    
    # 实际使用的参数
    if 'transcription_params' in result:
        params = result['transcription_params']
        print(f"   📝 实际参数:")
        print(f"      模型: {params.get('model', 'N/A')}")
        print(f"      语言: {params.get('language', 'N/A')}")
        print(f"      任务: {params.get('task_type', 'N/A')}")
        print(f"      格式: {params.get('output_format', 'N/A')}")
    
    # 生成的文件
    if 'files' in result:
        files = result['files']
        print(f"   📄 生成文件: {len(files)} 个")
        for file_info in files:
            print(f"      - {file_info['filename']} ({file_info['type']})")
    
    # 转录内容
    if 'full_text' in result:
        text = result['full_text'].strip()
        if text:
            print(f"   💬 转录内容:")
            # 显示前200个字符
            preview = text[:200] + "..." if len(text) > 200 else text
            print(f"      {preview}")
            
            # 分析语言特征
            chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
            english_words = len([word for word in text.split() if word.isalpha()])
            
            print(f"   🔍 语言分析:")
            print(f"      中文字符数: {chinese_chars}")
            print(f"      英文单词数: {english_words}")
            
            if config['language'] == 'zh' and chinese_chars == 0:
                print("   ⚠️  警告: 指定中文但未检测到中文字符")
            elif config['language'] == 'auto':
                detected_lang = "中文" if chinese_chars > english_words else "英文"
                print(f"      自动检测结果: {detected_lang}")
                
        else:
            print("   ❌ 转录内容为空")

def print_final_summary(results):
    """打印最终测试总结"""
    print("\n" + "="*80)
    print("📊 中文音频转录测试总结报告")
    print("="*80)
    
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    print(f"\n📈 总体统计:")
    print(f"   测试配置数: {total_count}")
    print(f"   成功测试: {success_count}")
    print(f"   失败测试: {total_count - success_count}")
    print(f"   成功率: {success_count/total_count*100:.1f}%")
    
    print(f"\n🎯 详细结果:")
    for i, result in enumerate(results, 1):
        config = result['config']
        print(f"\n{i}. {config['name']}:")
        
        if result['success']:
            print(f"   ✅ 状态: 成功")
            print(f"   ⏱️  耗时: {result['total_time']:.1f}s")
            
            # 显示转录内容预览
            transcription_result = result.get('result', {})
            if 'full_text' in transcription_result:
                text = transcription_result['full_text'].strip()
                if text:
                    preview = text[:100] + "..." if len(text) > 100 else text
                    print(f"   💬 内容: {preview}")
                else:
                    print(f"   ⚠️  转录内容为空")
        else:
            print(f"   ❌ 状态: 失败")
            print(f"   🚨 错误: {result['error']}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    print("🎤 开始中文音频转录测试...")
    print(f"📅 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        results = test_chinese_audio()
        
        # 保存测试结果
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        result_file = f"chinese_transcription_test_{timestamp}.json"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 测试结果已保存到: {result_file}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n🚨 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
