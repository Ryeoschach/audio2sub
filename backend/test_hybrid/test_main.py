#!/usr/bin/env python3
"""
主测试脚本
执行混合Whisper架构测试，对比不同实现的效果
"""
import sys
import time
from pathlib import Path

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from config import TEST_AUDIO_PATH, OUTPUT_DIR, get_device_config
from hybrid_whisper import HybridWhisperProcessor, optimize_segments_for_subtitles
from subtitle_export import export_subtitle_comparison, create_analysis_report

def main():
    """主测试函数"""
    print("=== Whisper 混合架构测试开始 ===")
    
    # 检查设备配置
    device_config = get_device_config()
    print(f"\n设备配置:")
    for key, value in device_config.items():
        print(f"  {key}: {value}")
    
    # 检查测试音频文件
    if not TEST_AUDIO_PATH.exists():
        print(f"\n❌ 测试音频文件不存在: {TEST_AUDIO_PATH}")
        print("请确保文件路径正确，或修改config.py中的TEST_AUDIO_PATH")
        return
    
    print(f"\n✅ 测试音频文件: {TEST_AUDIO_PATH}")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    
    # 初始化混合处理器
    print(f"\n--- 初始化混合Whisper处理器 ---")
    processor = HybridWhisperProcessor()
    
    if not processor.use_transformers and not processor.use_faster_whisper:
        print("❌ 没有可用的Whisper模型")
        return
    
    # 执行转录
    print(f"\n--- 开始音频转录 ---")
    start_time = time.time()
    
    results = processor.process_audio(str(TEST_AUDIO_PATH))
    
    total_time = time.time() - start_time
    print(f"\n⏱️ 总处理时间: {total_time:.2f}秒")
    
    # 打印结果摘要
    print(f"\n--- 结果摘要 ---")
    for method_name, segments in results.items():
        if segments:
            print(f"{method_name.title()}:")
            print(f"  - 分段数量: {len(segments)}")
            print(f"  - 总文本长度: {sum(len(seg.text) for seg in segments)} 字符")
            if segments:
                total_duration = max(seg.end for seg in segments)
                print(f"  - 音频时长: {total_duration:.2f}秒")
            print(f"  - 前3段内容:")
            for i, seg in enumerate(segments[:3], 1):
                print(f"    {i}. [{seg.start:.1f}s-{seg.end:.1f}s] {seg.text}")
        else:
            print(f"{method_name.title()}: 无结果")
    
    # 优化faster-whisper结果
    if "faster_whisper" in results and results["faster_whisper"]:
        print(f"\n--- 优化字幕分段 ---")
        optimized = optimize_segments_for_subtitles(results["faster_whisper"])
        results["faster_whisper_optimized"] = optimized
        print(f"原始分段: {len(results['faster_whisper'])}")
        print(f"优化分段: {len(optimized)}")
    
    # 导出结果
    print(f"\n--- 导出字幕文件 ---")
    export_subtitle_comparison(results, OUTPUT_DIR)
    
    # 生成分析报告
    print(f"\n--- 生成分析报告 ---")
    create_analysis_report(results, OUTPUT_DIR / "analysis_report.md")
    
    print(f"\n✅ 测试完成！结果已保存到: {OUTPUT_DIR}")
    print(f"📊 查看分析报告: {OUTPUT_DIR / 'analysis_report.md'}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
