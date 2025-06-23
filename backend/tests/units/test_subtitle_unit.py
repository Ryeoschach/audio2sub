#!/usr/bin/env python3
"""
最简单的字幕生成测试
"""
import sys
from pathlib import Path

# 确保使用当前目录的模块
sys.path.insert(0, '.')

def simple_test():
    print("🔍 最简单的字幕生成测试")
    print("=" * 50)
    
    try:
        # 测试导入
        print("1. 测试模块导入...")
        from app.tasks import generate_subtitles_from_segments
        print("   ✅ 成功导入 generate_subtitles_from_segments")
        
        # 创建最简单的测试数据
        print("\n2. 创建测试数据...")
        test_segments = [
            {
                "start": 0.0,
                "end": 3.0,
                "text": "Hello world"
            },
            {
                "start": 3.0,
                "end": 6.0,
                "text": "This is a test"
            }
        ]
        print(f"   ✅ 创建了 {len(test_segments)} 个测试段落")
        
        # 创建输出文件路径
        print("\n3. 创建输出文件...")
        srt_path = Path("test_output.srt")
        vtt_path = Path("test_output.vtt")
        print(f"   SRT文件: {srt_path}")
        print(f"   VTT文件: {vtt_path}")
        
        # 调用字幕生成函数
        print("\n4. 生成字幕...")
        generate_subtitles_from_segments(test_segments, srt_path, vtt_path)
        print("   ✅ 字幕生成函数调用完成")
        
        # 检查结果
        print("\n5. 检查生成结果...")
        
        if srt_path.exists():
            srt_size = srt_path.stat().st_size
            print(f"   SRT文件存在: {srt_size} 字节")
            
            if srt_size > 0:
                with open(srt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print("   SRT内容:")
                    print("   " + "-" * 30)
                    print(content)
                    print("   " + "-" * 30)
            else:
                print("   ⚠️ SRT文件为空")
        else:
            print("   ❌ SRT文件不存在")
        
        if vtt_path.exists():
            vtt_size = vtt_path.stat().st_size
            print(f"   VTT文件存在: {vtt_size} 字节")
            
            if vtt_size > 0:
                with open(vtt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print("   VTT内容:")
                    print("   " + "-" * 30)
                    print(content)
                    print("   " + "-" * 30)
            else:
                print("   ⚠️ VTT文件为空或只有头部")
        else:
            print("   ❌ VTT文件不存在")
        
        # 清理
        print("\n6. 清理测试文件...")
        try:
            if srt_path.exists():
                srt_path.unlink()
                print("   ✅ SRT测试文件已删除")
            if vtt_path.exists():
                vtt_path.unlink()
                print("   ✅ VTT测试文件已删除")
        except Exception as e:
            print(f"   ⚠️ 清理失败: {e}")
        
        print("\n✅ 测试完成!")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    simple_test()
