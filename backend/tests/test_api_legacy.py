#!/usr/bin/env python3
"""
Audio2Sub Backend API端到端测试
测试完整的文件上传→转录→字幕生成流程
"""

import sys
import os
import time
import httpx
import asyncio
from pathlib import Path
import json

# 确保使用当前目录的模块
sys.path.insert(0, '.')

async def test_complete_api_workflow():
    """测试完整的API工作流程"""
    print("🚀 开始API端到端测试")
    
    # 测试音频文件路径
    test_audio_path = "/Users/creed/workspace/sourceCode/whisper.cpp/111.wav"
    if not Path(test_audio_path).exists():
        print(f"❌ 测试音频文件不存在: {test_audio_path}")
        return False
    
    # 启动FastAPI服务器
    print("🔄 启动FastAPI服务器...")
    
    import subprocess
    import signal
    
    # 启动服务器进程
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 等待服务器启动
    print("⏳ 等待服务器启动...")
    await asyncio.sleep(3)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 1. 测试健康检查
            print("🔸 步骤1: 健康检查")
            health_response = await client.get("http://localhost:8000/health")
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"✅ 服务器健康状态: {health_data['status']}")
                print(f"🎙️ Whisper.cpp: {health_data['whisper_cpp']}")
                print(f"📡 Redis: {health_data['redis']}")
            else:
                print(f"❌ 健康检查失败: {health_response.status_code}")
                return False
            
            # 2. 上传文件并开始转录
            print("🔸 步骤2: 上传音频文件")
            with open(test_audio_path, "rb") as audio_file:
                files = {"file": ("test_audio.wav", audio_file, "audio/wav")}
                upload_response = await client.post("http://localhost:8000/upload/", files=files)
            
            if upload_response.status_code == 202:
                upload_data = upload_response.json()
                task_id = upload_data["task_id"]
                file_id = upload_data["file_id"]
                print(f"✅ 文件上传成功")
                print(f"📋 任务ID: {task_id}")
                print(f"📁 文件ID: {file_id}")
            else:
                print(f"❌ 文件上传失败: {upload_response.status_code}")
                print(f"错误内容: {upload_response.text}")
                return False
            
            # 3. 轮询任务状态
            print("🔸 步骤3: 轮询任务状态")
            max_wait_time = 180  # 最多等待3分钟
            wait_time = 0
            poll_interval = 5  # 每5秒检查一次
            
            while wait_time < max_wait_time:
                status_response = await client.get(f"http://localhost:8000/status/{task_id}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    state = status_data["state"]
                    status_msg = status_data["status"]
                    
                    print(f"⏳ 任务状态: {state} - {status_msg}")
                    
                    if state == "SUCCESS":
                        print("✅ 转录任务完成!")
                        result = status_data.get("result", {})
                        
                        # 显示转录结果摘要
                        transcription_text = result.get("transcription", {}).get("text", "")
                        segments_count = len(result.get("transcription", {}).get("segments", []))
                        
                        print(f"📝 转录文本长度: {len(transcription_text)}")
                        print(f"📊 段落数量: {segments_count}")
                        
                        if transcription_text:
                            preview = transcription_text[:200] + "..." if len(transcription_text) > 200 else transcription_text
                            print(f"📄 转录预览: {preview}")
                        
                        # 检查生成的文件
                        srt_file = result.get("srt_file")
                        vtt_file = result.get("vtt_file")
                        
                        if srt_file:
                            print(f"📄 SRT字幕文件: {srt_file}")
                        if vtt_file:
                            print(f"📄 VTT字幕文件: {vtt_file}")
                        
                        break
                        
                    elif state == "FAILURE":
                        print(f"❌ 任务失败: {status_msg}")
                        return False
                        
                    elif state in ["PENDING", "PROGRESS"]:
                        # 继续等待
                        await asyncio.sleep(poll_interval)
                        wait_time += poll_interval
                    else:
                        print(f"🔄 未知状态: {state}")
                        await asyncio.sleep(poll_interval)
                        wait_time += poll_interval
                else:
                    print(f"❌ 状态查询失败: {status_response.status_code}")
                    return False
            
            if wait_time >= max_wait_time:
                print("⏰ 任务超时")
                return False
            
            # 4. 下载结果文件 (可选)
            print("🔸 步骤4: 验证结果文件")
            
            if srt_file:
                try:
                    srt_response = await client.get(f"http://localhost:8000/results/{file_id}/{Path(srt_file).name}")
                    if srt_response.status_code == 200:
                        srt_content = srt_response.text
                        print(f"✅ SRT文件下载成功: {len(srt_content)} 字符")
                        
                        # 显示前几行
                        lines = srt_content.split('\n')[:10]
                        print("📄 SRT文件前10行:")
                        for i, line in enumerate(lines):
                            print(f"   {i+1}: {line}")
                    else:
                        print(f"⚠️ SRT文件下载失败: {srt_response.status_code}")
                except Exception as e:
                    print(f"⚠️ SRT文件下载异常: {e}")
            
            print("🎉 API端到端测试完成!")
            return True
            
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 关闭服务器
        print("🔄 关闭测试服务器...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
            server_process.wait()

async def main():
    """主测试函数"""
    print("🎯 Audio2Sub Backend API端到端测试")
    print("=" * 50)
    
    success = await test_complete_api_workflow()
    
    if success:
        print("\n🎉 所有API测试通过！系统完整功能正常。")
        return 0
    else:
        print("\n❌ API测试失败，请检查系统配置。")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
