from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
from pathlib import Path
from typing import Optional

from .config import settings
from .tasks import create_transcription_task
from .models import (
    ModelSize, LanguageCode, OutputFormat, 
    TranscriptionResponse, ModelInfo, ModelsListResponse
)

app = FastAPI(
    title="Audio2Sub API",
    description="API for transcribing audio and video files to subtitles.",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS, # Allows all origins from .env or default ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
RESULTS_DIR = Path("results")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/")
async def root():
    """根路径 - 返回API基本信息"""
    return {
        "app": "Audio2Sub Backend",
        "version": "0.1.0", 
        "description": "Audio transcription service using whisper.cpp",
        "endpoints": {
            "upload": "/upload/",
            "models": "/models/",
            "status": "/status/{task_id}",
            "results": "/results/{file_id}/{filename}",
            "health": "/health",
            "ping": "/ping"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        from .config import settings
        
        # 检查基本配置
        config_status = "loaded"
        
        # 检查Redis连接
        import redis
        try:
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            r.ping()
            redis_status = "connected"
        except Exception as e:
            redis_status = f"disconnected ({str(e)})"
        
        # 基本部署信息
        deployment_info = {
            "mode": settings.DEPLOYMENT_MODE,
            "device": settings.WHISPER_DEVICE,
            "model": settings.MODEL_NAME
        }
        
        return {
            "status": "healthy" if "connected" in redis_status else "partial",
            "config": config_status,
            "redis": redis_status,
            "deployment": deployment_info,
            "version": "0.1.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/ping")
async def ping():
    return {"ping": "pong!"}

@app.post("/upload/", response_model=TranscriptionResponse, tags=["Transcription"])
async def upload_file_for_transcription(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    model: ModelSize = Form(default=ModelSize.BASE),
    language: LanguageCode = Form(default=LanguageCode.AUTO),
    output_format: OutputFormat = Form(default=OutputFormat.BOTH),
    task: str = Form(default="transcribe")
):
    """
    上传音频/视频文件进行转录
    
    - **file**: 音频或视频文件
    - **model**: Whisper 模型大小 (tiny, base, small, medium, large-v1, large-v2, large-v3, large-v3-turbo)
    - **language**: 音频语言代码 (auto, zh, en, ja, ko, 等)
    - **output_format**: 输出格式 (srt, vtt, both)
    - **task**: 任务类型 (transcribe 或 translate)
    """
    # 验证模型是否支持
    if model.value not in settings.SUPPORTED_MODELS:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的模型: {model.value}. 支持的模型: {list(settings.SUPPORTED_MODELS.keys())}"
        )
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file name provided")

    # Sanitize filename (basic example)
    original_filename = Path(file.filename).name
    file_id = str(uuid.uuid4())
    file_extension = Path(original_filename).suffix
    # Ensure extension is one of common audio/video types, or let ffmpeg handle it
    # For simplicity, we'll save with original extension for now
    saved_filename = f"{file_id}{file_extension}"
    file_path = UPLOAD_DIR / saved_filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
    finally:
        file.file.close()

    # 准备转录参数
    transcription_params = {
        "model": model.value,
        "language": language.value,
        "output_format": output_format.value,
        "task": task
    }

    # Create a task for Celery with dynamic parameters
    task_result = create_transcription_task.delay(
        str(file_path), 
        file_id, 
        original_filename,
        transcription_params
    )

    # 预估处理时间（基于模型大小）
    estimated_times = {
        "tiny": 30, "tiny.en": 30,
        "base": 60, "base.en": 60,
        "small": 120, "small.en": 120,
        "medium": 300, "medium.en": 300,
        "large-v1": 600, "large-v2": 600, "large-v3": 600,
        "large-v3-turbo": 150
    }
    estimated_time = estimated_times.get(model.value, 120)

    return TranscriptionResponse(
        task_id=task_result.id,
        file_id=file_id,
        message=f"文件已上传，开始使用 {model.value} 模型进行转录",
        model_used=model.value,
        estimated_time=estimated_time
    )

@app.get("/status/{task_id}", tags=["Transcription"])
async def get_task_status(task_id: str):
    try:
        task_result = create_transcription_task.AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            response = {
                'state': task_result.state,
                'status': 'Pending...'
            }
        elif task_result.state == 'FAILURE':
            # Handle failure state more safely
            try:
                error_info = task_result.info
                if isinstance(error_info, dict):
                    error_message = error_info.get('status', 'Task failed')
                else:
                    error_message = str(error_info)
            except Exception as e:
                # Fallback if we can't get the error info
                error_message = f"Task failed with unknown error: {str(e)}"
            
            response = {
                'state': task_result.state,
                'status': error_message,
            }
        elif task_result.state == 'SUCCESS':
            response = {
                'state': task_result.state,
                'status': 'Completed',
                'result': task_result.result
            }
        else:
            # Handle PROGRESS or other states
            try:
                info = task_result.info
                if isinstance(info, dict):
                    status = info.get('status', f'Task state: {task_result.state}')
                    progress = info.get('progress', 0)
                    response = {
                        'state': task_result.state,
                        'status': status,
                        'progress': progress
                    }
                else:
                    response = {
                        'state': task_result.state,
                        'status': str(info) if info else f'Task state: {task_result.state}',
                    }
            except Exception as e:
                # Fallback if we can't get task info
                response = {
                    'state': task_result.state,
                    'status': f'Task state: {task_result.state}',
                }
        
        return response
        
    except Exception as e:
        # Handle any unexpected errors in status checking
        return {
            'state': 'ERROR',
            'status': f'Error checking task status: {str(e)}'
        }

@app.get("/results/{file_id}/{filename}", tags=["Transcription"])
async def get_result_file(file_id: str, filename: str):
    # Basic security: ensure filename is just a name, not a path traversal attempt
    safe_filename = Path(filename).name 
    file_path = RESULTS_DIR / file_id / safe_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine appropriate media type for .srt or .vtt
    media_type = "text/plain" # Default
    if safe_filename.endswith(".srt"):
        media_type = "application/x-subrip"
    elif safe_filename.endswith(".vtt"):
        media_type = "text/vtt"

    from fastapi.responses import FileResponse
    return FileResponse(path=file_path, filename=safe_filename, media_type=media_type)

@app.get("/models/", response_model=ModelsListResponse, tags=["Models"])
async def get_supported_models():
    """获取支持的模型列表"""
    models = []
    for model_name, model_info in settings.SUPPORTED_MODELS.items():
        models.append(ModelInfo(
            name=model_name,
            size=model_info["size"],
            speed=model_info["speed"],
            accuracy=model_info["accuracy"],
            use_case=model_info["use_case"]
        ))
    
    return ModelsListResponse(
        models=models,
        default_model=settings.MODEL_NAME
    )

# Placeholder for WebSocket endpoint for real-time progress (optional)
# @app.websocket("/ws/progress/{task_id}")
# async def websocket_progress(websocket: WebSocket, task_id: str):
#     await websocket.accept()
#     # Logic to send progress updates
#     await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
