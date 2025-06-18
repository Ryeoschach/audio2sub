import os
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import timedelta
import platform

# Use OpenAI Whisper instead of whisper.cpp for better compatibility
try:
    import whisper
except ImportError:
    raise ImportError("Please install openai-whisper: pip install openai-whisper")

from .config import settings

logger = logging.getLogger(__name__)

class WhisperManager:
    """Manages OpenAI Whisper model loading and inference"""
    
    def __init__(self):
        self.whisper_model: Optional[whisper.Whisper] = None
        self.current_model_name: Optional[str] = None
    
    def _get_device_setting(self) -> str:
        """Determine the best device setting for whisper"""
        device = settings.WHISPER_DEVICE.lower()
        
        if device == "auto":
            # Auto-detect best available device
            try:
                system = platform.system()
                
                if system == "Darwin":  # macOS
                    # Check for Apple Silicon
                    machine = platform.machine()
                    if machine == "arm64":
                        logger.info("Detected Apple Silicon, using CPU with optimizations")
                        return "cpu"  # OpenAI Whisper doesn't support MPS yet
                    else:
                        logger.info("Detected Intel Mac, using CPU")
                        return "cpu"
                else:
                    logger.info("Using CPU for maximum compatibility")
                    return "cpu"
            except Exception as e:
                logger.warning(f"Device auto-detection failed: {e}, defaulting to CPU")
                return "cpu"
        
        # Force CPU for OpenAI Whisper compatibility
        if device in ["cuda", "metal", "mps"]:
            logger.warning(f"Device {device} not supported with OpenAI Whisper, using CPU")
            return "cpu"
        
        return "cpu"
    
    def load_model(self, model_name: Optional[str] = None) -> whisper.Whisper:
        """Load or reload OpenAI Whisper model"""
        model_name = model_name or settings.MODEL_NAME
        
        if self.whisper_model and self.current_model_name == model_name:
            logger.info(f"Model {model_name} already loaded")
            return self.whisper_model
        
        # Determine device
        device = self._get_device_setting()
        
        try:
            logger.info(f"Loading OpenAI Whisper model: {model_name} on device: {device}")
            
            # Load model with device setting
            self.whisper_model = whisper.load_model(model_name, device=device)
            self.current_model_name = model_name
            
            logger.info(f"✅ Whisper model {model_name} loaded successfully on {device}")
            return self.whisper_model
            
        except Exception as e:
            logger.error(f"Failed to load OpenAI Whisper model: {e}")
            raise RuntimeError(f"Could not load OpenAI Whisper model {model_name}: {e}")
    
    def transcribe(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe audio file using OpenAI Whisper"""
        if not self.whisper_model:
            self.load_model()
        
        try:
            logger.info(f"Starting transcription with OpenAI Whisper for {audio_file_path}")
            start_time = time.time()
            
            # Prepare transcription parameters
            transcribe_options = {
                "verbose": False,
                "word_timestamps": settings.WHISPER_WORD_TIMESTAMPS,
                "temperature": settings.WHISPER_TEMPERATURE,
            }
            
            # Add language if specified
            if settings.WHISPER_LANGUAGE != "auto":
                transcribe_options["language"] = settings.WHISPER_LANGUAGE
            
            # Add task if specified
            if settings.WHISPER_TASK == "translate":
                transcribe_options["task"] = "translate"
            
            # Perform transcription
            result = self.whisper_model.transcribe(audio_file_path, **transcribe_options)
            
            end_time = time.time()
            transcription_duration = end_time - start_time
            
            logger.info(f"Transcription completed in {transcription_duration:.2f} seconds")
            
            # Format result to match expected structure
            formatted_result = {
                "text": result.get("text", ""),
                "segments": self._format_segments(result.get("segments", [])),
                "transcription_time": transcription_duration,
                "transcription_time_formatted": str(timedelta(seconds=int(transcription_duration))),
                "language": result.get("language", "unknown")
            }
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise RuntimeError(f"OpenAI Whisper transcription failed: {e}")
    
    def _format_segments(self, segments: List[Dict]) -> List[Dict]:
        """Format OpenAI Whisper segments to match expected structure"""
        formatted_segments = []
        
        for segment in segments:
            formatted_segment = {
                "start": segment.get("start", 0.0),
                "end": segment.get("end", 0.0),
                "text": segment.get("text", "").strip(),
                "words": []
            }
            
            # Add word-level timestamps if available
            if "words" in segment:
                for word in segment["words"]:
                    formatted_word = {
                        "start": word.get("start", 0.0),
                        "end": word.get("end", 0.0),
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
