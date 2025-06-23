#!/usr/bin/env python3
"""
简单的测试脚本，用于启动FastAPI应用
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    print("🚀 Starting Audio2Sub Backend with whisper.cpp integration")
    print("📍 API will be available at: http://localhost:8000")
    print("📖 API docs will be available at: http://localhost:8000/docs")
    print("📊 Model configuration:")
    from app.config import settings
    print(f"   - Model: {settings.MODEL_NAME}")
    print(f"   - Device: {settings.WHISPER_DEVICE}")
    print(f"   - Language: {settings.WHISPER_LANGUAGE}")
    print(f"   - Task: {settings.WHISPER_TASK}")
    print()
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
