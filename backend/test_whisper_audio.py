#!/usr/bin/env python3
"""
Test insanely-fast-whisper with a small test audio file
"""

import subprocess
import tempfile
import os
import json
from pathlib import Path
import wave
import struct
import math

def create_test_audio_file(duration_seconds=5, sample_rate=16000):
    """Create a simple test audio file with a sine wave"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_file.close()
    
    # Generate sine wave data
    frequency = 440  # A4 note
    frames = []
    for i in range(int(duration_seconds * sample_rate)):
        value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
        frames.append(struct.pack('<h', value))
    
    # Write WAV file
    with wave.open(temp_file.name, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b''.join(frames))
    
    print(f"Created test audio file: {temp_file.name}")
    print(f"File size: {os.path.getsize(temp_file.name)} bytes")
    return temp_file.name

def test_insanely_fast_whisper_with_audio():
    """Test insanely-fast-whisper with a real audio file"""
    
    # Create test audio file
    audio_file = create_test_audio_file(duration_seconds=3)
    
    # Create output directory
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    output_json = output_dir / "test_transcription.json"
    
    try:
        # Command to test
        cmd = [
            "insanely-fast-whisper",
            "--file-name", audio_file,
            "--model-name", "openai/whisper-tiny",  # Use tiny model for faster testing
            "--transcript-path", str(output_json),
            "--device-id", "mps",
            "--timestamp", "word",
            "--task", "transcribe"
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        
        # Run the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        print(f"Return code: {result.returncode}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        
        # Check if output file was created
        if output_json.exists():
            print(f"✓ Output file created: {output_json}")
            print(f"Output file size: {output_json.stat().st_size} bytes")
            
            # Try to read the JSON
            try:
                with open(output_json, 'r') as f:
                    data = json.load(f)
                print("✓ JSON is valid")
                print(f"Text content: {data.get('text', 'No text field')}")
                print(f"Available keys: {list(data.keys())}")
                
                if 'segments' in data:
                    print(f"Number of segments: {len(data['segments'])}")
                
            except json.JSONDecodeError as e:
                print(f"✗ JSON decode error: {e}")
                # Show raw content
                with open(output_json, 'r') as f:
                    content = f.read()
                print(f"Raw content: {content[:500]}...")
        else:
            print("✗ Output file was not created")
            
    except subprocess.TimeoutExpired:
        print("✗ Command timed out")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        # Cleanup
        try:
            os.unlink(audio_file)
            print(f"Cleaned up test audio file: {audio_file}")
        except:
            pass
        
        try:
            if output_json.exists():
                os.unlink(output_json)
                print(f"Cleaned up test output: {output_json}")
        except:
            pass

if __name__ == "__main__":
    test_insanely_fast_whisper_with_audio()
