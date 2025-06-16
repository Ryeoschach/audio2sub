from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    APP_NAME: str = "Audio2Sub Backend"
    DEBUG: bool = True

    # Default to local Redis settings
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379  # User confirmed Redis is running on port 16379
    REDIS_PASSWORD: str | None = "redispassword" # From 说明文档
    # REDIS_PASSWORD: str | None = None  # Optional, can be set in .env file

    REDIS_DB: int = 0

    # Default Celery broker and result backend to local Redis with password
    # Ensure these are constructed correctly, especially if REDIS_PASSWORD can be None
    CELERY_BROKER_URL: Optional[str] = None # Will be constructed in __init__
    CELERY_RESULT_BACKEND: Optional[str] = None # Will be constructed in __init__

    # Path where Whisper models are stored (if downloaded locally)
    # For Hugging Face Transformers, models are typically cached automatically.
    # MODEL_PATH can be used if you have a specific local directory for models.
    MODEL_PATH: Optional[str] = None 
    MODEL_NAME: str = "openai/whisper-large-v3-turbo" # Valid Hugging Face model ID
    MODEL_DEVICE: str = "mps" # "mps" for Apple Silicon, "cuda" for NVIDIA, "cpu"
    TORCH_DTYPE: str = "float16" # PyTorch dtype for model, e.g., "float16", "float32". MPS often prefers float16.
    
    # Performance optimization settings
    BATCH_SIZE: int = 4 # Batch size for processing audio chunks (lower for stability)
    CHUNK_LENGTH_S: int = 30 # Length of audio chunks in seconds (minimum 15s recommended)
    STRIDE_LENGTH_S: int = 5 # Stride between chunks in seconds (for overlap, must be < chunk_length)
    
    # Subtitle generation settings
    MAX_SUBTITLE_DURATION: int = 6 # Maximum duration for a single subtitle entry (seconds)
    MAX_WORDS_PER_SUBTITLE: int = 10 # Maximum number of words per subtitle entry
    MAX_CHARS_PER_SUBTITLE: int = 60 # Maximum number of characters per subtitle entry
    
    # Number of threads for CTranslate2 computation - Not directly applicable to Transformers pipeline
    MODEL_NUM_WORKERS: int = 4  # Use single thread to avoid issues

    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # File upload and results directories
    UPLOAD_DIR: str = "uploads"
    RESULTS_DIR: str = "results"

    # FFmpeg path (usually in PATH, but can be specified if needed)
    # FFMPEG_PATH: str = "/usr/bin/ffmpeg"

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

settings = Settings()
