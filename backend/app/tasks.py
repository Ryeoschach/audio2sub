import os
import json
import logging
from celery import Celery
from .config import settings
import ffmpeg
from pathlib import Path
from typing import Dict, Any, List
import time
from datetime import datetime, timedelta
import requests
from .whisper_manager import get_whisper_manager

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

def transcribe_with_whisper(audio_file_path: str, model_name: str = None, language: str = None, task_type: str = None) -> Dict[str, Any]:
    """
    Use OpenAI Whisper for transcription with optimized settings
    
    Args:
        audio_file_path: 音频文件路径
        model_name: 模型名称 (覆盖默认配置)
        language: 语言代码 (覆盖默认配置)
        task_type: 任务类型 (覆盖默认配置)
    """
    start_time = time.time()
    
    # 使用传入的参数或默认配置
    final_model_name = model_name or settings.MODEL_NAME
    final_language = language or settings.WHISPER_LANGUAGE
    final_task_type = task_type or settings.WHISPER_TASK
    
    try:
        logger.info(f"Starting transcription with OpenAI Whisper for {audio_file_path}")
        logger.info(f"Model: {final_model_name}, Language: {final_language}, Task: {final_task_type}")
        logger.info(f"Transcription started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get whisper manager and perform transcription with dynamic parameters
        whisper_manager = get_whisper_manager()
        result = whisper_manager.transcribe(
            audio_file_path, 
            model_name=final_model_name,
            language=final_language,
            task_type=final_task_type
        )
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        logger.info(f"Total processing time: {total_duration:.2f} seconds")
        
        # Update result with total timing
        result["total_processing_time"] = total_duration
        result["total_processing_time_formatted"] = str(timedelta(seconds=int(total_duration)))
        
        return result
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise

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

def generate_subtitles_from_segments(segments, srt_path: Path, vtt_path: Path):
    """Generate SRT and VTT files from segments with intelligent subtitle segmentation"""
    with open(srt_path, "w", encoding="utf-8") as srt_file, open(vtt_path, "w", encoding="utf-8") as vtt_file:
        vtt_file.write("WEBVTT\n\n")
        
        if not segments:
            logger.warning("No segments provided for subtitle generation")
            return
        
        segment_id = 1
        current_words = []
        segment_start_time = None
        
        logger.info(f"🎬 Generating subtitles with limits:")
        logger.info(f"   ⏱️ MAX_SUBTITLE_DURATION: {settings.MAX_SUBTITLE_DURATION}s")
        logger.info(f"   📝 MAX_WORDS_PER_SUBTITLE: {settings.MAX_WORDS_PER_SUBTITLE}")
        logger.info(f"   📏 MAX_CHARS_PER_SUBTITLE: {settings.MAX_CHARS_PER_SUBTITLE}")
        logger.info(f"   📊 Total segments to process: {len(segments)}")
        
        # Process each segment
        for i, segment in enumerate(segments):
            start_time = segment.get("start", 0.0)
            end_time = segment.get("end", start_time + 1.0)
            text = segment.get("text", "").strip()
            
            # Skip empty text
            if not text:
                continue
            
            # Initialize first segment
            if segment_start_time is None:
                segment_start_time = start_time
            
            # Split text into words if not already split
            if "words" in segment and segment["words"]:
                # Use word-level timestamps if available
                for word_info in segment["words"]:
                    word = word_info.get("word", "").strip()
                    if word:
                        current_words.append({
                            "word": word,
                            "start": word_info.get("start", start_time),
                            "end": word_info.get("end", end_time)
                        })
            else:
                # Split text into words with estimated timing
                words = text.split()
                word_duration = (end_time - start_time) / len(words) if words else 0
                
                for j, word in enumerate(words):
                    word_start = start_time + (j * word_duration)
                    word_end = start_time + ((j + 1) * word_duration)
                    current_words.append({
                        "word": word,
                        "start": word_start,
                        "end": word_end
                    })
            
            # Check if we should end current subtitle
            current_text = " ".join([w["word"] for w in current_words])
            segment_duration = current_words[-1]["end"] - segment_start_time if current_words else 0
            
            should_end_subtitle = False
            break_reason = ""
            
            # Time limit check
            if segment_duration >= settings.MAX_SUBTITLE_DURATION:
                should_end_subtitle = True
                break_reason = f"TIME_LIMIT ({segment_duration:.1f}s)"
            
            # Word count check
            elif len(current_words) >= settings.MAX_WORDS_PER_SUBTITLE:
                should_end_subtitle = True
                break_reason = f"WORD_LIMIT ({len(current_words)} words)"
            
            # Character count check
            elif len(current_text) >= settings.MAX_CHARS_PER_SUBTITLE:
                should_end_subtitle = True
                break_reason = f"CHAR_LIMIT ({len(current_text)} chars)"
            
            # Last segment check
            elif i == len(segments) - 1:
                should_end_subtitle = True
                break_reason = "LAST_SEGMENT"
            
            # Create subtitle entry
            if should_end_subtitle and current_words:
                segment_end_time = current_words[-1]["end"]
                actual_duration = segment_end_time - segment_start_time
                
                start_ts_str = format_timestamp(segment_start_time)
                end_ts_str = format_timestamp(segment_end_time)
                
                # Write SRT
                srt_file.write(f"{segment_id}\n{start_ts_str} --> {end_ts_str}\n{current_text}\n\n")
                
                # Write VTT
                vtt_file.write(f"{start_ts_str.replace(',', '.')} --> {end_ts_str.replace(',', '.')}\n{current_text}\n\n")
                
                logger.info(f"✅ Subtitle {segment_id}: {actual_duration:.1f}s, {len(current_words)}w, {len(current_text)}c - {break_reason}")
                
                # Reset for next segment
                segment_id += 1
                current_words = []
                segment_start_time = None
        
        total_generated = segment_id - 1
        logger.info(f"🎉 Generated {total_generated} subtitle entries")

def safe_update_state(self, state, meta=None):
    """Safe wrapper for update_state that works both in Celery and direct call contexts"""
    try:
        if hasattr(self, 'update_state') and hasattr(self, 'request') and self.request.id:
            self.update_state(state=state, meta=meta)
        else:
            logger.info(f"State update: {state} - {meta}")
    except Exception as e:
        logger.warning(f"Could not update state: {e}")

@celery_app.task(bind=True, name="app.tasks.create_transcription_task")
def create_transcription_task(self, input_filepath_str: str, file_id: str, original_filename: str, transcription_params: dict = None):
    """
    Process audio/video file and generate transcription with OpenAI Whisper
    
    Args:
        input_filepath_str: 输入文件路径
        file_id: 文件ID
        original_filename: 原始文件名
        transcription_params: 转录参数 {model, language, output_format, task}
    """
    # Record overall start time
    overall_start_time = time.time()
    start_datetime = datetime.now()
    
    # 处理转录参数，设置默认值
    if transcription_params is None:
        transcription_params = {}
    
    model_name = transcription_params.get("model", settings.MODEL_NAME)
    language = transcription_params.get("language", settings.WHISPER_LANGUAGE)
    output_format = transcription_params.get("output_format", "both")
    task_type = transcription_params.get("task", settings.WHISPER_TASK)
    
    logger.info(f"📁 Starting transcription task for file: {original_filename}")
    logger.info(f"🤖 Using model: {model_name}")
    logger.info(f"🌐 Language: {language}")
    logger.info(f"📄 Output format: {output_format}")
    logger.info(f"🎯 Task type: {task_type}")
    logger.info(f"🕐 Task started at: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🆔 File ID: {file_id}")
    
    input_filepath = Path(input_filepath_str)
    output_dir = RESULTS_DIR / file_id
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_file_to_transcribe = input_filepath
    temp_audio_path = None
    
    # Timing variables for different phases
    ffmpeg_time = 0
    transcription_time = 0
    subtitle_generation_time = 0
    
    try:
        safe_update_state(self, state='PROGRESS', meta={'status': 'Processing file...', 'progress': 10})
        
        # Handle video files - extract audio
        video_extensions = {'.mov', '.mp4', '.avi', '.mkv', '.webm', '.flv', '.wmv'}
        if input_filepath.suffix.lower() in video_extensions:
            ffmpeg_start = time.time()
            temp_audio_path = output_dir / f"{file_id}_extracted_audio.wav"
            try:
                logger.info(f"🎬 Extracting audio from video: {input_filepath}")
                
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
                ffmpeg_time = time.time() - ffmpeg_start
                logger.info(f"✅ Audio extraction completed in {ffmpeg_time:.2f} seconds")
                
            except Exception as e:
                error_msg = str(e.stderr.decode() if hasattr(e, 'stderr') and e.stderr else e)
                logger.error(f"FFmpeg Error for {original_filename}: {error_msg}")
                safe_update_state(self,
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
            safe_update_state(self,
                state='FAILURE', 
                meta={
                    'status': error_msg,
                    'exc_type': 'ValueError',
                    'exc_message': error_msg
                }
            )
            return
        
        safe_update_state(self, state='PROGRESS', meta={'status': f'Starting transcription with {model_name} model...', 'progress': 30})
        
        # Use OpenAI Whisper for transcription
        logger.info(f"🎙️ Starting transcription with model: {model_name}")
        transcription_data = transcribe_with_whisper(
            str(audio_file_to_transcribe),
            model_name=model_name,
            language=language,
            task_type=task_type
        )
        transcription_time = transcription_data.get("total_processing_time", 0)
        
        logger.info(f"✅ Transcription completed")
        safe_update_state(self, state='PROGRESS', meta={'status': 'Generating subtitles...', 'progress': 80})
        
        # Generate subtitle files based on requested format
        subtitle_start = time.time()
        generated_files = []
        
        # Extract segments from transcription data
        segments = transcription_data.get("segments", [])
        
        if output_format in ["srt", "both"]:
            srt_filename = f"{Path(original_filename).stem}.srt"
            srt_path = output_dir / srt_filename
            generated_files.append({"type": "srt", "filename": srt_filename, "path": str(srt_path)})
            logger.info(f"📄 Will generate SRT file: {srt_path}")
        
        if output_format in ["vtt", "both"]:
            vtt_filename = f"{Path(original_filename).stem}.vtt"
            vtt_path = output_dir / vtt_filename
            generated_files.append({"type": "vtt", "filename": vtt_filename, "path": str(vtt_path)})
            logger.info(f"📄 Will generate VTT file: {vtt_path}")
        
        # Generate the subtitle files using existing function
        if generated_files:
            # 确保 segments 不为空
            if not segments:
                # Fallback: create a single segment with full text
                full_text = transcription_data.get("text", "").strip()
                if full_text:
                    segments = [{
                        "text": full_text,
                        "start": 0.0,
                        "end": 30.0  # Assume 30 seconds for full text
                    }]
            
            if len(generated_files) == 2:  # both formats
                generate_subtitles_from_segments(segments, 
                    Path(generated_files[0]["path"]) if generated_files[0]["type"] == "srt" else Path(generated_files[1]["path"]),
                    Path(generated_files[1]["path"]) if generated_files[1]["type"] == "vtt" else Path(generated_files[0]["path"]))
            elif generated_files[0]["type"] == "srt":
                # Only SRT
                temp_vtt = output_dir / "temp.vtt"
                generate_subtitles_from_segments(segments, Path(generated_files[0]["path"]), temp_vtt)
                temp_vtt.unlink()  # Remove temp VTT file
            else:
                # Only VTT  
                temp_srt = output_dir / "temp.srt"
                generate_subtitles_from_segments(segments, temp_srt, Path(generated_files[0]["path"]))
                temp_srt.unlink()  # Remove temp SRT file
        subtitle_generation_time = time.time() - subtitle_start
        
        logger.info(f"✅ Subtitle generation completed in {subtitle_generation_time:.2f} seconds")
        for file_info in generated_files:
            logger.info(f"📄 {file_info['type'].upper()} saved to: {file_info['path']}")
        
        # Calculate total time and log summary
        total_time = time.time() - overall_start_time
        end_datetime = datetime.now()
        
        logger.info(f"🏁 Task completed at: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"⏱️  TIMING SUMMARY:")
        logger.info(f"   📁 File processing: {ffmpeg_time:.2f}s")
        logger.info(f"   🎙️  Transcription: {transcription_time:.2f}s")
        logger.info(f"   📄 Subtitle generation: {subtitle_generation_time:.2f}s")
        logger.info(f"   🎯 TOTAL TIME: {total_time:.2f}s ({timedelta(seconds=int(total_time))})")
        
        return {
            "status": "Completed",
            "files": generated_files,  # 动态生成的文件列表
            "original_filename": original_filename,
            "file_id": file_id,
            "full_text": transcription_data.get("text", ""),
            # 模型和参数信息
            "transcription_params": {
                "model": model_name,
                "language": language,
                "output_format": output_format,
                "task_type": task_type
            },
            # Timing information
            "timing": {
                "total_time": total_time,
                "total_time_formatted": str(timedelta(seconds=int(total_time))),
                "ffmpeg_time": ffmpeg_time,
                "transcription_time": transcription_time,
                "subtitle_generation_time": subtitle_generation_time,
                "start_time": start_datetime.isoformat(),
                "end_time": end_datetime.isoformat()
            }
        }
        
    except Exception as e:
        total_time = time.time() - overall_start_time
        logger.error(f"❌ Error during transcription for {original_filename} after {total_time:.2f} seconds: {e}", exc_info=True)
        safe_update_state(self,
            state='FAILURE', 
            meta={
                'status': f'Error: {str(e)}',
                'exc_type': type(e).__name__,
                'exc_message': str(e),
                'total_time': total_time
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