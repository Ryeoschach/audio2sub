#!/usr/bin/env python3
"""
Test the complete transcription workflow
"""

import subprocess
import tempfile
import os
import json
from pathlib import Path

def test_complete_workflow():
    """Test the complete workflow with a real audio file"""
    
    # Create test output directory
    output_dir = Path("test_results")
    output_dir.mkdir(exist_ok=True)
    output_json = output_dir / "transcription_output.json"
    
    # You can replace this with your actual audio file path
    # For now, let's assume we have the uploaded file from the logs
    test_audio_file = "/Users/creed/Workspace/OpenSource/audio2sub/backend/uploads/40e91bb1-204d-4d7e-8df4-45d1c5118a14.mp3"
    
    if not os.path.exists(test_audio_file):
        print(f"Test audio file not found: {test_audio_file}")
        print("Please update the path or upload a file first")
        return
    
    try:
        # Set environment to reduce warnings
        env = os.environ.copy()
        env['TRANSFORMERS_VERBOSITY'] = 'error'
        
        # Command to test (same as in our task)
        cmd = [
            "insanely-fast-whisper",
            "--file-name", test_audio_file,
            "--model-name", "openai/whisper-base",
            "--transcript-path", str(output_json),
            "--device-id", "mps",
            "--timestamp", "word",
            "--task", "transcribe"
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        print(f"Input file exists: {os.path.exists(test_audio_file)}")
        print(f"Input file size: {os.path.getsize(test_audio_file)} bytes")
        
        # Run the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
            env=env
        )
        
        print(f"\nReturn code: {result.returncode}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        
        # Check output file regardless of return code
        if output_json.exists():
            file_size = output_json.stat().st_size
            print(f"\n✓ Output file created: {output_json}")
            print(f"Output file size: {file_size} bytes")
            
            if file_size > 0:
                try:
                    with open(output_json, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    print("✓ JSON is valid")
                    print(f"Text content: {data.get('text', 'No text field')[:200]}...")
                    print(f"Available keys: {list(data.keys())}")
                    
                    if 'segments' in data:
                        print(f"Number of segments: {len(data['segments'])}")
                        if data['segments']:
                            print(f"First segment: {data['segments'][0]}")
                    
                    # Test if we would succeed with our current logic
                    stderr_lower = result.stderr.lower() if result.stderr else ""
                    critical_errors = ["error:", "exception:", "failed:", "cannot", "unable"]
                    has_critical_error = any(error in stderr_lower for error in critical_errors)
                    
                    print(f"\nCritical error detection: {has_critical_error}")
                    print(f"Would our task succeed? {file_size > 0 and (result.returncode == 0 or not has_critical_error)}")
                    
                except json.JSONDecodeError as e:
                    print(f"✗ JSON decode error: {e}")
                    with open(output_json, 'r') as f:
                        content = f.read()
                    print(f"Raw content (first 500 chars): {content[:500]}")
            else:
                print("✗ Output file is empty")
        else:
            print("✗ Output file was not created")
            
    except subprocess.TimeoutExpired:
        print("✗ Command timed out")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        # Optional cleanup - comment out if you want to inspect the file
        # try:
        #     if output_json.exists():
        #         os.unlink(output_json)
        #         print(f"Cleaned up test output: {output_json}")
        # except:
        #     pass
        pass

if __name__ == "__main__":
    test_complete_workflow()
