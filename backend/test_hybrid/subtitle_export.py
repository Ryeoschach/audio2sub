"""
字幕格式输出模块
支持SRT和WebVTT格式
"""
import math
from typing import List
from pathlib import Path
from dataclasses import dataclass

from hybrid_whisper import TranscriptionSegment

def format_time_srt(seconds: float) -> str:
    """格式化时间为SRT格式 (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def format_time_vtt(seconds: float) -> str:
    """格式化时间为WebVTT格式 (HH:MM:SS.mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"

def export_to_srt(segments: List[TranscriptionSegment], output_path: Path) -> None:
    """导出为SRT格式"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments, 1):
            f.write(f"{i}\n")
            f.write(f"{format_time_srt(segment.start)} --> {format_time_srt(segment.end)}\n")
            f.write(f"{segment.text}\n\n")
    
    print(f"SRT file exported to: {output_path}")

def export_to_vtt(segments: List[TranscriptionSegment], output_path: Path) -> None:
    """导出为WebVTT格式"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")
        
        for segment in segments:
            f.write(f"{format_time_vtt(segment.start)} --> {format_time_vtt(segment.end)}\n")
            f.write(f"{segment.text}\n\n")
    
    print(f"WebVTT file exported to: {output_path}")

def export_to_txt(segments: List[TranscriptionSegment], output_path: Path) -> None:
    """导出为纯文本格式"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for segment in segments:
            f.write(f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}\n")
    
    print(f"Text file exported to: {output_path}")

def export_subtitle_comparison(results: dict, output_dir: Path) -> None:
    """导出不同方法的字幕对比"""
    for method_name, segments in results.items():
        if not segments:
            continue
        
        method_dir = output_dir / method_name
        method_dir.mkdir(exist_ok=True)
        
        # 导出原始segments
        export_to_srt(segments, method_dir / f"raw_{method_name}.srt")
        export_to_vtt(segments, method_dir / f"raw_{method_name}.vtt")
        export_to_txt(segments, method_dir / f"raw_{method_name}.txt")
        
        # 如果有优化的segments
        if method_name == "faster_whisper":
            from hybrid_whisper import optimize_segments_for_subtitles
            optimized_segments = optimize_segments_for_subtitles(segments)
            
            export_to_srt(optimized_segments, method_dir / f"optimized_{method_name}.srt")
            export_to_vtt(optimized_segments, method_dir / f"optimized_{method_name}.vtt")
            export_to_txt(optimized_segments, method_dir / f"optimized_{method_name}.txt")
        
        print(f"Exported {method_name} results to {method_dir}")

def create_analysis_report(results: dict, output_path: Path) -> None:
    """创建分析报告"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Whisper 混合架构测试报告\n\n")
        f.write(f"生成时间: {Path(__file__).stat().st_mtime}\n\n")
        
        for method_name, segments in results.items():
            if not segments:
                f.write(f"## {method_name.title()}\n")
                f.write("未生成结果\n\n")
                continue
            
            f.write(f"## {method_name.title()}\n")
            f.write(f"- 分段数量: {len(segments)}\n")
            
            total_duration = max(seg.end for seg in segments) if segments else 0
            f.write(f"- 总时长: {total_duration:.2f}秒\n")
            
            avg_segment_duration = sum(seg.duration for seg in segments) / len(segments) if segments else 0
            f.write(f"- 平均分段时长: {avg_segment_duration:.2f}秒\n")
            
            total_chars = sum(len(seg.text) for seg in segments)
            f.write(f"- 总字符数: {total_chars}\n")
            
            avg_chars_per_segment = total_chars / len(segments) if segments else 0
            f.write(f"- 平均每段字符数: {avg_chars_per_segment:.1f}\n")
            
            # 置信度信息（如果可用）
            confidences = [seg.confidence for seg in segments if seg.confidence is not None]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                f.write(f"- 平均置信度: {avg_confidence:.3f}\n")
            
            f.write(f"\n### 前5个分段示例:\n")
            for i, segment in enumerate(segments[:5], 1):
                f.write(f"{i}. [{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}\n")
            
            f.write("\n")
        
        # 对比分析
        if len(results) > 1:
            f.write("## 对比分析\n")
            methods = list(results.keys())
            
            for i, method1 in enumerate(methods):
                for method2 in methods[i+1:]:
                    segments1 = results[method1]
                    segments2 = results[method2]
                    
                    if not segments1 or not segments2:
                        continue
                    
                    f.write(f"\n### {method1.title()} vs {method2.title()}\n")
                    f.write(f"- 分段数量: {len(segments1)} vs {len(segments2)}\n")
                    
                    text1 = " ".join(seg.text for seg in segments1)
                    text2 = " ".join(seg.text for seg in segments2)
                    f.write(f"- 文本长度: {len(text1)} vs {len(text2)} 字符\n")
    
    print(f"Analysis report created: {output_path}")

if __name__ == "__main__":
    # 测试格式化功能
    test_segments = [
        TranscriptionSegment(0.0, 3.5, "这是一个测试字幕", 0.95),
        TranscriptionSegment(3.5, 7.2, "用于验证格式化功能", 0.92),
    ]
    
    from config import OUTPUT_DIR
    export_to_srt(test_segments, OUTPUT_DIR / "test.srt")
    export_to_vtt(test_segments, OUTPUT_DIR / "test.vtt")
    export_to_txt(test_segments, OUTPUT_DIR / "test.txt")
