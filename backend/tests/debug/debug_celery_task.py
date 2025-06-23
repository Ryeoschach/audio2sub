#!/usr/bin/env python3
"""
模拟实际的Celery任务执行，调试API调用时的问题
"""

import sys
import shutil
from pathlib import Path
import tempfile
import uuid

sys.path.insert(0, '.')

def simulate_api_upload_and_transcription():
    """模拟API上传和转录流程"""
    print("🔍 模拟API上传和转录流程")
    
    try:
        from app.tasks import create_transcription_task
        
        # 1. 模拟文件上传
        test_audio = "/Users/creed/workspace/sourceCode/whisper.cpp/111.wav"
        if not Path(test_audio).exists():
            print(f"❌ 测试音频文件不存在: {test_audio}")
            return False
        
        # 模拟文件上传到uploads目录
        file_id = str(uuid.uuid4())
        original_filename = "111.wav"
        
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # 复制文件到uploads目录
        uploaded_file_path = upload_dir / f"{file_id}.wav"
        shutil.copy2(test_audio, uploaded_file_path)
        
        print(f"📁 文件已上传到: {uploaded_file_path}")
        print(f"🆔 文件ID: {file_id}")
        print(f"📋 原始文件名: {original_filename}")
        
        # 2. 直接调用Celery任务函数 (不通过异步队列)
        print("\n🔄 直接调用Celery任务函数...")
        
        # 调用任务函数 - 不需要传递self参数，因为bind=True会自动传递
        result = create_transcription_task(str(uploaded_file_path), file_id, original_filename)
        
        print(f"\n📊 任务执行结果:")
        print(f"   - 类型: {type(result)}")
        if isinstance(result, dict):
            print(f"   - 键: {list(result.keys())}")
            print(f"   - 状态: {result.get('status', 'N/A')}")
            print(f"   - SRT文件: {result.get('srt_path', 'N/A')}")
            print(f"   - VTT文件: {result.get('vtt_path', 'N/A')}")
        
        # 3. 检查生成的结果文件
        results_dir = Path("results") / file_id
        if results_dir.exists():
            print(f"\n📁 检查结果目录: {results_dir}")
            files = list(results_dir.iterdir())
            
            for file in files:
                size = file.stat().st_size
                print(f"   - {file.name}: {size} 字节")
                
                if file.suffix in ['.srt', '.vtt'] and size > 0:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f"     内容预览: {content[:200]}...")
                elif size == 0:
                    print(f"     ⚠️ 文件为空")
        else:
            print(f"❌ 结果目录不存在: {results_dir}")
        
        # 清理上传的文件
        try:
            uploaded_file_path.unlink()
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ 模拟任务执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_celery_task_with_logging():
    """测试Celery任务并输出详细日志"""
    print("\n🔍 测试Celery任务执行过程")
    
    import logging
    
    # 设置详细日志
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()
    
    try:
        # 运行模拟任务
        success = simulate_api_upload_and_transcription()
        
        if success:
            print("\n✅ Celery任务模拟成功")
        else:
            print("\n❌ Celery任务模拟失败")
        
        return success
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_task_function_directly():
    """直接检查任务函数定义"""
    print("\n🔍 检查任务函数定义")
    
    try:
        from app.tasks import create_transcription_task
        
        # 检查函数属性
        print(f"📋 任务函数: {create_transcription_task}")
        print(f"   - 函数名: {create_transcription_task.__name__}")
        print(f"   - 模块: {create_transcription_task.__module__}")
        
        # 检查是否有Celery装饰器
        if hasattr(create_transcription_task, 'delay'):
            print("✅ 函数有Celery装饰器")
            print(f"   - 任务名: {create_transcription_task.name}")
        else:
            print("⚠️ 函数没有Celery装饰器")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🎯 模拟API调用的Celery任务调试")
    print("=" * 60)
    print(f"🐍 Python: {sys.executable}")
    
    # 1. 检查任务函数定义
    check_success = check_task_function_directly()
    
    # 2. 测试任务执行
    task_success = test_celery_task_with_logging()
    
    print("\n" + "=" * 60)
    print("📊 调试结果:")
    print(f"   - 任务函数检查: {'✅' if check_success else '❌'}")
    print(f"   - 任务执行测试: {'✅' if task_success else '❌'}")
    
    if check_success and task_success:
        print("\n🎉 Celery任务执行正常！")
        return True
    else:
        print("\n❌ Celery任务执行存在问题")
        return False

if __name__ == "__main__":
    main()
