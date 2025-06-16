from celery_app import celery_app
from app.config import settings
from faster_whisper import WhisperModel
import ffmpeg
import os
from pathlib import Path

UPLOAD_DIR = Path("uploads")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Global model variable - will be initialized when needed
model = None

def get_whisper_model():
    """Lazy load the Whisper model to avoid segfault issues during import"""
    global model
    if model is None:
        try:
            print(f"Loading Whisper model: {settings.MODEL_NAME} on {settings.MODEL_DEVICE} with {settings.MODEL_COMPUTE_TYPE}")
            # Add timeout and more robust error handling
            import os
            os.environ['TOKENIZERS_PARALLELISM'] = 'false'  # Avoid tokenizers warning
            
            model = WhisperModel(
                settings.MODEL_NAME, 
                device=settings.MODEL_DEVICE, 
                compute_type=settings.MODEL_COMPUTE_TYPE,
                num_workers=1,  # Force single thread
                download_root=None,  # Use default cache location
                local_files_only=False  # Allow downloading if needed
            )
            print("Whisper model loaded successfully.")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to load Whisper model: {e}")
    return model 

def format_timestamp(seconds):
    """Converts seconds to SRT/VTT timestamp format HH:MM:SS,ms."""
    assert seconds >= 0, "non-negative timestamp"
    milliseconds = round(seconds * 1000.0)

    hours = milliseconds // 3_600_000
    milliseconds -= hours * 3_600_000

    minutes = milliseconds // 60_000
    milliseconds -= minutes * 60_000

    seconds = milliseconds // 1_000
    milliseconds -= seconds * 1_000

    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def safe_get_segment_data(segment):
    """Safely extract data from a segment object, handling various formats."""
    try:
        # Try to access attributes directly (faster-whisper format)
        if hasattr(segment, 'start') and hasattr(segment, 'end') and hasattr(segment, 'text'):
            return {
                'start': float(segment.start),
                'end': float(segment.end),
                'text': str(segment.text).strip()
            }
        # Try tuple format (some whisper implementations return tuples)
        elif isinstance(segment, (tuple, list)) and len(segment) >= 3:
            return {
                'start': float(segment[0]),
                'end': float(segment[1]),
                'text': str(segment[2]).strip()
            }
        # Try dictionary format
        elif isinstance(segment, dict):
            return {
                'start': float(segment.get('start', 0)),
                'end': float(segment.get('end', 1)),
                'text': str(segment.get('text', '[No text]')).strip()
            }
        else:
            print(f"Warning: Unknown segment format: {type(segment)}, {segment}")
            return {
                'start': 0,
                'end': 1,
                'text': '[Unknown segment format]'
            }
    except Exception as e:
        print(f"Error extracting segment data: {e}")
        return {
            'start': 0,
            'end': 1,
            'text': '[Error processing segment]'
        }

@celery_app.task(bind=True)
def create_transcription_task(self, input_filepath_str: str, file_id: str, original_filename: str):
    try:
        model = get_whisper_model()
    except Exception as e:
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e), 'status': 'Failed to load Whisper model'})
        raise e

    input_filepath = Path(input_filepath_str)
    output_dir = RESULTS_DIR / file_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define output paths for audio (if conversion needed) and subtitles
    # For video files, we need to extract audio first since faster-whisper may not handle video formats directly
    audio_file_to_transcribe = input_filepath
    temp_audio_path = None
    
    # Check if file is a video format that needs audio extraction
    video_extensions = {'.mov', '.mp4', '.avi', '.mkv', '.webm', '.flv', '.wmv'}
    if input_filepath.suffix.lower() in video_extensions:
        temp_audio_path = output_dir / f"{file_id}_extracted_audio.wav"
        try:
            print(f"Extracting audio from video: {input_filepath} to {temp_audio_path}")
            
            # First, probe the file to check if it has audio streams
            probe = ffmpeg.probe(str(input_filepath))
            audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
            
            if not audio_streams:
                # No audio streams found - this is likely a screen recording without audio
                print(f"Warning: No audio streams found in {input_filepath}")
                raise RuntimeError(f"The video file {original_filename} does not contain any audio tracks. Please upload a video with audio or an audio file directly.")
            
            print(f"Found {len(audio_streams)} audio stream(s) in the video")
            
            # Extract audio and convert to WAV format that faster-whisper can handle reliably
            (
                ffmpeg
                .input(str(input_filepath))
                .output(str(temp_audio_path), acodec='pcm_s16le', ar='16000', ac=1)
                .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
            )
            audio_file_to_transcribe = temp_audio_path
            print("Audio extraction successful")
        except Exception as e:
            # Handle ffmpeg-python errors more generally
            if hasattr(e, 'stderr') and e.stderr:
                error_msg = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
            else:
                error_msg = str(e)
            print(f"FFmpeg Error: {error_msg}")
            raise RuntimeError(f"Failed to extract audio from video file: {error_msg}")
    else:
        # For audio files, we might still want to convert to a standard format for better compatibility
        audio_extensions = {'.mp3', '.m4a', '.aac', '.ogg', '.flac'}
        if input_filepath.suffix.lower() in audio_extensions:
            temp_audio_path = output_dir / f"{file_id}_converted_audio.wav"
            try:
                print(f"Converting audio file: {input_filepath} to {temp_audio_path}")
                (
                    ffmpeg
                    .input(str(input_filepath))
                    .output(str(temp_audio_path), acodec='pcm_s16le', ar='16000', ac=1)
                    .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
                )
                audio_file_to_transcribe = temp_audio_path
                print("Audio conversion successful")
            except Exception as e:
                # Handle ffmpeg-python errors more generally
                if hasattr(e, 'stderr') and e.stderr:
                    error_msg = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
                else:
                    error_msg = str(e)
                print(f"FFmpeg Warning: {error_msg}. Proceeding with original file.")
                # For audio files, we can try to proceed with the original if conversion fails

    try:
        self.update_state(state='PROGRESS', meta={'status': 'Starting transcription...'})        
        
        # Check if audio file exists and is readable
        if not audio_file_to_transcribe.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_to_transcribe}")
        
        # Transcribe the audio file
        segments, info = model.transcribe(str(audio_file_to_transcribe), beam_size=5, word_timestamps=True)
        print(f"Transcription language: {info.language} with probability {info.language_probability:.2f}")
        self.update_state(state='PROGRESS', meta={'status': 'Transcription complete, generating subtitles...'}) 

        # Convert segments to list to handle them safely
        segments_list = list(segments)
        
        if not segments_list:
            print("Warning: No segments found in transcription")
            # Create empty subtitle files
            srt_filename = f"{Path(original_filename).stem}.srt"
            srt_path = output_dir / srt_filename
            with open(srt_path, "w", encoding="utf-8") as srt_file:
                srt_file.write("1\n00:00:00,000 --> 00:00:01,000\n[No speech detected]\n\n")
            
            vtt_filename = f"{Path(original_filename).stem}.vtt"
            vtt_path = output_dir / vtt_filename
            with open(vtt_path, "w", encoding="utf-8") as vtt_file:
                vtt_file.write("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\n[No speech detected]\n\n")
        else:
            # Generate SRT
            srt_filename = f"{Path(original_filename).stem}.srt"
            srt_path = output_dir / srt_filename
            with open(srt_path, "w", encoding="utf-8") as srt_file:
                for i, segment in enumerate(segments_list):
                    segment_data = safe_get_segment_data(segment)
                    start_time = segment_data['start']
                    end_time = segment_data['end']
                    text = segment_data['text']
                    
                    srt_file.write(str(i + 1) + "\n")
                    srt_file.write(f"{format_timestamp(start_time)} --> {format_timestamp(end_time)}\n")
                    srt_file.write(text + "\n\n")
            print(f"SRT file saved to {srt_path}")

            # Generate VTT (similar to SRT but with a different header and dot for ms separator)
            vtt_filename = f"{Path(original_filename).stem}.vtt"
            vtt_path = output_dir / vtt_filename
            with open(vtt_path, "w", encoding="utf-8") as vtt_file:
                vtt_file.write("WEBVTT\n\n")
                for i, segment in enumerate(segments_list):
                    segment_data = safe_get_segment_data(segment)
                    start_time = segment_data['start']
                    end_time = segment_data['end']
                    text = segment_data['text']
                    
                    vtt_file.write(f"{format_timestamp(start_time).replace(',', '.')} --> {format_timestamp(end_time).replace(',', '.')}\n")
                    vtt_file.write(text + "\n\n")
            print(f"VTT file saved to {vtt_path}")

        # Clean up uploaded file and temporary audio file if created
        if input_filepath.exists():
            os.remove(input_filepath)
        if temp_audio_path and temp_audio_path.exists() and temp_audio_path != input_filepath:
            os.remove(temp_audio_path)

        return {
            "message": "Transcription successful", 
            "original_filename": original_filename,
            "file_id": file_id,
            "srt_path": str(srt_filename), # relative to results/file_id/
            "vtt_path": str(vtt_filename)  # relative to results/file_id/
        }

    except Exception as e:
        # Log error, clean up, etc.
        print(f"Error during transcription task for {input_filepath_str}: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        # Clean up uploaded file if an error occurs
        if input_filepath.exists():
            try:
                os.remove(input_filepath)
            except OSError as rm_err:
                print(f"Error removing file {input_filepath} during cleanup: {rm_err}")
        
        # Clean up temporary audio file if it exists
        if 'temp_audio_path' in locals() and temp_audio_path and temp_audio_path.exists() and temp_audio_path != input_filepath:
            try:
                os.remove(temp_audio_path)
            except OSError as rm_err:
                print(f"Error removing temp audio file {temp_audio_path} during cleanup: {rm_err}")
        
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e), 'status': 'Transcription failed'})        
        raise # Re-raise the exception so Celery marks it as failed
