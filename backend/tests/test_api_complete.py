#!/usr/bin/env python3
"""
测试修复后的API端点
"""

import sys
import httpx
import asyncio
import time
from pathlib import Path

async def test_api_endpoint():
    """测试API端点完整流程"""
    
    print("=" * 60)
    print("🧪 测试修复后的API端点")
    print("=" * 60)
    
    # 测试音频文件
    audio_file = "/Users/creed/workspace/sourceCode/whisper.cpp/111.wav"
    
    if not Path(audio_file).exists():
        print(f"❌ 错误: 音频文件不存在: {audio_file}")
        return False
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            # 1. 测试健康检查
            print("🏥 测试健康检查...")
            health_response = await client.get("http://localhost:8000/health")
            if health_response.status_code == 200:
                print("✅ 健康检查通过")
            else:
                print(f"❌ 健康检查失败: {health_response.status_code}")
                return False
            
            # 2. 上传文件
            print("\n📤 上传音频文件...")
            with open(audio_file, "rb") as f:
                files = {"file": ("111.wav", f, "audio/wav")}
                upload_response = await client.post(
                    "http://localhost:8000/upload/",
                    files=files
                )
            
            if upload_response.status_code != 202:
                print(f"❌ 文件上传失败: {upload_response.status_code}")
                print(f"响应: {upload_response.text}")
                return False
            
            upload_data = upload_response.json()
            task_id = upload_data["task_id"]
            file_id = upload_data["file_id"]
            
            print(f"✅ 文件上传成功")
            print(f"   📋 任务ID: {task_id}")
            print(f"   🆔 文件ID: {file_id}")
            
            # 3. 轮询任务状态
            print("\n⏳ 轮询任务状态...")
            max_wait_time = 120  # 最多等待2分钟
            wait_time = 0
            poll_interval = 5  # 每5秒检查一次
            
            while wait_time < max_wait_time:
                status_response = await client.get(f"http://localhost:8000/status/{task_id}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    state = status_data["state"]
                    status_msg = status_data.get("status", "Unknown")
                    progress = status_data.get("progress", 0)
                    
                    print(f"   📊 状态: {state} - {status_msg} ({progress}%)")
                    
                    if state == "SUCCESS":
                        print("✅ 转录任务完成!")
                        result = status_data.get("result", {})
                        
                        print(f"📊 结果摘要:")
                        print(f"   - 状态: {result.get('status', 'Unknown')}")
                        print(f"   - SRT文件: {result.get('srt_path', 'N/A')}")
                        print(f"   - VTT文件: {result.get('vtt_path', 'N/A')}")
                        
                        # 显示时间统计
                        timing = result.get('timing', {})
                        if timing:
                            print(f"   ⏱️ 总时间: {timing.get('total_time_formatted', 'N/A')}")
                        
                        # 4. 下载生成的字幕文件
                        print("\n📥 下载生成的字幕文件...")
                        
                        srt_file = result.get("srt_path")
                        vtt_file = result.get("vtt_path")
                        
                        if srt_file:
                            srt_response = await client.get(f"http://localhost:8000/results/{file_id}/{srt_file}")
                            if srt_response.status_code == 200:
                                srt_content = srt_response.text
                                print(f"✅ SRT文件下载成功 ({len(srt_content)} 字符)")
                                print("📝 SRT内容预览:")
                                lines = srt_content.split('\n')[:6]
                                for line in lines:
                                    print(f"   {line}")
                                if len(lines) >= 6:
                                    print("   ...")
                            else:
                                print(f"❌ SRT文件下载失败: {srt_response.status_code}")
                        
                        if vtt_file:
                            vtt_response = await client.get(f"http://localhost:8000/results/{file_id}/{vtt_file}")
                            if vtt_response.status_code == 200:
                                vtt_content = vtt_response.text
                                print(f"\n✅ VTT文件下载成功 ({len(vtt_content)} 字符)")
                                print("📝 VTT内容预览:")
                                lines = vtt_content.split('\n')[:8]
                                for line in lines:
                                    print(f"   {line}")
                                if len(lines) >= 8:
                                    print("   ...")
                            else:
                                print(f"❌ VTT文件下载失败: {vtt_response.status_code}")
                        
                        return True
                        
                    elif state == "FAILURE":
                        print(f"❌ 任务失败: {status_msg}")
                        return False
                    
                    # 等待下次轮询
                    await asyncio.sleep(poll_interval)
                    wait_time += poll_interval
                else:
                    print(f"❌ 状态查询失败: {status_response.status_code}")
                    print(f"响应: {status_response.text}")
                    return False
            
            print(f"⏰ 任务超时 (等待了 {max_wait_time} 秒)")
            return False
            
        except Exception as e:
            print(f"❌ API测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

async def main():
    """主测试函数"""
    print(f"🐍 Python: {sys.executable}")
    
    success = await test_api_endpoint()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 API端点测试成功！字幕生成问题已修复！")
    else:
        print("❌ API端点测试失败")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
