import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

print("=== 最简化 faster-whisper 测试 ===")

from config import TEST_AUDIO_PATH

if not TEST_AUDIO_PATH.exists():
    print(f"❌ 音频文件不存在: {TEST_AUDIO_PATH}")
    exit(1)

print(f"✅ 音频文件: {TEST_AUDIO_PATH}")

try:
    from faster_whisper import WhisperModel
    
    # 使用最简单的配置
    config = {"compute_type": "float32", "device": "cpu"}
    
    print(f"--- 配置: {config} ---")
    model = WhisperModel("base", **config)
    print("✅ 模型加载成功")
    
    print("开始转录...")
    import time
    start_time = time.time()
    
    segments, info = model.transcribe(str(TEST_AUDIO_PATH), language="zh")
    
    # 只取前2个分段避免长时间处理
    first_segments = []
    for i, segment in enumerate(segments):
        if i >= 2:
            break
        first_segments.append(segment)
    
    total_time = time.time() - start_time
    
    print(f"✅ 转录成功！耗时: {total_time:.2f}秒")
    print(f"📊 音频时长: {info.duration:.2f}秒")
    print(f"🈳 检测语言: {info.language}")
    print(f"📝 前{len(first_segments)}段:")
    
    for j, segment in enumerate(first_segments, 1):
        print(f"  {j}. [{segment.start:.1f}s-{segment.end:.1f}s] {segment.text}")
    
    print("🎉 测试成功！")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
