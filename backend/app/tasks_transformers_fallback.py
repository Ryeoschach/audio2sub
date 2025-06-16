import os
import json
import logging
from celery import Celery
from .config import settings
import ffmpeg
from pathlib import Path
import torch
from transformers import pipeline, AutoProcessor, AutoModelForSpeechSeq2Seq
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import celery_app from the celery_app.py file
try:
    from celery_app import celery_app
except ImportError:
    logger.warning("Could not import celery_app directly, creating fallback")
    celery_app = Celery(
        "tasks_fallback",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
RESULTS_DIR = Path(settings.RESULTS_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Global model cache
_whisper_pipeline = None

def get_whisper_pipeline():
    """Get or create the Whisper pipeline"""
    global _whisper_pipeline
    if _whisper_pipeline is None:
        try:
            logger.info(f"Loading Whisper model: {settings.MODEL_NAME}")
            
            # Determine device and dtype
            device = "cpu"  # Start with CPU for stability
            torch_dtype = torch.float32
            
            # Check if MPS is available and working
            if torch.backends.mps.is_available() and torch.backends.mps.is_built():
                try:
                    # Test MPS with a simple operation
                    test_tensor = torch.tensor([1.0]).to("mps")
                    device = "mps"
                    torch_dtype = torch.float16
                    logger.info("Using MPS device")
                except Exception as e:
                    logger.warning(f"MPS test failed, falling back to CPU: {e}")
                    device = "cpu"
                    torch_dtype = torch.float32
            else:
                logger.info("MPS not available, using CPU")
            
            _whisper_pipeline = pipeline(
                "automatic-speech-recognition",
                model=settings.MODEL_NAME,
                torch_dtype=torch_dtype,
                device=device,
                model_kwargs={"attn_implementation": "eager"}  # Use eager attention for stability
            )
            logger.info(f"Whisper pipeline loaded successfully on {device}")
        except Exception as e:
            logger.error(f"Failed to load Whisper pipeline: {e}")
            raise RuntimeError(f"Could not load Whisper model: {e}")
    
    return _whisper_pipeline

def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format"""
    assert seconds >= 0, "non-negative timestamp expected"
    milliseconds = round(seconds * 1000.0)
    hours = milliseconds // 3_600_000
    milliseconds -= hours * 3_600_000
    minutes = milliseconds // 60_000
    milliseconds -= minutes * 60_000
    seconds_val = milliseconds // 1_000
    milliseconds -= seconds_val * 1_000
    return f"{hours:02d}:{minutes:02d}:{seconds_val:02d},{milliseconds:03d}"

def transcribe_with_transformers(audio_file_path: str) -> Dict[str, Any]:
    """
    Use transformers pipeline directly for transcription
    """
    try:
        logger.info(f"Starting transcription with transformers pipeline for {audio_file_path}")
        pipeline_instance = get_whisper_pipeline()
        
        result = pipeline_instance(
            audio_file_path,
            chunk_length_s=30,
            stride_length_s=5,
            return_timestamps=True,
            generate_kwargs={"language": None, "task": "transcribe"}  # Auto-detect language
        )
        
        logger.info("Transcription completed successfully")
        
        # Format result to match expected structure
        formatted_result = {
            "text": result.get("text", ""),
            "segments": []
        }
        
        # Convert chunks to segments
        if "chunks" in result:
            for i, chunk in enumerate(result["chunks"]):
                timestamp = chunk.get("timestamp", [0, 1])
                start_time = timestamp[0] if timestamp[0] is not None else 0
                end_time = timestamp[1] if timestamp[1] is not None else start_time + 1
                
                formatted_result["segments"].append({
                    "word": chunk.get("text", "").strip(),
                    "start": start_time,
                    "end": end_time
                })
        
        return formatted_result
        
    except Exception as e:
        logger.error(f"Error in transformers transcription: {e}")
        raise RuntimeError(f"Transcription failed: {str(e)}")

def generate_subtitles_from_segments(segments, srt_path: Path, vtt_path: Path):
    """Generate SRT and VTT files from segments"""
    with open(srt_path, "w", encoding="utf-8") as srt_file, open(vtt_path, "w", encoding="utf-8") as vtt_file:
        vtt_file.write("WEBVTT\n\n")
        
        if not segments:
            logger.warning("No segments provided for subtitle generation")
            return
        
        segment_id = 1
        current_segment_text = ""
        current_start = None
        
        # Group words into sentences/segments for better readability
        for i, segment in enumerate(segments):
            word = segment.get("word", "").strip()
            start_time = segment.get("start", 0.0)
            end_time = segment.get("end", start_time + 0.1)
            
            if current_start is None:
                current_start = start_time
            
            current_segment_text += word + " "
            
            # Create a new segment every ~10 words or at sentence end
            should_break = (
                len(current_segment_text.split()) >= 10 or 
                word.endswith(('.', '!', '?')) or
                i == len(segments) - 1  # Last segment
            )
            
            if should_break and current_segment_text.strip():
                start_ts_str = format_timestamp(current_start)
                end_ts_str = format_timestamp(end_time)
                
                # Write SRT
                srt_file.write(f"{segment_id}\n{start_ts_str} --> {end_ts_str}\n{current_segment_text.strip()}\n\n")
                
                # Write VTT
                vtt_file.write(f"{start_ts_str.replace(',', '.')} --> {end_ts_str.replace(',', '.')}\n{current_segment_text.strip()}\n\n")
                
                # Reset for next segment
                segment_id += 1
                current_segment_text = ""
                current_start = None

@celery_app.task(bind=True, name="app.tasks.create_transcription_task")
def create_transcription_task(self, input_filepath_str: str, file_id: str, original_filename: str):
    """
    Process audio/video file and generate transcription using transformers pipeline (fallback method)
    """
    input_filepath = Path(input_filepath_str)
    output_dir = RESULTS_DIR / file_id
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_file_to_transcribe = input_filepath
    temp_audio_path = None
    
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Processing file...', 'progress': 10})
        
        # Handle video files - extract audio
        video_extensions = {'.mov', '.mp4', '.avi', '.mkv', '.webm', '.flv', '.wmv'}
        if input_filepath.suffix.lower() in video_extensions:
            temp_audio_path = output_dir / f"{file_id}_extracted_audio.wav"
            try:
                logger.info(f"Extracting audio from {input_filepath} to {temp_audio_path}")
                
                # Check if video has audio tracks
                probe = ffmpeg.probe(str(input_filepath))
                if not any(stream['codec_type'] == 'audio' for stream in probe.get('streams', [])):
                    raise RuntimeError(f"Video file {original_filename} has no audio tracks.")
                
                # Extract audio
                (
                    ffmpeg
                    .input(str(input_filepath))
                    .output(str(temp_audio_path), acodec='pcm_s16le', ar='16000', ac=1)
                    .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
                )
                audio_file_to_transcribe = temp_audio_path
                logger.info("Audio extraction successful.")
                
            except Exception as e:
                error_msg = str(e.stderr.decode() if hasattr(e, 'stderr') and e.stderr else e)
                logger.error(f"FFmpeg Error for {original_filename}: {error_msg}")
                self.update_state(
                    state='FAILURE', 
                    meta={
                        'status': f'FFmpeg error: {error_msg}',
                        'exc_type': type(e).__name__,
                        'exc_message': str(e)
                    }
                )
                return
        
        # Check if it's an audio file
        audio_extensions = {'.wav', '.mp3', '.flac', '.m4a', '.aac', '.ogg', '.wma'}
        if input_filepath.suffix.lower() not in audio_extensions and temp_audio_path is None:
            error_msg = f"Unsupported file format: {input_filepath.suffix}"
            logger.error(error_msg)
            self.update_state(
                state='FAILURE', 
                meta={
                    'status': error_msg,
                    'exc_type': 'ValueError',
                    'exc_message': error_msg
                }
            )
            return
        
        self.update_state(state='PROGRESS', meta={'status': 'Starting transcription...', 'progress': 30})
        
        # Use transformers pipeline for transcription
        logger.info(f"Transcribing {audio_file_to_transcribe} with {settings.MODEL_NAME}")
        transcription_data = transcribe_with_transformers(str(audio_file_to_transcribe))
        
        logger.info(f"Transcription complete for {audio_file_to_transcribe}")
        self.update_state(state='PROGRESS', meta={'status': 'Generating subtitles...', 'progress': 80})
        
        # Generate subtitle files
        srt_filename = f"{Path(original_filename).stem}.srt"
        srt_path = output_dir / srt_filename
        vtt_filename = f"{Path(original_filename).stem}.vtt"
        vtt_path = output_dir / vtt_filename
        
        # Extract segments from transcription data
        segments = transcription_data.get("segments", [])
        if not segments:
            # Fallback: create a single segment with full text
            full_text = transcription_data.get("text", "").strip()
            if full_text:
                segments = [{
                    "word": full_text,
                    "start": 0.0,
                    "end": 30.0  # Assume 30 seconds for full text
                }]
        
        generate_subtitles_from_segments(segments, srt_path, vtt_path)
        
        logger.info(f"SRT saved to {srt_path}, VTT saved to {vtt_path}")
        
        return {
            "status": "Completed",
            "srt_path": str(srt_filename),
            "vtt_path": str(vtt_filename),
            "original_filename": original_filename,
            "file_id": file_id,
            "full_text": transcription_data.get("text", "")
        }
        
    except Exception as e:
        logger.error(f"Error during transcription for {original_filename}: {e}", exc_info=True)
        self.update_state(
            state='FAILURE', 
            meta={
                'status': f'Error: {str(e)}',
                'exc_type': type(e).__name__,
                'exc_message': str(e)
            }
        )
        raise
    finally:
        # Clean up temporary files
        cleanup_files = []
        if temp_audio_path and temp_audio_path.exists():
            cleanup_files.append(temp_audio_path)
        if input_filepath.exists():
            cleanup_files.append(input_filepath)
        
        for file_path in cleanup_files:
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Could not clean up {file_path}: {cleanup_error}")
