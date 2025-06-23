from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
from pathlib import Path
from typing import Optional, List
import logging

from .config import settings
from .tasks import create_transcription_task, create_batch_transcription_task
from .models import (
    ModelSize, LanguageCode, OutputFormat, 
    TranscriptionResponse, ModelInfo, ModelsListResponse,
    BatchTranscriptionRequest, BatchTranscriptionResponse, 
    BatchTaskStatus, BatchResultSummary, BatchTaskInfo
)

# Configure logging
logger = logging.getLogger(__name__)

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
            "batch_upload": "/batch-upload/",
            "models": "/models/",
            "status": "/status/{task_id}",
            "batch_status": "/batch-status/{batch_id}",
            "batch_result": "/batch-result/{batch_id}",
            "batch_cancel": "/batch/{batch_id}",
            "results": "/results/{file_id}/{filename}",
            "health": "/health",
            "ping": "/ping"
        },
        "features": {
            "single_file_upload": "Support for single audio/video file transcription",
            "batch_upload": "Support for batch processing up to 50 files",
            "concurrent_processing": "Configurable concurrent file processing (1-10)",
            "multiple_formats": "Support for SRT and VTT subtitle formats",
            "multiple_models": "Support for various Whisper model sizes",
            "progress_tracking": "Real-time progress tracking for batch jobs"
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

# 批量处理API端点
@app.post("/batch-upload/", response_model=BatchTranscriptionResponse, tags=["Batch Transcription"])
async def batch_upload_files_for_transcription(
    files: List[UploadFile] = File(...),
    model: ModelSize = Form(default=ModelSize.BASE),
    language: LanguageCode = Form(default=LanguageCode.AUTO),
    output_format: OutputFormat = Form(default=OutputFormat.BOTH),
    task: str = Form(default="transcribe"),
    concurrent_limit: int = Form(default=3)
):
    """
    批量上传音频/视频文件进行转录
    
    - **files**: 多个音频或视频文件
    - **model**: Whisper 模型大小 (tiny, base, small, medium, large-v1, large-v2, large-v3, large-v3-turbo)
    - **language**: 音频语言代码 (auto, zh, en, ja, ko, 等)
    - **output_format**: 输出格式 (srt, vtt, both)
    - **task**: 任务类型 (transcribe 或 translate)
    - **concurrent_limit**: 并发处理文件数量限制 (1-10)
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    if len(files) > 50:  # 限制最大文件数量
        raise HTTPException(status_code=400, detail="Too many files. Maximum 50 files allowed.")
    
    # 验证模型是否支持
    if model.value not in settings.SUPPORTED_MODELS:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的模型: {model.value}. 支持的模型: {list(settings.SUPPORTED_MODELS.keys())}"
        )
    
    # 验证并发限制
    if concurrent_limit < 1 or concurrent_limit > 10:
        raise HTTPException(status_code=400, detail="Concurrent limit must be between 1 and 10")
    
    batch_id = str(uuid.uuid4())
    file_infos = []
    task_infos = []
    
    # 预估处理时间
    estimated_times = {
        "tiny": 30, "tiny.en": 30,
        "base": 60, "base.en": 60,
        "small": 120, "small.en": 120,
        "medium": 300, "medium.en": 300,
        "large-v1": 600, "large-v2": 600, "large-v3": 600,
        "large-v3-turbo": 150
    }
    single_file_time = estimated_times.get(model.value, 120)
    
    # 处理每个文件
    for file in files:
        if not file.filename:
            continue
            
        # 生成文件ID和保存路径
        file_id = str(uuid.uuid4())
        original_filename = Path(file.filename).name
        file_extension = Path(original_filename).suffix
        saved_filename = f"{file_id}{file_extension}"
        file_path = UPLOAD_DIR / saved_filename
        
        try:
            # 保存文件
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            file_infos.append({
                'file_id': file_id,
                'original_filename': original_filename,
                'file_path': str(file_path)
            })
            
            task_infos.append(BatchTaskInfo(
                file_id=file_id,
                filename=original_filename,
                task_id="",  # 将在批量任务中生成
                status="PENDING",
                progress=0,
                estimated_time=single_file_time
            ))
            
        except Exception as e:
            # 清理已保存的文件
            if file_path.exists():
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Could not save file {file.filename}: {e}")
        finally:
            file.file.close()
    
    if not file_infos:
        raise HTTPException(status_code=400, detail="No valid files to process")
    
    # 准备转录参数
    transcription_params = {
        "model": model.value,
        "language": language.value,
        "output_format": output_format.value,
        "task": task
    }
    
    # 准备批量任务信息
    batch_info = {
        'batch_id': batch_id,
        'file_infos': file_infos,
        'transcription_params': transcription_params,
        'concurrent_limit': concurrent_limit
    }
    
    # 创建批量处理任务
    batch_task_result = create_batch_transcription_task.delay(batch_info)
    
    # 计算总预估时间（考虑并发）
    total_files = len(file_infos)
    parallel_groups = (total_files + concurrent_limit - 1) // concurrent_limit
    estimated_total_time = parallel_groups * single_file_time
    
    return BatchTranscriptionResponse(
        batch_id=batch_id,
        message=f"批量任务已创建，共 {total_files} 个文件，使用 {model.value} 模型",
        total_files=total_files,
        tasks=task_infos,
        model_used=model.value,
        estimated_total_time=estimated_total_time
    )


@app.get("/batch-status/{batch_id}", response_model=BatchTaskStatus, tags=["Batch Transcription"])
async def get_batch_task_status(batch_id: str):
    """
    获取批量任务状态
    
    - **batch_id**: 批量任务ID
    """
    try:
        from .tasks import get_batch_status, get_batch_file_statuses
        
        # 获取批量任务状态
        batch_status = get_batch_status(batch_id)
        if not batch_status:
            raise HTTPException(status_code=404, detail="Batch task not found")
        
        # 获取所有文件的状态
        file_statuses = get_batch_file_statuses(batch_id)
        
        # 构建任务信息列表
        tasks = []
        for file_status in file_statuses:
            task_info = BatchTaskInfo(
                file_id=file_status.get('file_id', ''),
                filename=file_status.get('filename', ''),
                task_id=file_status.get('task_id', ''),
                status=file_status.get('status', 'UNKNOWN'),
                progress=int(file_status.get('progress', 0)),
                estimated_time=int(file_status.get('estimated_time', 30)),  # 默认30秒
                error=file_status.get('error')
            )
            tasks.append(task_info)
        
        # 计算统计信息
        total_files = len(tasks)
        completed_files = sum(1 for t in tasks if t.status == 'SUCCESS')
        failed_files = sum(1 for t in tasks if t.status == 'FAILURE')
        
        return BatchTaskStatus(
            batch_id=batch_id,
            total_files=total_files,
            completed_files=completed_files,
            failed_files=failed_files,
            progress_percentage=float(batch_status.get('progress_percentage', 0)),
            overall_status=batch_status.get('overall_status', 'UNKNOWN'),
            tasks=tasks,
            start_time=batch_status.get('start_time'),
            estimated_completion_time=batch_status.get('estimated_completion_time')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting batch status: {e}")


@app.get("/batch-result/{batch_id}", response_model=BatchResultSummary, tags=["Batch Transcription"])
async def get_batch_result_summary(batch_id: str):
    """
    获取批量任务结果汇总
    
    - **batch_id**: 批量任务ID
    """
    try:
        from .tasks import get_batch_status, get_batch_file_statuses, create_transcription_task
        
        # 获取批量任务状态
        batch_status = get_batch_status(batch_id)
        if not batch_status:
            raise HTTPException(status_code=404, detail="Batch task not found")
        
        overall_status = batch_status.get('overall_status', '')
        if overall_status not in ['COMPLETED', 'FAILED']:
            raise HTTPException(status_code=202, detail=f"Batch task is still in progress: {overall_status}")
        
        # 获取所有文件的详细结果
        file_statuses = get_batch_file_statuses(batch_id)
        
        results = []
        errors = []
        successful_files = 0
        failed_files = 0
        
        for file_status in file_statuses:
            task_id = file_status.get('task_id', '')
            file_id = file_status.get('file_id', '')
            filename = file_status.get('filename', 'unknown')
            status = file_status.get('status', 'UNKNOWN')
            
            if status == 'SUCCESS' and task_id:
                # 获取成功任务的详细结果
                try:
                    task_result = create_transcription_task.AsyncResult(task_id)
                    if task_result.state == 'SUCCESS':
                        task_data = task_result.result
                        results.append(task_data)
                        successful_files += 1
                    else:
                        errors.append({
                            "file_id": file_id,
                            "filename": filename,
                            "error": f"Task state: {task_result.state}"
                        })
                        failed_files += 1
                except Exception as e:
                    errors.append({
                        "file_id": file_id,
                        "filename": filename,
                        "error": f"Failed to get task result: {str(e)}"
                    })
                    failed_files += 1
            else:
                # 失败的任务
                errors.append({
                    "file_id": file_id,
                    "filename": filename,
                    "error": file_status.get('error', 'Unknown error')
                })
                failed_files += 1
        
        return BatchResultSummary(
            batch_id=batch_id,
            total_files=len(file_statuses),
            successful_files=successful_files,
            failed_files=failed_files,
            total_processing_time=float(batch_status.get('total_processing_time', 0)),
            results=results,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting batch result: {e}")


@app.delete("/batch/{batch_id}", tags=["Batch Transcription"])
async def cancel_batch_task(batch_id: str):
    """
    取消批量任务
    
    - **batch_id**: 批量任务ID
    """
    try:
        from .tasks import create_batch_transcription_task, get_batch_file_statuses
        
        # 获取批量任务
        batch_task_result = create_batch_transcription_task.AsyncResult(batch_id)
        
        if batch_task_result.state in ['SUCCESS', 'FAILURE']:
            return {"message": "Batch task already completed"}
        
        # 尝试撤销任务
        batch_task_result.revoke(terminate=True)
        
        # 获取所有子任务并尝试撤销
        file_statuses = get_batch_file_statuses(batch_id)
        cancelled_tasks = 0
        
        for file_status in file_statuses:
            task_id = file_status.get('task_id')
            if task_id:
                try:
                    subtask_result = create_transcription_task.AsyncResult(task_id)
                    subtask_result.revoke(terminate=True)
                    cancelled_tasks += 1
                except Exception as e:
                    logger.warning(f"Could not cancel subtask {task_id}: {e}")
        
        return {
            "message": f"Batch task cancelled. {cancelled_tasks} subtasks were cancelled.",
            "batch_id": batch_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling batch task: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
