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
    }
    
    def __init__(self):
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        self.whisper_cpp_path = self._find_whisper_cpp()
    
    def _find_whisper_cpp(self) -> Optional[str]:
        """Find whisper.cpp executable"""
        # Common paths where whisper.cpp might be installed
        possible_paths = [
            "whisper",  # If in PATH
            "/usr/local/bin/whisper",
            "/opt/homebrew/bin/whisper",
            "./whisper",  # Local build
            "../whisper.cpp/main",  # If built from source in parent directory
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, "--help"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    logger.info(f"Found whisper.cpp at: {path}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                continue
        
        logger.warning("whisper.cpp not found. Please install whisper.cpp and make sure it's in PATH")
        return None
    
    def _download_model(self, model_name: str) -> Path:
        """Download whisper.cpp model if not exists"""
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
    
    def transcribe(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe audio file using whisper.cpp command line tool"""
        if not self.whisper_cpp_path:
            # Fallback: create mock transcription for testing
            logger.warning("whisper.cpp not available, creating mock transcription")
            return self._create_mock_transcription(audio_file_path)
        
        try:
            logger.info(f"Starting transcription with whisper.cpp for {audio_file_path}")
            start_time = time.time()
            
            # Download model if needed
            model_name = settings.MODEL_NAME
            model_path = self._download_model(model_name)
            
            # Prepare whisper.cpp command
            cmd = [
                self.whisper_cpp_path,
                "-f", audio_file_path,
                "-m", str(model_path),
                "-oj",  # Output JSON
                "-of", "/tmp/whisper_output",  # Output file prefix
            ]
            
            # Add additional parameters
            if settings.WHISPER_THREADS > 0:
                cmd.extend(["-t", str(settings.WHISPER_THREADS)])
            
            if settings.WHISPER_LANGUAGE != "auto":
                cmd.extend(["-l", settings.WHISPER_LANGUAGE])
            
            if settings.WHISPER_TASK == "translate":
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
            else:
                # Fallback: parse text output
                whisper_result = {"text": result.stdout, "segments": []}
            
            end_time = time.time()
            transcription_duration = end_time - start_time
            
            logger.info(f"Transcription completed in {transcription_duration:.2f} seconds")
            
            # Format result to match expected structure
            formatted_result = {
                "text": whisper_result.get("text", ""),
                "segments": self._format_segments(whisper_result.get("segments", [])),
                "transcription_time": transcription_duration,
                "transcription_time_formatted": str(timedelta(seconds=int(transcription_duration))),
                "language": "unknown"  # whisper.cpp doesn't always provide language info
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
            formatted_segment = {
                "start": segment.get("offsets", {}).get("from", 0) / 100.0,  # Convert from centiseconds
                "end": segment.get("offsets", {}).get("to", 0) / 100.0,
                "text": segment.get("text", "").strip(),
                "words": []
            }
            
            # Add word-level timestamps if available
            if "words" in segment:
                for word in segment["words"]:
                    formatted_word = {
                        "start": word.get("offsets", {}).get("from", 0) / 100.0,
                        "end": word.get("offsets", {}).get("to", 0) / 100.0,
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
