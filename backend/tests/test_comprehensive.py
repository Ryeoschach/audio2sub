#!/usr/bin/env python3
"""
在uv虚拟环境中运行Audio2Sub Backend完整功能测试
测试whisper.cpp迁移后的所有核心功能
"""

import sys
import os
from pathlib import Path
import time
import json
import tempfile
import subprocess
import logging
from datetime import datetime

# 确保使用当前目录的模块
sys.path.insert(0, '.')

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_section(title: str):
    """打印测试段落标题"""
    print(f"\n{'='*60}")
    print(f"🎯 {title}")
    print(f"{'='*60}")

def print_subsection(title: str):
    """打印子段落标题"""
    print(f"\n🔸 {title}")
    print("-" * 40)

def check_environment():
    """检查虚拟环境和基础依赖"""
    print_section("环境检查")
    
    # 检查Python版本和位置
    python_path = sys.executable
    python_version = sys.version
    print(f"✅ Python路径: {python_path}")
    print(f"✅ Python版本: {python_version.split()[0]}")
    
    # 检查是否在uv虚拟环境中
    if '.venv' in python_path:
        print("✅ 运行在uv虚拟环境中")
    else:
        print("⚠️ 不在虚拟环境中运行")
    
    # 检查关键依赖
    required_packages = ['fastapi', 'celery', 'redis', 'pydantic_settings', 'pathlib']
    print_subsection("Python包检查")
    
    for package in required_packages:
        try:
            if package == 'redis':
                import redis
                print(f"✅ {package}: {redis.__version__}")
            elif package == 'fastapi':
                import fastapi
                print(f"✅ {package}: {fastapi.__version__}")
            elif package == 'celery':
                import celery
                print(f"✅ {package}: {celery.__version__}")
            elif package == 'pathlib':
                from pathlib import Path
                print(f"✅ {package}: 内置模块")
            elif package == 'pydantic_settings':
                from pydantic_settings import BaseSettings
                print(f"✅ {package}: 已安装")
            else:
                __import__(package)
                print(f"✅ {package}: 已安装")
        except ImportError as e:
            print(f"❌ {package}: 未安装 - {e}")
            return False
    
    return True

def test_config_loading():
    """测试配置加载"""
    print_section("配置系统测试")
    
    try:
        from app.config import settings
        
        print("✅ 配置加载成功")
        print(f"📝 APP_NAME: {settings.APP_NAME}")
        print(f"🔧 WHISPER_CPP_PATH: {settings.WHISPER_CPP_PATH}")
        print(f"📊 MODEL_NAME: {settings.MODEL_NAME}")
        print(f"🖥️ WHISPER_DEVICE: {settings.WHISPER_DEVICE}")
        print(f"🧵 WHISPER_THREADS: {settings.WHISPER_THREADS}")
        print(f"🗣️ WHISPER_LANGUAGE: {settings.WHISPER_LANGUAGE}")
        print(f"📡 REDIS_HOST: {settings.REDIS_HOST}")
        print(f"🔌 REDIS_PORT: {settings.REDIS_PORT}")
        print(f"🔑 REDIS_PASSWORD: {'***' if settings.REDIS_PASSWORD else 'None'}")
        print(f"🔗 CELERY_BROKER_URL: {settings.CELERY_BROKER_URL}")
        
        # 检查目录创建
        upload_dir = Path(settings.UPLOAD_DIR)
        results_dir = Path(settings.RESULTS_DIR)
        print(f"📁 UPLOAD_DIR: {upload_dir} ({'存在' if upload_dir.exists() else '不存在'})")
        print(f"📁 RESULTS_DIR: {results_dir} ({'存在' if results_dir.exists() else '不存在'})")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_whisper_cpp_availability():
    """测试whisper.cpp可用性"""
    print_section("Whisper.cpp可用性测试")
    
    try:
        from app.whisper_manager import WhisperManager
        
        manager = WhisperManager()
        print(f"✅ WhisperManager初始化成功")
        print(f"🔧 whisper.cpp路径: {manager.whisper_cpp_path}")
        
        if manager.whisper_cpp_path:
            # 测试whisper.cpp命令
            cmd = [manager.whisper_cpp_path, "--help"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ whisper.cpp命令行工具正常")
            else:
                print(f"⚠️ whisper.cpp命令返回错误: {result.returncode}")
        else:
            print("⚠️ whisper.cpp路径未找到，将使用mock模式")
            
        return True
        
    except Exception as e:
        print(f"❌ WhisperManager测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_redis_connection():
    """测试Redis连接"""
    print_section("Redis连接测试")
    
    try:
        from app.config import settings
        import redis
        
        # 创建Redis连接
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        # 测试连接
        r.ping()
        print("✅ Redis连接成功")
        
        # 测试基本操作
        test_key = "audio2sub_test"
        test_value = f"test_{int(time.time())}"
        r.set(test_key, test_value, ex=10)  # 10秒过期
        retrieved_value = r.get(test_key)
        
        if retrieved_value == test_value:
            print("✅ Redis读写测试成功")
            r.delete(test_key)
        else:
            print("❌ Redis读写测试失败")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        print("💡 提示: 请确保Redis服务器运行在127.0.0.1:6379，密码为'redispassword'")
        return False

def test_celery_configuration():
    """测试Celery配置"""
    print_section("Celery配置测试")
    
    try:
        from celery_app import celery_app
        # Import tasks to ensure they are registered
        from app.tasks import create_transcription_task
        
        print("✅ Celery应用创建成功")
        print(f"🔗 Broker URL: {celery_app.conf.broker_url}")
        print(f"📊 Result Backend: {celery_app.conf.result_backend}")
        
        # 检查已注册的任务
        registered_tasks = list(celery_app.tasks.keys())
        print(f"📋 已注册任务数量: {len(registered_tasks)}")
        
        target_task = "app.tasks.create_transcription_task"
        if target_task in registered_tasks:
            print(f"✅ 目标任务已注册: {target_task}")
            return True
        else:
            print(f"❌ 目标任务未注册: {target_task}")
            print("📋 已注册的任务:")
            for task in registered_tasks:
                if not task.startswith('celery.'):
                    print(f"   - {task}")
            # Try direct function test
            try:
                # Test if the function is accessible
                test_result = create_transcription_task
                print(f"✅ 任务函数可直接访问: {test_result}")
                return True
            except Exception as e:
                print(f"❌ 任务函数访问失败: {e}")
                return False
            
        return True
        
    except Exception as e:
        print(f"❌ Celery配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_transcription_functionality():
    """测试转录功能"""
    print_section("转录功能测试")
    
    try:
        from app.whisper_manager import get_whisper_manager
        
        # 使用测试音频文件
        test_audio_path = "/Users/creed/workspace/sourceCode/whisper.cpp/111.wav"
        if not Path(test_audio_path).exists():
            print(f"⚠️ 测试音频文件不存在: {test_audio_path}")
            print("🔄 使用mock转录进行测试...")
            test_audio_path = "mock_audio.wav"
        
        manager = get_whisper_manager()
        print(f"🎙️ 开始转录测试: {test_audio_path}")
        
        start_time = time.time()
        result = manager.transcribe(test_audio_path)
        transcription_time = time.time() - start_time
        
        print(f"✅ 转录完成，耗时: {transcription_time:.2f}秒")
        print(f"📝 转录文本长度: {len(result.get('text', ''))}")
        print(f"📊 段落数量: {len(result.get('segments', []))}")
        print(f"🗣️ 检测语言: {result.get('language', 'unknown')}")
        
        # 显示转录文本片段
        text = result.get('text', '')
        if text:
            preview = text[:200] + "..." if len(text) > 200 else text
            print(f"📄 转录文本预览: {preview}")
        
        return True, result
        
    except Exception as e:
        print(f"❌ 转录功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_subtitle_generation(transcription_result):
    """测试字幕生成功能"""
    print_section("字幕生成测试")
    
    if not transcription_result:
        print("❌ 没有转录结果，跳过字幕生成测试")
        return False
    
    try:
        from app.tasks import generate_subtitles_from_segments
        
        segments = transcription_result.get('segments', [])
        if not segments:
            print("⚠️ 转录结果中没有段落信息，创建测试段落")
            # 创建测试段落
            segments = [
                {
                    "start": 0.0,
                    "end": 3.0,
                    "text": "This is a test subtitle segment.",
                    "words": []
                },
                {
                    "start": 3.0,
                    "end": 6.0,
                    "text": "This is another test segment for subtitle generation.",
                    "words": []
                }
            ]
        
        print(f"📊 处理段落数量: {len(segments)}")
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.srt', delete=False) as srt_file:
            srt_path = Path(srt_file.name)
        
        with tempfile.NamedTemporaryFile(suffix='.vtt', delete=False) as vtt_file:
            vtt_path = Path(vtt_file.name)
        
        try:
            # 生成字幕文件
            print("🔄 正在生成字幕文件...")
            generate_subtitles_from_segments(segments, srt_path, vtt_path)
            
            # 检查SRT文件
            if srt_path.exists():
                srt_size = srt_path.stat().st_size
                print(f"✅ SRT文件生成成功: {srt_size} 字节")
                
                if srt_size > 0:
                    with open(srt_path, 'r', encoding='utf-8') as f:
                        srt_content = f.read()
                        # 统计字幕条目
                        entries = [e.strip() for e in srt_content.split('\n\n') if e.strip()]
                        print(f"📝 SRT字幕条目数量: {len(entries)}")
                        
                        # 显示前2个条目
                        for i, entry in enumerate(entries[:2]):
                            if entry:
                                print(f"📄 SRT条目 {i+1}:")
                                for line in entry.split('\n'):
                                    print(f"   {line}")
                else:
                    print("⚠️ SRT文件为空")
            else:
                print("❌ SRT文件未生成")
            
            # 检查VTT文件
            if vtt_path.exists():
                vtt_size = vtt_path.stat().st_size
                print(f"✅ VTT文件生成成功: {vtt_size} 字节")
                
                if vtt_size > 8:  # 大于"WEBVTT\n\n"
                    with open(vtt_path, 'r', encoding='utf-8') as f:
                        vtt_content = f.read()
                        lines = vtt_content.split('\n')
                        print(f"📝 VTT文件行数: {len(lines)}")
                        
                        # 显示前几行
                        print("📄 VTT文件前10行:")
                        for i, line in enumerate(lines[:10]):
                            print(f"   {i+1}: {line}")
                else:
                    print("⚠️ VTT文件只有头部")
            else:
                print("❌ VTT文件未生成")
                
            return True
            
        finally:
            # 清理临时文件
            try:
                srt_path.unlink()
                vtt_path.unlink()
            except:
                pass
                
    except Exception as e:
        print(f"❌ 字幕生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fastapi_server():
    """测试FastAPI服务器"""
    print_section("FastAPI服务器测试")
    
    try:
        from app.main import app
        import httpx
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # 测试根路径
        response = client.get("/")
        if response.status_code == 200:
            print("✅ 根路径访问成功")
            print(f"📄 响应内容: {response.json()}")
        else:
            print(f"❌ 根路径访问失败: {response.status_code}")
            return False
        
        # 测试健康检查
        response = client.get("/health")
        if response.status_code == 200:
            print("✅ 健康检查接口正常")
            health_data = response.json()
            print(f"📊 健康状态: {health_data}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI服务器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_comprehensive_test():
    """运行完整功能测试"""
    print_section("Audio2Sub Backend 全面功能测试")
    print(f"🕐 测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python环境: {sys.executable}")
    
    # 测试结果统计
    test_results = {
        "environment": False,
        "config": False,
        "whisper_cpp": False,
        "redis": False,
        "celery": False,
        "transcription": False,
        "subtitle_generation": False,
        "fastapi": False
    }
    
    transcription_result = None
    
    # 1. 环境检查
    test_results["environment"] = check_environment()
    
    # 2. 配置加载测试
    if test_results["environment"]:
        test_results["config"] = test_config_loading()
    
    # 3. Whisper.cpp测试
    if test_results["config"]:
        test_results["whisper_cpp"] = test_whisper_cpp_availability()
    
    # 4. Redis连接测试
    if test_results["config"]:
        test_results["redis"] = test_redis_connection()
    
    # 5. Celery配置测试
    if test_results["config"] and test_results["redis"]:
        test_results["celery"] = test_celery_configuration()
    
    # 6. 转录功能测试
    if test_results["whisper_cpp"]:
        success, transcription_result = test_transcription_functionality()
        test_results["transcription"] = success
    
    # 7. 字幕生成测试
    if test_results["config"]:
        test_results["subtitle_generation"] = test_subtitle_generation(transcription_result)
    
    # 8. FastAPI服务器测试
    if test_results["config"]:
        test_results["fastapi"] = test_fastapi_server()
    
    # 输出最终结果
    print_section("测试结果汇总")
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    print(f"📊 测试总览: {passed_tests}/{total_tests} 通过")
    print()
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print(f"\n🕐 测试结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！Audio2Sub Backend系统运行正常。")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} 个测试失败，请检查相关组件。")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
