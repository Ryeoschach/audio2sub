import os
import logging
import subprocess
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import timedelta
import platform
import requests
import shutil

from .config import settings

logger = logging.getLogger(__name__)

class WhisperManager:
    """Manages whisper.cpp command line tool for transcription"""
    
    # Model download URLs for different versions
    MODEL_URLS = {
        "tiny": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin",
        "tiny.en": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin",
        "base": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin", 
        "base.en": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin",
        "small": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
        "small.en": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin",
        "medium": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin",
        "medium.en": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.en.bin",
        "large-v1": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v1.bin",
        "large-v2": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v2.bin",
        "large-v3": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin",
        "large-v3-turbo": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin",
    }
    
    def __init__(self):
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        self.whisper_cpp_path = self._find_or_compile_whisper_cpp()
    
    def _get_whisper_build_dir(self) -> Path:
        """Get the whisper.cpp build directory based on deployment mode"""
        if hasattr(settings, 'DEPLOYMENT_MODE'):
            if settings.DEPLOYMENT_MODE == 'native':
                # For native mode, use a local build directory
                return Path.home() / ".audio2sub" / "whisper.cpp"
            elif settings.DEPLOYMENT_MODE == 'hybrid':
                # For hybrid mode, whisper.cpp is already compiled in container
                return Path("/usr/local/bin")
        
        # Default location
        return Path.cwd() / "whisper.cpp"
    
    def _detect_optimal_build_flags(self) -> Dict[str, str]:
        """Detect optimal build flags for the current system"""
        build_flags = {}
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        if system == "darwin":  # macOS
            if machine in ["arm64", "aarch64"]:
                # Apple Silicon - use Metal acceleration
                build_flags["WHISPER_METAL"] = "1"
                logger.info("Detected Apple Silicon, enabling Metal acceleration")
            else:
                # Intel Mac - use basic optimizations
                build_flags["WHISPER_NO_ACCELERATE"] = "0"  # Enable Accelerate framework
                logger.info("Detected Intel Mac, enabling Accelerate framework")
        
        elif system == "linux":
            # Check for NVIDIA GPU
            try:
                result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    build_flags["WHISPER_CUDA"] = "1"
                    logger.info("Detected NVIDIA GPU, enabling CUDA acceleration")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.info("No NVIDIA GPU detected, using CPU optimizations")
        
        return build_flags
    
    def _compile_whisper_cpp(self, build_dir: Path) -> Optional[str]:
        """Dynamically compile whisper.cpp with optimal settings for current system"""
        try:
            logger.info(f"Compiling whisper.cpp in {build_dir}")
            
            # Create build directory if it doesn't exist
            build_dir.mkdir(parents=True, exist_ok=True)
            
            # Clone whisper.cpp if not exists
            if not (build_dir / "CMakeLists.txt").exists():
                logger.info("Cloning whisper.cpp repository...")
                subprocess.run([
                    "git", "clone", 
                    "https://github.com/ggerganov/whisper.cpp.git", 
                    str(build_dir)
                ], check=True, timeout=120)
            
            # Detect optimal build flags
            build_flags = self._detect_optimal_build_flags()
            
            # Create build subdirectory
            cmake_build_dir = build_dir / "build"
            cmake_build_dir.mkdir(exist_ok=True)
            
            # Prepare CMake command
            cmake_cmd = ["cmake", ".."]
            for flag, value in build_flags.items():
                cmake_cmd.append(f"-D{flag}={value}")
            
            # Run CMake configuration
            logger.info(f"Running CMake: {' '.join(cmake_cmd)}")
            subprocess.run(cmake_cmd, cwd=cmake_build_dir, check=True, timeout=60)
            
            # Compile
            make_cmd = ["make", "-j", str(os.cpu_count() or 4)]
            logger.info(f"Compiling with: {' '.join(make_cmd)}")
            subprocess.run(make_cmd, cwd=cmake_build_dir, check=True, timeout=300)
            
            # Find the compiled executable
            whisper_exe = cmake_build_dir / "bin" / "whisper-cli"
            if whisper_exe.exists() and whisper_exe.is_file():
                # Make executable
                whisper_exe.chmod(0o755)
                logger.info(f"Successfully compiled whisper.cpp at: {whisper_exe}")
                return str(whisper_exe)
            else:
                logger.error(f"Compiled whisper.cpp not found at expected location: {whisper_exe}")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to compile whisper.cpp: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during whisper.cpp compilation: {e}")
            return None
    
    def _find_or_compile_whisper_cpp(self) -> Optional[str]:
        """Find existing whisper.cpp or compile it dynamically"""
        # In hybrid/docker mode, whisper.cpp should already be available
        if (hasattr(settings, 'DEPLOYMENT_MODE') and 
            settings.DEPLOYMENT_MODE in ['hybrid', 'docker']):
            whisper_path = "/usr/local/bin/whisper-cli"
            if os.path.exists(whisper_path) and os.access(whisper_path, os.X_OK):
                logger.info(f"Found whisper.cpp in container at: {whisper_path}")
                return whisper_path
            else:
                logger.warning(f"whisper.cpp not found in container at: {whisper_path}")
        
        # Try configured path first
        if hasattr(settings, 'WHISPER_CPP_PATH') and settings.WHISPER_CPP_PATH:
            whisper_path = Path(settings.WHISPER_CPP_PATH)
            if whisper_path.exists() and whisper_path.is_file():
                logger.info(f"Found whisper.cpp at configured path: {whisper_path}")
                return str(whisper_path)
        
        # Search common installation paths
        common_paths = [
            "whisper-cli",  # If in PATH
            "/usr/local/bin/whisper-cli",
            "/opt/homebrew/bin/whisper-cli",
            "/Users/creed/workspace/sourceCode/whisper.cpp/build/bin/whisper-cli",  # Local build
        ]
        
        for path in common_paths:
            try:
                result = subprocess.run([path, "--help"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    logger.info(f"Found existing whisper.cpp at: {path}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                continue
        
        # If not found and in native mode, try to compile dynamically
        if (hasattr(settings, 'DEPLOYMENT_MODE') and 
            settings.DEPLOYMENT_MODE == 'native'):
            logger.info("whisper.cpp not found, attempting dynamic compilation...")
            build_dir = self._get_whisper_build_dir()
            compiled_path = self._compile_whisper_cpp(build_dir)
            if compiled_path:
                return compiled_path
        
        logger.warning("whisper.cpp not found and compilation failed/not attempted")
        return None
    
    def _download_model(self, model_name: str) -> Path:
        """Download whisper.cpp model if not exists"""
        # In hybrid mode, try mounted models first
        if (hasattr(settings, 'DEPLOYMENT_MODE') and 
            settings.DEPLOYMENT_MODE == 'hybrid'):
            # In hybrid mode, models might be mounted at /app/models/
            model_file = Path(f"/app/models/ggml-{model_name}.bin")
            if model_file.exists():
                logger.info(f"Using mounted model in hybrid mode: {model_file}")
                return model_file
            else:
                logger.info(f"Model {model_name} not found in mounted path: {model_file}, will download")
        
        model_file = self.models_dir / f"ggml-{model_name}.bin"
        
        if model_file.exists():
            logger.info(f"Model {model_name} already exists at {model_file}")
            return model_file
        
        if model_name not in self.MODEL_URLS:
            raise ValueError(f"Unknown model name: {model_name}. Available: {list(self.MODEL_URLS.keys())}")
        
        url = self.MODEL_URLS[model_name]
        logger.info(f"Downloading model {model_name} from {url}")
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(model_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024) == 0:  # Log every MB
                                logger.info(f"Download progress: {progress:.1f}%")
            
            logger.info(f"Model {model_name} downloaded successfully to {model_file}")
            return model_file
            
        except Exception as e:
            if model_file.exists():
                model_file.unlink()  # Remove partially downloaded file
            raise RuntimeError(f"Failed to download model {model_name}: {e}")
    
    def transcribe(self, audio_file_path: str, model_name: str = None, language: str = None, task_type: str = None) -> Dict[str, Any]:
        """
        Transcribe audio file using whisper.cpp command line tool
        
        Args:
            audio_file_path: 音频文件路径
            model_name: 模型名称 (可选，覆盖默认配置)
            language: 语言代码 (可选，覆盖默认配置)
            task_type: 任务类型 (可选，覆盖默认配置)
        """
        if not self.whisper_cpp_path:
            # Fallback: create mock transcription for testing
            logger.warning("whisper.cpp not available, creating mock transcription")
            return self._create_mock_transcription(audio_file_path)
        
        # 使用传入的参数或默认配置
        final_model_name = model_name or settings.MODEL_NAME
        final_language = language or settings.WHISPER_LANGUAGE
        final_task_type = task_type or settings.WHISPER_TASK
        
        try:
            logger.info(f"Starting transcription with whisper.cpp for {audio_file_path}")
            logger.info(f"Using model: {final_model_name}, language: {final_language}, task: {final_task_type}")
            start_time = time.time()
            
            # Download model if needed
            model_path = self._download_model(final_model_name)
            
            # Prepare whisper.cpp command
            cmd = [
                self.whisper_cpp_path,
                "-f", audio_file_path,  # 输入音频文件
                "-m", str(model_path),  # 模型路径
                "-oj",  # 输出JSON格式
                "-of", "/tmp/whisper_output",  # 输出文件前缀
                "-ng",  # 强制使用CPU模式避免GPU超时
            ]
            
            # Add additional parameters
            if settings.WHISPER_THREADS > 0:
                cmd.extend(["-t", str(settings.WHISPER_THREADS)])
            
            if final_language != "auto":
                cmd.extend(["-l", final_language])
            
            if final_task_type == "translate":
                cmd.append("--translate")
            
            # Run whisper.cpp
            logger.info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"whisper.cpp failed with code {result.returncode}")
                logger.error(f"stderr: {result.stderr}")
                raise RuntimeError(f"whisper.cpp failed: {result.stderr}")
            
            # Read JSON output
            json_file = Path("/tmp/whisper_output.json")
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    whisper_result = json.load(f)
                
                # Clean up temp file
                json_file.unlink()
                
                # Extract transcription text and segments from whisper.cpp JSON format
                transcription_segments = whisper_result.get("transcription", [])
                full_text = " ".join([seg.get("text", "").strip() for seg in transcription_segments])
                language = whisper_result.get("result", {}).get("language", "unknown")
                
            else:
                # Fallback: parse text output
                full_text = result.stdout.strip()
                transcription_segments = []
                language = "unknown"
            
            end_time = time.time()
            transcription_duration = end_time - start_time
            
            logger.info(f"Transcription completed in {transcription_duration:.2f} seconds")
            
            # Format result to match expected structure
            formatted_result = {
                "text": full_text,
                "segments": self._format_segments(transcription_segments),
                "transcription_time": transcription_duration,
                "transcription_time_formatted": str(timedelta(seconds=int(transcription_duration))),
                "language": language
            }
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise RuntimeError(f"whisper.cpp transcription failed: {e}")
    
    def _create_mock_transcription(self, audio_file_path: str) -> Dict[str, Any]:
        """Create a mock transcription for testing when whisper.cpp is not available"""
        mock_text = "This is a mock transcription generated because whisper.cpp is not available on this system."
        
        # Create mock segments with timing
        mock_segments = []
        words = mock_text.split()
        word_duration = 0.5  # 0.5 seconds per word
        
        for i, word in enumerate(words):
            start_time = i * word_duration
            end_time = (i + 1) * word_duration
            mock_segments.append({
                "start": start_time,
                "end": end_time,
                "text": word,
                "words": [{
                    "start": start_time,
                    "end": end_time,
                    "word": word,
                    "probability": 1.0
                }]
            })
        
        return {
            "text": mock_text,
            "segments": mock_segments,
            "transcription_time": 1.0,
            "transcription_time_formatted": "0:00:01",
            "language": "en"
        }
    
    def _format_segments(self, segments: List[Dict]) -> List[Dict]:
        """Format whisper.cpp segments to match expected structure"""
        formatted_segments = []
        
        for segment in segments:
            # whisper.cpp offsets are in milliseconds
            start_ms = segment.get("offsets", {}).get("from", 0)
            end_ms = segment.get("offsets", {}).get("to", 0)
            
            formatted_segment = {
                "start": start_ms / 1000.0,  # Convert from milliseconds to seconds
                "end": end_ms / 1000.0,
                "text": segment.get("text", "").strip(),
                "words": []
            }
            
            # Add word-level timestamps if available
            if "words" in segment:
                for word in segment["words"]:
                    word_start_ms = word.get("offsets", {}).get("from", 0)
                    word_end_ms = word.get("offsets", {}).get("to", 0)
                    formatted_word = {
                        "start": word_start_ms / 1000.0,
                        "end": word_end_ms / 1000.0,
                        "word": word.get("word", "").strip(),
                        "probability": word.get("probability", 1.0)
                    }
                    formatted_segment["words"].append(formatted_word)
            
            if formatted_segment["text"]:
                formatted_segments.append(formatted_segment)
        
        return formatted_segments

# Global whisper manager instance
_whisper_manager = None

def get_whisper_manager() -> WhisperManager:
    """Get or create the global whisper manager instance"""
    global _whisper_manager
    if _whisper_manager is None:
        _whisper_manager = WhisperManager()
    return _whisper_manager