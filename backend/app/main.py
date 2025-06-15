from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
from pathlib import Path

from .config import settings
from .tasks import create_transcription_task
# from . import utils # Placeholder for ffmpeg and other utilities

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

@app.get("/ping")
async def ping():
    return {"ping": "pong!"}

@app.post("/upload/", tags=["Transcription"])
async def upload_file_for_transcription(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
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

    # Create a task for Celery
    task = create_transcription_task.delay(str(file_path), file_id, original_filename)

    return JSONResponse(
        status_code=202,
        content={"task_id": task.id, "file_id": file_id, "message": "File uploaded, transcription started."}
    )

@app.get("/status/{task_id}", tags=["Transcription"])
async def get_task_status(task_id: str):
    task_result = create_transcription_task.AsyncResult(task_id)
    if task_result.state == 'PENDING':
        response = {
            'state': task_result.state,
            'status': 'Pending...'
        }
    elif task_result.state == 'FAILURE':
        response = {
            'state': task_result.state,
            'status': str(task_result.info),  # This is the exception raised
        }
    elif task_result.state == 'SUCCESS':
        response = {
            'state': task_result.state,
            'status': 'Completed',
            'result': task_result.result # This will contain { "transcript_path": "...", "original_filename": "..." }
        }
    else:
        response = {
            'state': task_result.state,
            'status': str(task_result.info), # e.g. PROGRESS
        }
    return response

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

# Placeholder for WebSocket endpoint for real-time progress (optional)
# @app.websocket("/ws/progress/{task_id}")
# async def websocket_progress(websocket: WebSocket, task_id: str):
#     await websocket.accept()
#     # Logic to send progress updates
#     await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
