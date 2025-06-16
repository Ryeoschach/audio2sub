#!/usr/bin/env python3
"""
Test script to check if insanely-fast-whisper is working correctly
"""

import subprocess
import tempfile
import os
import json
from pathlib import Path

def test_insanely_fast_whisper():
    print("Testing insanely-fast-whisper installation and basic functionality...")
    
    # Check if insanely-fast-whisper is installed
    try:
        result = subprocess.run(["insanely-fast-whisper", "--help"], 
                              capture_output=True, text=True, timeout=30)
        print(f"insanely-fast-whisper help command return code: {result.returncode}")
        if result.returncode != 0:
            print("ERROR: insanely-fast-whisper --help failed")
            print(f"stderr: {result.stderr}")
            return False
        print("✓ insanely-fast-whisper is installed and accessible")
    except Exception as e:
        print(f"ERROR: Cannot run insanely-fast-whisper: {e}")
        return False
    
    # Test with a simple audio file (you'll need to provide one)
    # For now, let's just test if we can run the command with basic parameters
    
    print("\nTesting basic command structure...")
    test_output_dir = Path("test_output")
    test_output_dir.mkdir(exist_ok=True)
    test_json_path = test_output_dir / "test_output.json"
    
    # Create a minimal test - this will fail but we can see the error
    cmd = [
        "insanely-fast-whisper",
        "--help"  # Just get help for now
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        print(f"Basic command test return code: {result.returncode}")
        print(f"stdout: {result.stdout[:500]}...")  # First 500 chars
        if result.stderr:
            print(f"stderr: {result.stderr[:500]}...")
    except Exception as e:
        print(f"ERROR running basic command: {e}")
        return False
    
    # Test model availability
    print("\nTesting model availability...")
    try:
        # Try to see what models are available or if we can load one
        cmd_model_test = [
            "python", "-c", 
            "from transformers import pipeline; print('Models accessible'); "
            "import torch; print(f'MPS available: {torch.backends.mps.is_available()}'); "
            "print(f'MPS built: {torch.backends.mps.is_built()}')"
        ]
        result = subprocess.run(cmd_model_test, capture_output=True, text=True, timeout=60)
        print(f"Model test return code: {result.returncode}")
        print(f"Model test output: {result.stdout}")
        if result.stderr:
            print(f"Model test stderr: {result.stderr}")
    except Exception as e:
        print(f"ERROR testing model: {e}")
    
    return True

if __name__ == "__main__":
    test_insanely_fast_whisper()
