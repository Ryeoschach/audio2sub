#!/usr/bin/env python3
"""
最简化的faster-whisper测试
测试不同配置来找到稳定的运行方式
"""
import sys
import time
import warnings
from pathlib import Path

# 抑制资源泄漏警告
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

sys.path.append(str(Path(__file__).parent.parent))

def test_basic():
    """基础测试"""
    print("=== 最简化 faster-whisper 测试 ===")
    
    from config import TEST_AUDIO_PATH
    
    if not TEST_AUDIO_PATH.exists():
        print(f"❌ 音频文件不存在: {TEST_AUDIO_PATH}")
        return
    
    print(f"✅ 音频文件: {TEST_AUDIO_PATH}")
    
    try:
        from faster_whisper import WhisperModel
        
        # 尝试不同的配置（优化顺序，最稳定的在前）
        configs = [
            {"compute_type": "float32", "device": "cpu", "num_workers": 1},  # 最稳定
            {"compute_type": "int8", "device": "cpu", "num_workers": 1},     # 次选
            {"compute_type": "float16", "device": "cpu", "num_workers": 1},  # 备选
        ]
        
        for i, config in enumerate(configs, 1):
            print(f"\n--- 配置 {i}: {config} ---")
            try:
                # 限制工作线程数避免资源泄漏
                model = WhisperModel("base", **config)
                print(f"✅ 模型加载成功")
                
                # 简单转录测试（限制处理时长）
                print("开始转录测试...")
                start_time = time.time()
                
                segments, info = model.transcribe(
                    str(TEST_AUDIO_PATH),
                    language="zh",
                    # 使用最简单的参数避免资源问题
                    vad_filter=False,
                    word_timestamps=False,
                    # 限制处理长度
                    condition_on_previous_text=False
                )
                
                # 只收集前几个分段，避免长时间迭代
                first_segments = []
                segment_count = 0
                for segment in segments:
                    if segment_count >= 3:  # 只要前3个分段
                        break
                    first_segments.append(segment)
                    segment_count += 1
                
                total_time = time.time() - start_time
                
                print(f"✅ 转录成功！耗时: {total_time:.2f}秒")
                print(f"📊 音频时长: {info.duration:.2f}秒")
                print(f"🈳 检测语言: {info.language}")
                print(f"📝 前{len(first_segments)}段:")
                
                for k, segment in enumerate(first_segments, 1):
                    print(f"  {k}. [{segment.start:.1f}s-{segment.end:.1f}s] {segment.text}")
                
                print(f"🎉 配置 {i} 测试成功！")
                
                # 显式清理资源
                del model
                import gc
                gc.collect()
                
                return  # 找到一个成功的配置就退出
                
            except Exception as e:
                print(f"❌ 配置 {i} 失败: {e}")
                continue
        
        print("❌ 所有配置都失败了")
        
    except Exception as e:
        print(f"❌ 导入或初始化失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic()
