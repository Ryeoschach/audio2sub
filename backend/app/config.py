from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "Audio2Sub Backend"
    DEBUG: bool = True

    # Default to local Redis settings
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = "redispassword" # From 说明文档
    REDIS_DB: int = 0

    # Default Celery broker and result backend to local Redis with password
    CELERY_BROKER_URL: str = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    CELERY_RESULT_BACKEND: str = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

    # Path where Whisper models are stored (if downloaded locally)
    # faster-whisper will download to a cache dir by default if MODEL_PATH is not set.
    # Example: MODEL_PATH: str = "/path/to/your/models/faster-whisper-large-v3"
    MODEL_NAME: str = "base" # Default model, can be small, medium, large, large-v2, large-v3 etc.
    MODEL_DEVICE: str = "cpu" # "cuda" or "cpu"
    MODEL_COMPUTE_TYPE: str = "int8" # e.g., "float16", "int8"

    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # FFmpeg path (usually in PATH, but can be specified if needed)
    # FFMPEG_PATH: str = "/usr/bin/ffmpeg"

    class Config:
        env_file = ".env" # This will override defaults if .env file exists
        env_file_encoding = "utf-8"

settings = Settings()

# Update URLs if password is None, to avoid "redis://:None@..."
if settings.REDIS_PASSWORD is None:
    settings.CELERY_BROKER_URL = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
    settings.CELERY_RESULT_BACKEND = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
else:
    settings.CELERY_BROKER_URL = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
    settings.CELERY_RESULT_BACKEND = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
