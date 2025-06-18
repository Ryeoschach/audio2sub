from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    APP_NAME: str = "Audio2Sub Backend"
    DEBUG: bool = True

    # Default to local Redis settings
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 16379  # 使用Redis默认端口
    REDIS_PASSWORD: str | None = None  # 使用密码
    REDIS_DB: int = 0

    # Default Celery broker and result backend to local Redis with password
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # Whisper.cpp executable path
    WHISPER_CPP_PATH: str = "/Users/creed/workspace/sourceCode/whisper.cpp/build/bin/whisper-cli"
    
    # Whisper.cpp model configuration
    MODEL_PATH: str = "models/ggml-base.bin"  # Path to whisper.cpp model file
    MODEL_NAME: str = "base"  # Model size: tiny, base, small, medium, large-v1, large-v2, large-v3
    
    # Processing device configuration
    # whisper.cpp supports: "cpu", "cuda", "metal" (for Apple Silicon)
    WHISPER_DEVICE: str = "auto"  # auto, cpu, cuda, metal
    
    # Whisper.cpp processing parameters
    WHISPER_THREADS: int = 0  # 0 = auto-detect optimal thread count
    WHISPER_PROCESSORS: int = 1  # Number of processors to use
    
    # Language and task settings
    WHISPER_LANGUAGE: str = "auto"  # "auto" for auto-detection, or specific language code
    WHISPER_TASK: str = "transcribe"  # "transcribe" or "translate"
    
    # Audio processing settings
    WHISPER_MAX_LEN: int = 0  # Maximum length to process (0 = no limit)
    WHISPER_SPLIT_ON_WORD: bool = True  # Split on word boundaries
    WHISPER_WORD_TIMESTAMPS: bool = True  # Enable word-level timestamps
    
    # Model performance settings
    WHISPER_TEMPERATURE: float = 0.0  # Temperature for sampling (0.0 = deterministic)
    WHISPER_BEST_OF: int = 5  # Number of candidates to consider
    WHISPER_BEAM_SIZE: int = 5  # Beam size for beam search
    
    # Subtitle generation settings
    MAX_SUBTITLE_DURATION: int = 4  # Maximum duration for a single subtitle entry (seconds)
    MAX_WORDS_PER_SUBTITLE: int = 8  # Maximum number of words per subtitle entry
    MAX_CHARS_PER_SUBTITLE: int = 50  # Maximum number of characters per subtitle entry
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # File upload and results directories
    UPLOAD_DIR: str = "uploads"
    RESULTS_DIR: str = "results"

    class Config:
        env_file = ".env" # This will override defaults if .env file exists
        env_file_encoding = "utf-8"
        extra = "ignore" # Add this to ignore extra fields not defined in Settings

    def __init__(self, **values):
        super().__init__(**values)
        # Construct Celery URLs after other base settings are loaded
        if self.REDIS_PASSWORD:
            self.CELERY_BROKER_URL = f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            self.CELERY_RESULT_BACKEND = f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        else:
            self.CELERY_BROKER_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            self.CELERY_RESULT_BACKEND = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        
        # Create upload and results directories
        import os
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.RESULTS_DIR, exist_ok=True)

settings = Settings()
