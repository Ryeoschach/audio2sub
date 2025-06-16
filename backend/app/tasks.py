import os
import json
import logging
from celery import Celery
from .config import settings
import ffmpeg
from pathlib import Path
import torch
from transformers import pipeline
from typing import Dict, Any
import warnings
import time
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress specific transformers warnings
warnings.filterwarnings("ignore", message="The input name `inputs` is deprecated")
warnings.filterwarnings("ignore", message="You have passed task=transcribe, but also have set `forced_decoder_ids`")
warnings.filterwarnings("ignore", message="The attention mask is not set and cannot be inferred")

# Set environment variables to reduce warnings
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

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
    """Get or create the Whisper pipeline with better error handling"""
    global _whisper_pipeline
    if _whisper_pipeline is None:
        try:
            logger.info(f"Loading Whisper model: {settings.MODEL_NAME}")
            
            # Start with CPU for stability, test MPS if available
            device = "cpu"
            torch_dtype = torch.float32
            
            # Check MPS availability and test it
            if torch.backends.mps.is_available() and torch.backends.mps.is_built():
                try:
                    # Test MPS with a simple operation
                    test_tensor = torch.tensor([1.0]).to("mps")
                    del test_tensor
                    device = "mps"
                    torch_dtype = torch.float16
                    logger.info("MPS is available and working, using MPS device")
                except Exception as e:
                    logger.warning(f"MPS test failed, falling back to CPU: {e}")
                    device = "cpu"
                    torch_dtype = torch.float32
            else:
                logger.info("MPS not available, using CPU")
            
            logger.info(f"Creating pipeline with device: {device}, dtype: {torch_dtype}")
            
            # Try to create pipeline with minimal parameters first
            try:
                _whisper_pipeline = pipeline(
                    "automatic-speech-recognition",
                    model=settings.MODEL_NAME,
                    torch_dtype=torch_dtype,
                    device=device,
                    model_kwargs={
                        "attn_implementation": "eager",  # Use eager attention for stability
                    },
                )
                logger.info(f"✅ Whisper pipeline loaded successfully on {device}")
            except Exception as pipeline_error:
                logger.warning(f"Failed to load pipeline with advanced options: {pipeline_error}")
                logger.info("Trying with basic configuration...")
                
                # Fallback to very basic configuration
                _whisper_pipeline = pipeline(
                    "automatic-speech-recognition",
                    model=settings.MODEL_NAME,
                    torch_dtype=torch_dtype,
                    device=device,
                )
                logger.info(f"✅ Whisper pipeline loaded with basic config on {device}")
            
            logger.info(f"Performance settings - Batch size: {settings.BATCH_SIZE}, Chunk: {settings.CHUNK_LENGTH_S}s, Stride: {settings.STRIDE_LENGTH_S}s")
        except Exception as e:
            logger.error(f"Failed to load Whisper pipeline: {e}")
            raise RuntimeError(f"Could not load Whisper model: {e}")
    
    return _whisper_pipeline

def transcribe_with_transformers(audio_file_path: str) -> Dict[str, Any]:
    """
    Use transformers pipeline directly for transcription with optimized settings
    """
    start_time = time.time()
    transcription_start_time = None
    
    try:
        logger.info(f"Starting transcription with transformers pipeline for {audio_file_path}")
        logger.info(f"Transcription started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        pipeline_instance = get_whisper_pipeline()
        
        # Validate parameters to avoid range() errors
        batch_size = max(1, settings.BATCH_SIZE)  # Ensure batch_size is at least 1
        chunk_length_s = max(10, settings.CHUNK_LENGTH_S)  # Ensure minimum chunk length
        stride_length_s = min(chunk_length_s - 1, max(1, settings.STRIDE_LENGTH_S))  # Ensure stride is valid
        
        logger.info(f"Using validated parameters - Batch size: {batch_size}, Chunk: {chunk_length_s}s, Stride: {stride_length_s}s")
        
        # Record transcription start time
        transcription_start_time = time.time()
        
        # Try with optimized settings - start with chunk-level timestamps which are more reliable
        try:
            result = pipeline_instance(
                audio_file_path,
                batch_size=batch_size,
                chunk_length_s=chunk_length_s,
                stride_length_s=stride_length_s,
                return_timestamps=True,  # Use chunk-level timestamps (more reliable)
                generate_kwargs={
                    "language": None,  # Auto-detect language
                    "task": "transcribe",
                    "num_beams": 1,  # Use greedy decoding for speed
                    "do_sample": False,  # Disable sampling for deterministic results
                }
            )
        except Exception as batch_error:
            logger.warning(f"Batch processing failed: {batch_error}")
            logger.info("Falling back to simplest parameters")
            
            # Fallback to simplest parameters
            result = pipeline_instance(
                audio_file_path,
                batch_size=1,  # Use single batch
                chunk_length_s=30,  # Fixed chunk length
                stride_length_s=5,   # Fixed stride
                return_timestamps=True,
                generate_kwargs={
                    "task": "transcribe",
                    "do_sample": False,
                }
            )
        
        # Calculate timing
        transcription_end_time = time.time()
        transcription_duration = transcription_end_time - transcription_start_time
        
        logger.info(f"Transcription completed successfully")
        logger.info(f"Transcription duration: {transcription_duration:.2f} seconds ({timedelta(seconds=int(transcription_duration))})")
        
        # Format result to match expected structure
        formatted_result = {
            "text": result.get("text", ""),
            "segments": [],
            "transcription_time": transcription_duration,
            "transcription_time_formatted": str(timedelta(seconds=int(transcription_duration)))
        }
        
        # Convert chunks to word-level segments with proper timing
        if "chunks" in result:
            logger.info(f"Processing {len(result['chunks'])} chunks")
            for i, chunk in enumerate(result["chunks"]):
                timestamp = chunk.get("timestamp", [0, 1])
                start_time = timestamp[0] if timestamp[0] is not None else 0
                end_time = timestamp[1] if timestamp[1] is not None else start_time + 1
                text = chunk.get("text", "").strip()
                
                # Split chunk text into words and create individual word segments
                if text:
                    words = text.split()
                    chunk_duration = end_time - start_time
                    
                    # Ensure minimum duration per word (0.1 seconds)
                    min_duration_per_word = 0.1
                    total_min_duration = len(words) * min_duration_per_word
                    
                    if chunk_duration < total_min_duration:
                        chunk_duration = total_min_duration
                        end_time = start_time + chunk_duration
                    
                    # Distribute time evenly across words
                    time_per_word = chunk_duration / len(words) if len(words) > 0 else 1.0
                    
                    for j, word in enumerate(words):
                        word_start = start_time + (j * time_per_word)
                        word_end = start_time + ((j + 1) * time_per_word)
                        
                        formatted_result["segments"].append({
                            "word": word,
                            "start": word_start,
                            "end": word_end
                        })
        else:
            # Fallback: create segments from full text with estimated timing
            full_text = result.get("text", "").strip()
            logger.info(f"No chunks found, processing full text (length: {len(full_text)})")
            if full_text:
                words = full_text.split()
                # Use a reasonable speaking rate: about 2.5 words per second
                words_per_second = 2.5
                
                for i, word in enumerate(words):
                    start_time = i / words_per_second
                    end_time = (i + 1) / words_per_second
                    
                    formatted_result["segments"].append({
                        "word": word,
                        "start": start_time,
                        "end": end_time
                    })
        
        logger.info(f"Created {len(formatted_result['segments'])} segments")
        
        # Calculate total processing time
        total_time = time.time() - start_time
        formatted_result["total_processing_time"] = total_time
        formatted_result["total_processing_time_formatted"] = str(timedelta(seconds=int(total_time)))
        
        logger.info(f"Total processing time: {total_time:.2f} seconds ({timedelta(seconds=int(total_time))})")
        
        return formatted_result
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"Error in transformers transcription after {total_time:.2f} seconds: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise RuntimeError(f"Transcription failed: {str(e)}")

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
        
        logger.info(f"Generating subtitles with limits: {settings.MAX_SUBTITLE_DURATION}s, {settings.MAX_WORDS_PER_SUBTITLE} words, {settings.MAX_CHARS_PER_SUBTITLE} chars")
        
        # Process each word
        for i, segment in enumerate(segments):
            word = segment.get("word", "").strip()
            start_time = segment.get("start", 0.0)
            end_time = segment.get("end", start_time + 0.1)
            
            # Skip empty words
            if not word:
                continue
            
            # Initialize first segment
            if segment_start_time is None:
                segment_start_time = start_time
            
            # Add word to current segment
            current_words.append({
                "word": word,
                "start": start_time,
                "end": end_time
            })
            
            # Build current text
            current_text = " ".join([w["word"] for w in current_words])
            
            # Calculate current segment duration
            segment_duration = end_time - segment_start_time
            
            # Check if we should end this subtitle
            should_end_subtitle = False
            
            # 1. Time limit reached
            if segment_duration >= settings.MAX_SUBTITLE_DURATION:
                should_end_subtitle = True
            
            # 2. Word count limit reached
            elif len(current_words) >= settings.MAX_WORDS_PER_SUBTITLE:
                should_end_subtitle = True
            
            # 3. Character count limit reached
            elif len(current_text) >= settings.MAX_CHARS_PER_SUBTITLE:
                should_end_subtitle = True
            
            # 4. Natural sentence break (but ensure minimum 2 words)
            elif word.endswith(('.', '!', '?')) and len(current_words) >= 2:
                should_end_subtitle = True
            
            # 5. Last word
            elif i == len(segments) - 1:
                should_end_subtitle = True
            
            # Create subtitle entry
            if should_end_subtitle and current_words:
                segment_end_time = current_words[-1]["end"]
                
                start_ts_str = format_timestamp(segment_start_time)
                end_ts_str = format_timestamp(segment_end_time)
                
                # Write SRT
                srt_file.write(f"{segment_id}\n{start_ts_str} --> {end_ts_str}\n{current_text}\n\n")
                
                # Write VTT
                vtt_file.write(f"{start_ts_str.replace(',', '.')} --> {end_ts_str.replace(',', '.')}\n{current_text}\n\n")
                
                # Log for debugging
                logger.debug(f"Subtitle {segment_id}: {segment_duration:.1f}s, {len(current_words)} words, {len(current_text)} chars")
                
                # Reset for next segment
                segment_id += 1
                current_words = []
                segment_start_time = None
        
        logger.info(f"Generated {segment_id - 1} subtitle entries")

@celery_app.task(bind=True, name="app.tasks.create_transcription_task")
def create_transcription_task(self, input_filepath_str: str, file_id: str, original_filename: str):
    """
    Process audio/video file and generate transcription with detailed timing information
    """
    # Record overall start time
    overall_start_time = time.time()
    start_datetime = datetime.now()
    
    logger.info(f"📁 Starting transcription task for file: {original_filename}")
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
        self.update_state(state='PROGRESS', meta={'status': 'Processing file...', 'progress': 10})
        
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
        logger.info(f"🎙️ Starting transcription with model: {settings.MODEL_NAME}")
        transcription_data = transcribe_with_transformers(str(audio_file_to_transcribe))
        transcription_time = transcription_data.get("total_processing_time", 0)
        
        logger.info(f"✅ Transcription completed")
        self.update_state(state='PROGRESS', meta={'status': 'Generating subtitles...', 'progress': 80})
        
        # Generate subtitle files
        subtitle_start = time.time()
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
        subtitle_generation_time = time.time() - subtitle_start
        
        logger.info(f"✅ Subtitle generation completed in {subtitle_generation_time:.2f} seconds")
        logger.info(f"📄 SRT saved to: {srt_path}")
        logger.info(f"📄 VTT saved to: {vtt_path}")
        
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
            "srt_path": str(srt_filename),
            "vtt_path": str(vtt_filename),
            "original_filename": original_filename,
            "file_id": file_id,
            "full_text": transcription_data.get("text", ""),
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
        self.update_state(
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
