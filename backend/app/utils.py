# Utility functions, e.g., for interacting with FFmpeg more directly if needed,
# or other helper functions for audio processing, file management, etc.

import ffmpeg
from pathlib import Path

def convert_to_standard_audio(input_path: Path, output_path: Path, audio_codec: str = 'pcm_s16le', audio_bitrate: str = '16000', audio_channels: int = 1):
    """
    Converts an input audio/video file to a standard audio format (e.g., WAV) using FFmpeg.
    Args:
        input_path: Path to the input file.
        output_path: Path to save the converted audio file.
        audio_codec: Target audio codec (e.g., 'pcm_s16le' for WAV, 'libmp3lame' for MP3).
        audio_bitrate: Target audio sample rate (e.g., '16000' for 16kHz).
        audio_channels: Target number of audio channels (e.g., 1 for mono).
    Returns:
        True if conversion was successful, False otherwise.
    Raises:
        ffmpeg.Error if FFmpeg encounters an error.
    """
    try:
        print(f"Attempting to convert {input_path} to {output_path}...")
        (   ffmpeg
            .input(str(input_path))
            .output(str(output_path), acodec=audio_codec, ar=audio_bitrate, ac=audio_channels)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        print(f"Successfully converted {input_path} to {output_path}")
        return True
    except ffmpeg.Error as e:
        stderr = e.stderr.decode('utf8') if e.stderr else 'No stderr'
        print(f"FFmpeg error during conversion of {input_path}:")
        print(f"Stdout: {e.stdout.decode('utf8') if e.stdout else 'No stdout'}")
        print(f"Stderr: {stderr}")
        # raise  # Re-raise the exception to be handled by the caller
        return False # Or return False to indicate failure

# Example usage (you would call this from your tasks.py or main.py):
# if __name__ == '__main__':
#     # Create dummy files for testing
#     Path("test_uploads").mkdir(exist_ok=True)
#     Path("test_outputs").mkdir(exist_ok=True)
#     dummy_input = Path("test_uploads/dummy.mp4")
#     # Create a small dummy mp4 or audio file here for testing if needed
#     # For example, using ffmpeg command line: 
#     # ffmpeg -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 -t 5 test_uploads/dummy.mp4
#     # Ensure you have a file to test with.
#     if dummy_input.exists():
#         converted_output = Path("test_outputs/dummy_converted.wav")
#         success = convert_to_standard_audio(dummy_input, converted_output)
#         if success:
#             print(f"Test conversion successful: {converted_output}")
#         else:
#             print("Test conversion failed.")
#     else:
#         print(f"Test input file {dummy_input} not found. Skipping conversion test.")
