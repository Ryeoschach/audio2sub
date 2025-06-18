"""
依赖管理和环境检查脚本
"""
import subprocess
import sys
from pathlib import Path

def check_dependencies():
    """检查依赖项"""
    required_packages = [
        "torch",
        "transformers",
        "librosa",
        "numpy",
    ]
    
    optional_packages = [
        "faster-whisper",
    ]
    
    print("=== 检查必需依赖 ===")
    missing_required = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_required.append(package)
    
    print("\n=== 检查可选依赖 ===")
    missing_optional = []
    
    for package in optional_packages:
        try:
            if package == "faster-whisper":
                from faster_whisper import WhisperModel
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"⚠️  {package} (可选)")
            missing_optional.append(package)
    
    return missing_required, missing_optional

def install_dependencies():
    """安装缺失的依赖"""
    print("\n=== 安装依赖 ===")
    
    # 基础依赖
    basic_deps = [
        "torch",
        "transformers",
        "librosa",
        "numpy",
    ]
    
    for dep in basic_deps:
        try:
            print(f"Installing {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {dep}: {e}")
    
    # faster-whisper需要特殊处理
    try:
        print("Installing faster-whisper...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "faster-whisper"])
    except subprocess.CalledProcessError as e:
        print(f"Failed to install faster-whisper: {e}")
        print("You can install it manually with: pip install faster-whisper")

def check_model_cache():
    """检查本地模型缓存"""
    from config import FASTER_WHISPER_MODEL_PATH, HUGGINGFACE_CACHE
    
    print(f"\n=== 检查模型缓存 ===")
    print(f"Hugging Face缓存目录: {HUGGINGFACE_CACHE}")
    print(f"存在: {HUGGINGFACE_CACHE.exists()}")
    
    if HUGGINGFACE_CACHE.exists():
        models = list(HUGGINGFACE_CACHE.glob("models--*whisper*"))
        print(f"找到 {len(models)} 个Whisper模型:")
        for model in models:
            print(f"  - {model.name}")
    
    print(f"\nFaster-Whisper Base模型: {FASTER_WHISPER_MODEL_PATH}")
    print(f"存在: {FASTER_WHISPER_MODEL_PATH.exists()}")
    
    if FASTER_WHISPER_MODEL_PATH.exists():
        model_files = list(FASTER_WHISPER_MODEL_PATH.glob("*"))
        print(f"模型文件数量: {len(model_files)}")

def setup_environment():
    """设置测试环境"""
    print("=== 设置测试环境 ===")
    
    # 检查并创建输出目录
    from config import OUTPUT_DIR
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"✅ 输出目录: {OUTPUT_DIR}")
    
    # 检查测试音频
    from config import TEST_AUDIO_PATH
    print(f"测试音频: {TEST_AUDIO_PATH}")
    print(f"存在: {TEST_AUDIO_PATH.exists()}")
    
    if not TEST_AUDIO_PATH.exists():
        print("⚠️  测试音频文件不存在，请检查路径或提供有效的音频文件")

def main():
    """主函数"""
    print("Whisper混合架构测试环境检查\n")
    
    # 检查依赖
    missing_required, missing_optional = check_dependencies()
    
    if missing_required:
        print(f"\n❌ 缺少必需依赖: {missing_required}")
        install_choice = input("是否安装缺失的依赖? (y/n): ")
        if install_choice.lower() == 'y':
            install_dependencies()
        else:
            print("请手动安装缺失的依赖后再运行测试")
            return
    
    # 检查模型缓存
    check_model_cache()
    
    # 设置环境
    setup_environment()
    
    # 检查设备配置
    print(f"\n=== 设备配置 ===")
    from config import get_device_config
    config = get_device_config()
    for key, value in config.items():
        print(f"{key}: {value}")
    
    print(f"\n✅ 环境检查完成！")
    print(f"📝 运行测试: python test_main.py")

if __name__ == "__main__":
    main()
