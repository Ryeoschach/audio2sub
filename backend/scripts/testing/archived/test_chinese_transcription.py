#!/usr/bin/env python3
"""
中文语音转录测试脚本
"""
import requests
import time
import json

def test_chinese_transcription():
    """测试中文语音转录"""
    base_url = "http://localhost:8000"
    
    print("🎯 中文语音转录测试")
    print("=" * 40)
    
    # 1. 健康检查
    print("🔍 API 健康检查...")
    try:
        health = requests.get(f"{base_url}/health").json()
        print(f"✅ API 状态: {health['status']}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False
    
    # 2. 创建一个测试"音频"文件（模拟中文语音内容）
    # 注意：这仍然是文本，但我们会标记为音频格式
    chinese_content = """
    你好，这是一个中文语音转录测试。
    我们正在测试Audio2Sub的动态模型选择功能。
    今天是2025年6月19日，天气很好。
    希望这个测试能够正确识别中文语音。
    谢谢大家的关注和支持。
    """.strip()
    
    print(f"📁 准备中文测试内容 ({len(chinese_content)} 字符)")
    
    # 3. 测试配置
    test_configs = [
        {
            "name": "自动检测 + tiny模型",
            "model": "tiny",
            "language": "auto",
            "output_format": "srt"
        },
        {
            "name": "指定中文 + base模型", 
            "model": "base",
            "language": "zh",
            "output_format": "both"
        },
        {
            "name": "指定中文 + small模型",
            "model": "small", 
            "language": "zh",
            "output_format": "vtt"
        }
    ]
    
    results = []
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n{'='*20} 测试 {i}: {config['name']} {'='*20}")
        print(f"🔧 模型: {config['model']}")
        print(f"🌍 语言: {config['language']}")
        print(f"📄 输出: {config['output_format']}")
        
        try:
            # 上传文件（模拟中文音频）
            files = {
                'file': (f'chinese_test_{config["model"]}.wav', chinese_content.encode(), 'audio/wav')
            }
            data = {
                'model': config['model'],
                'language': config['language'],
                'output_format': config['output_format'],
                'task': 'transcribe'
            }
            
            print("🚀 上传中文音频...")
            upload_response = requests.post(f"{base_url}/upload/", files=files, data=data)
            
            if upload_response.status_code != 200:
                print(f"❌ 上传失败: {upload_response.status_code}")
                print(f"   错误: {upload_response.text}")
                continue
            
            upload_result = upload_response.json()
            task_id = upload_result['task_id']
            
            print(f"✅ 上传成功!")
            print(f"   任务ID: {task_id}")
            print(f"   使用模型: {upload_result.get('model_used', 'N/A')}")
            print(f"   预估时间: {upload_result.get('estimated_time', 'N/A')}秒")
            
            # 监控任务状态
            print("⏳ 监控转录进度...")
            success, result = monitor_transcription_task(base_url, task_id, max_wait=120)
            
            if success:
                print("✅ 转录完成!")
                
                # 分析转录结果
                analyze_transcription_result(result, config)
                
                results.append({
                    "config": config,
                    "success": True,
                    "result": result
                })
            else:
                print(f"❌ 转录失败: {result}")
                results.append({
                    "config": config,
                    "success": False,
                    "error": result
                })
                
        except Exception as e:
            print(f"🚨 测试出错: {e}")
            results.append({
                "config": config,
                "success": False,
                "error": str(e)
            })
        
        print("-" * 60)
    
    # 显示测试总结
    print_chinese_test_summary(results)
    
    return results

def monitor_transcription_task(base_url, task_id, max_wait=180):
    """监控转录任务"""
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{base_url}/status/{task_id}")
            if response.status_code == 200:
                status_data = response.json()
                state = status_data.get('state', 'UNKNOWN')
                
                print(f"   📊 状态: {state}")
                
                if state == 'SUCCESS':
                    return True, status_data.get('result', {})
                elif state == 'FAILURE':
                    error_msg = status_data.get('status', '未知错误')
                    return False, error_msg
                elif state == 'PROGRESS':
                    result = status_data.get('result', {})
                    if isinstance(result, dict) and 'status' in result:
                        print(f"   🔄 进度: {result['status']}")
                
                time.sleep(3)
            else:
                print(f"   ⚠️  状态查询失败: {response.status_code}")
                time.sleep(5)
                
        except Exception as e:
            print(f"   ❌ 状态查询错误: {e}")
            time.sleep(3)
    
    return False, "Timeout"

def analyze_transcription_result(result, config):
    """分析转录结果"""
    print("📊 转录结果分析:")
    
    # 检查转录参数
    if 'transcription_params' in result:
        params = result['transcription_params']
        print(f"   🔧 实际使用的参数:")
        print(f"      模型: {params.get('model', 'N/A')}")
        print(f"      语言: {params.get('language', 'N/A')}")
        print(f"      输出格式: {params.get('output_format', 'N/A')}")
        print(f"      任务类型: {params.get('task_type', 'N/A')}")
    
    # 检查处理时间
    if 'timing' in result:
        timing = result['timing']
        print(f"   ⏱️  处理时间:")
        print(f"      总时间: {timing.get('total_time', 'N/A')}s")
        print(f"      转录时间: {timing.get('transcription_time', 'N/A')}s")
    
    # 检查生成的文件
    if 'files' in result:
        files = result['files']
        print(f"   📄 生成文件: {len(files)} 个")
        for file_info in files:
            print(f"      - {file_info['filename']} ({file_info['type']})")
    
    # 检查转录文本
    if 'full_text' in result:
        text = result['full_text']
        if text:
            print(f"   💬 转录内容 ({len(text)} 字符):")
            print(f"      {text[:200]}{'...' if len(text) > 200 else ''}")
            
            # 分析语言
            analyze_transcription_language(text, config['language'])
        else:
            print("   ⚠️  转录内容为空")
    else:
        print("   ❌ 没有转录文本")

def analyze_transcription_language(text, expected_language):
    """分析转录结果的语言"""
    if not text:
        print("   🚨 语言分析: 无文本内容")
        return
    
    # 简单的语言检测
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    english_chars = sum(1 for char in text if char.isalpha() and ord(char) < 128)
    total_chars = len(text.replace(' ', '').replace('\n', ''))
    
    if total_chars == 0:
        print("   🚨 语言分析: 无有效字符")
        return
    
    chinese_ratio = chinese_chars / total_chars
    english_ratio = english_chars / total_chars
    
    print(f"   🔍 语言分析:")
    print(f"      中文字符: {chinese_chars} ({chinese_ratio:.1%})")
    print(f"      英文字符: {english_chars} ({english_ratio:.1%})")
    
    detected_language = "中文" if chinese_ratio > 0.3 else "英文" if english_ratio > 0.5 else "混合/其他"
    expected_language_name = {"zh": "中文", "en": "英文", "auto": "自动检测"}.get(expected_language, expected_language)
    
    print(f"   🎯 检测到的语言: {detected_language}")
    print(f"   ⚙️  期望的语言: {expected_language_name}")
    
    if expected_language == "zh" and chinese_ratio < 0.3:
        print("   ⚠️  警告: 期望中文但检测到的中文比例较低")
    elif expected_language == "en" and english_ratio < 0.5:
        print("   ⚠️  警告: 期望英文但检测到的英文比例较低")

def print_chinese_test_summary(results):
    """打印中文测试总结"""
    print("\n" + "="*80)
    print("📋 中文语音转录测试总结")
    print("="*80)
    
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    print(f"\n📈 测试统计:")
    print(f"   总测试数: {total_count}")
    print(f"   成功: {success_count}")
    print(f"   失败: {total_count - success_count}")
    print(f"   成功率: {success_count/total_count*100:.1f}%")
    
    # 显示每个测试的详细结果
    for i, result in enumerate(results, 1):
        config = result['config']
        print(f"\n🔹 测试 {i}: {config['name']}")
        
        if result['success']:
            print("   ✅ 状态: 成功")
            test_result = result['result']
            
            # 显示语言相关信息
            if 'transcription_params' in test_result:
                params = test_result['transcription_params']
                print(f"   🌍 语言设置: {config['language']} → 实际: {params.get('language', 'N/A')}")
            
            # 显示转录结果
            if 'full_text' in test_result and test_result['full_text']:
                text = test_result['full_text']
                chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
                english_chars = sum(1 for char in text if char.isalpha() and ord(char) < 128)
                
                print(f"   📝 转录结果: {len(text)} 字符")
                print(f"   🔍 语言比例: 中文 {chinese_chars}/{len(text)} ({chinese_chars/len(text)*100:.1f}%)")
                print(f"   📄 内容预览: {text[:100]}...")
            else:
                print("   ⚠️  转录结果为空")
        else:
            print("   ❌ 状态: 失败")
            print(f"   🚨 错误: {result['error']}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    print("🚀 开始中文语音转录测试...")
    print(f"📅 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        results = test_chinese_transcription()
        
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
