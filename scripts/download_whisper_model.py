"""
Download Whisper base.en model to local folder.
This script downloads the model from Hugging Face and extracts it locally.
"""
import os
import sys
from pathlib import Path

# Set up model directory
MODEL_DIR = Path(__file__).parent / "models" / "whisper-base-en"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

print(f"📥 Downloading Whisper base.en model to: {MODEL_DIR}")
print("This may take a few minutes on first run (~500MB)...\n")

try:
    # Import after installation
    from faster_whisper import WhisperModel
    
    # Download and initialize the model
    # This will handle the download automatically if local_files_only=False
    print("⏳ Initializing model (downloading if needed)...")
    model = WhisperModel("base.en", device="cpu", compute_type="int8", download_root=str(MODEL_DIR.parent))
    
    print("✅ SUCCESS! Model downloaded and verified.")
    print(f"📁 Model location: {MODEL_DIR}")
    print(f"📋 Files in directory: {list(MODEL_DIR.iterdir())}")
    
except Exception as e:
    print(f"❌ Failed to download model: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
