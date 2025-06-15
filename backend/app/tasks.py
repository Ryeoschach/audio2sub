from celery_app import celery_app
from app.config import settings
from faster_whisper import WhisperModel
import ffmpeg
import os
from pathlib import Path

UPLOAD_DIR = Path("uploads")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Initialize Whisper Model (can be done once when worker starts)
# This might be better placed in a worker initialization signal for Celery
# For simplicity, loading it here. Ensure model is downloaded or available.
try:
    print(f"Loading Whisper model: {settings.MODEL_NAME} on {settings.MODEL_DEVICE} with {settings.MODEL_COMPUTE_TYPE}")
    model = WhisperModel(settings.MODEL_NAME, device=settings.MODEL_DEVICE, compute_type=settings.MODEL_COMPUTE_TYPE)
    print("Whisper model loaded successfully.")
except Exception as e:
    print(f"Error loading Whisper model: {e}")
    # Fallback or raise critical error if model is essential
    model = None 

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

@celery_app.task(bind=True)
def create_transcription_task(self, input_filepath_str: str, file_id: str, original_filename: str):
    if model is None:
        raise RuntimeError("Whisper model is not loaded. Cannot process transcription.")

    input_filepath = Path(input_filepath_str)
    output_dir = RESULTS_DIR / file_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define output paths for audio (if conversion needed) and subtitles
    # For simplicity, we'll assume ffmpeg handles various inputs directly for Whisper
    # or that Whisper/faster-whisper can handle common formats.
    # A more robust solution would explicitly convert to a standard format like .wav or .mp3 first.
    audio_file_to_transcribe = input_filepath

    # Example: Convert to WAV if needed (and if ffmpeg is correctly set up)
    # temp_audio_path = output_dir / f"{file_id}_processed.wav"
    # try:
    #     print(f"Converting {input_filepath} to {temp_audio_path}")
    #     ffmpeg.input(str(input_filepath)).output(str(temp_audio_path), acodec='pcm_s16le', ar='16000', ac=1).run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
    #     audio_file_to_transcribe = temp_audio_path
    #     print("Conversion successful")
    # except ffmpeg.Error as e:
    #     print("FFmpeg Error:", e.stderr.decode() if e.stderr else "Unknown FFmpeg error")
    #     # Decide if to proceed with original or raise error
    #     # For now, we'll try to proceed with the original file if conversion fails
    #     if not audio_file_to_transcribe.exists(): # if original was meant to be replaced
    #          raise e # Re-raise if conversion was critical and failed

    try:
        self.update_state(state='PROGRESS', meta={'status': 'Starting transcription...'})        
        segments, info = model.transcribe(str(audio_file_to_transcribe), beam_size=5, word_timestamps=True)
        print(f"Transcription language: {info.language} with probability {info.language_probability:.2f}")
        self.update_state(state='PROGRESS', meta={'status': 'Transcription complete, generating subtitles...'}) 

        # Generate SRT
        srt_filename = f"{Path(original_filename).stem}.srt"
        srt_path = output_dir / srt_filename
        with open(srt_path, "w", encoding="utf-8") as srt_file:
            for i, segment in enumerate(segments):
                srt_file.write(str(i + 1) + "\n")
                srt_file.write(f"{format_timestamp(segment.start)} --> {format_timestamp(segment.end)}\n")
                srt_file.write(segment.text.strip() + "\n\n")
        print(f"SRT file saved to {srt_path}")

        # Generate VTT (similar to SRT but with a different header and dot for ms separator)
        vtt_filename = f"{Path(original_filename).stem}.vtt"
        vtt_path = output_dir / vtt_filename
        with open(vtt_path, "w", encoding="utf-8") as vtt_file:
            vtt_file.write("WEBVTT\n\n")
            for i, segment in enumerate(segments):
                vtt_file.write(f"{format_timestamp(segment.start).replace(',', '.')} --> {format_timestamp(segment.end).replace(',', '.')}\n")
                vtt_file.write(segment.text.strip() + "\n\n")
        print(f"VTT file saved to {vtt_path}")

        # Clean up uploaded file and temporary audio file if created
        if input_filepath.exists():
            os.remove(input_filepath)
        # if audio_file_to_transcribe != input_filepath and audio_file_to_transcribe.exists():
        #     os.remove(audio_file_to_transcribe)

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
        # Clean up uploaded file if an error occurs
        if input_filepath.exists():
            try:
                os.remove(input_filepath)
            except OSError as rm_err:
                print(f"Error removing file {input_filepath} during cleanup: {rm_err}")
        # if audio_file_to_transcribe != input_filepath and audio_file_to_transcribe.exists():
        #     try:
        #         os.remove(audio_file_to_transcribe)
        #     except OSError as rm_err:
        #         print(f"Error removing temp audio file {audio_file_to_transcribe} during cleanup: {rm_err}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e), 'status': 'Transcription failed'})        
        raise # Re-raise the exception so Celery marks it as failed
