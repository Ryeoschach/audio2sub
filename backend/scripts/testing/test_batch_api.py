#!/usr/bin/env python3
"""
测试批量处理API功能的脚本
"""

import requests
import time
import json
from pathlib import Path
import io


class Audio2SubBatchTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def check_api_health(self):
        """检查API健康状态"""
        try:
            print("🔍 检查API健康状态...")
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ API状态: {health_data.get('status', 'unknown')}")
                return True
            else:
                print(f"❌ API健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 无法连接到API: {e}")
            return False
    
    def create_test_files(self):
        """创建多个测试音频文件"""
        test_files = []
        
        # 创建简单的测试内容
        test_contents = [
            "Hello, this is test audio file number one for batch transcription.",
            "This is the second test file with different content for testing batch processing.",
            "Third test file contains some sample text to verify batch transcription functionality.",
        ]
        
        for i, content in enumerate(test_contents, 1):
            file_data = io.BytesIO(content.encode('utf-8'))
            file_data.name = f"test_audio_{i}.mp3"
            test_files.append(('files', (file_data.name, file_data, 'audio/mpeg')))
        
        return test_files
    
    def test_batch_upload(self):
        """测试批量上传功能"""
        print("\n🚀 测试批量上传功能...")
        
        # 准备测试文件
        files = self.create_test_files()
        
        # 准备请求数据
        data = {
            'model': 'tiny',
            'language': 'auto',
            'output_format': 'both',
            'task': 'transcribe',
            'concurrent_limit': 2
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/batch-upload/",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                batch_id = result['batch_id']
                total_files = result['total_files']
                
                print(f"✅ 批量上传成功!")
                print(f"   批量任务ID: {batch_id}")
                print(f"   文件数量: {total_files}")
                print(f"   使用模型: {result['model_used']}")
                print(f"   预估总时间: {result['estimated_total_time']}秒")
                
                return batch_id
            else:
                print(f"❌ 批量上传失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 批量上传异常: {e}")
            return None
    
    def monitor_batch_progress(self, batch_id, max_wait_time=300):
        """监控批量任务进度"""
        print(f"\n⏳ 监控批量任务进度: {batch_id}")
        
        # 等待一下确保Redis状态已初始化
        print("   等待状态初始化...")
        time.sleep(2)
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = self.session.get(f"{self.base_url}/batch-status/{batch_id}")
                
                if response.status_code == 200:
                    status = response.json()
                    overall_status = status['overall_status']
                    progress = status['progress_percentage']
                    completed = status['completed_files']
                    failed = status['failed_files']
                    total = status['total_files']
                    
                    print(f"📊 状态: {overall_status} | 进度: {progress:.1f}% | 完成: {completed}/{total} | 失败: {failed}")
                    
                    # 显示各个文件的详细状态
                    for task in status['tasks']:
                        filename = task['filename']
                        task_status = task['status']
                        task_progress = task.get('progress', 0)
                        error = task.get('error')
                        
                        status_emoji = {
                            'PENDING': '⏳',
                            'PROGRESS': '🔄',
                            'SUCCESS': '✅',
                            'FAILURE': '❌'
                        }.get(task_status, '❓')
                        
                        if error:
                            print(f"   {status_emoji} {filename}: {task_status} - {error}")
                        else:
                            print(f"   {status_emoji} {filename}: {task_status} ({task_progress}%)")
                    
                    if overall_status in ['COMPLETED', 'FAILED', 'PARTIAL_SUCCESS']:
                        print(f"\n🏁 批量任务完成: {overall_status}")
                        return overall_status
                    
                elif response.status_code == 404:
                    print(f"❌ 批量任务未找到: {batch_id}")
                    return None
                
                else:
                    print(f"❌ 状态查询失败: {response.status_code}")
                
            except Exception as e:
                print(f"❌ 状态查询异常: {e}")
            
            time.sleep(5)  # 每5秒检查一次
        
        print(f"⏰ 监控超时 ({max_wait_time}秒)")
        return "TIMEOUT"
    
    def get_batch_results(self, batch_id):
        """获取批量任务结果"""
        print(f"\n📄 获取批量任务结果: {batch_id}")
        
        try:
            response = self.session.get(f"{self.base_url}/batch-result/{batch_id}")
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ 结果汇总:")
                print(f"   总文件数: {result['total_files']}")
                print(f"   成功文件: {result['successful_files']}")
                print(f"   失败文件: {result['failed_files']}")
                print(f"   总处理时间: {result['total_processing_time']:.2f}秒")
                
                if result['results']:
                    print(f"\n📋 成功文件详情:")
                    for i, file_result in enumerate(result['results'], 1):
                        filename = file_result.get('filename', f'File {i}')
                        full_text = file_result.get('full_text', '').strip()
                        timing = file_result.get('timing', {})
                        
                        print(f"   {i}. {filename}")
                        if timing:
                            print(f"      处理时间: {timing.get('total_time', 'N/A')}秒")
                        if full_text:
                            preview = full_text[:100] + "..." if len(full_text) > 100 else full_text
                            print(f"      转录内容: {preview}")
                
                if result['errors']:
                    print(f"\n❌ 失败文件详情:")
                    for i, error_info in enumerate(result['errors'], 1):
                        filename = error_info.get('filename', f'File {i}')
                        error = error_info.get('error', 'Unknown error')
                        print(f"   {i}. {filename}: {error}")
                
                return result
                
            elif response.status_code == 202:
                print("⏳ 批量任务仍在处理中，请稍后再试")
                return None
            
            elif response.status_code == 404:
                print(f"❌ 批量任务未找到: {batch_id}")
                return None
            
            else:
                print(f"❌ 获取结果失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 获取结果异常: {e}")
            return None
    
    def test_batch_cancel(self, batch_id):
        """测试取消批量任务"""
        print(f"\n🛑 测试取消批量任务: {batch_id}")
        
        try:
            response = self.session.delete(f"{self.base_url}/batch/{batch_id}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {result['message']}")
                return True
            else:
                print(f"❌ 取消任务失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 取消任务异常: {e}")
            return False
    
    def run_full_test(self):
        """运行完整的批量处理测试"""
        print("🧪 开始批量处理API测试")
        print("=" * 50)
        
        # 1. 健康检查
        if not self.check_api_health():
            print("❌ API不可用，测试终止")
            return False
        
        # 2. 批量上传
        batch_id = self.test_batch_upload()
        if not batch_id:
            print("❌ 批量上传失败，测试终止")
            return False
        
        # 3. 监控进度
        final_status = self.monitor_batch_progress(batch_id)
        if not final_status:
            print("❌ 进度监控失败")
            return False
        
        # 4. 获取结果
        if final_status in ['COMPLETED', 'PARTIAL_SUCCESS']:
            results = self.get_batch_results(batch_id)
            if results:
                print("\n✅ 批量处理测试完成!")
                return True
        
        print(f"\n⚠️ 批量处理测试完成，最终状态: {final_status}")
        return True


def main():
    """主函数"""
    print("🎵 Audio2Sub 批量处理API测试工具")
    
    # 创建测试器
    tester = Audio2SubBatchTester()
    
    # 运行测试
    success = tester.run_full_test()
    
    if success:
        print("\n🎉 测试完成!")
    else:
        print("\n💥 测试失败!")


if __name__ == "__main__":
    main()
