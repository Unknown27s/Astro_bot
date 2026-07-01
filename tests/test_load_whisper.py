import os
import sys

# Add current directory to path if needed
sys.path.append(os.getcwd())

try:
    from faster_whisper import WhisperModel
    import os

    # Path from the script's perspective
    # Active document is rag/voice_to_text.py
    # MODEL_DIR = .../Astro_bot/models/whisper-base-en
    
    base_path = os.getcwd() # Assuming we are in d:\Harish Kumar\Project\Astro_botV2\Astro_bot
    model_path = os.path.join(base_path, "models", "whisper-base-en")
    
    print(f"Testing model load from: {model_path}")
    print(f"Directory exists: {os.path.exists(model_path)}")
    print(f"Files: {os.listdir(model_path)}")
    
    model = WhisperModel(model_path, device="cpu", compute_type="int8", local_files_only=True)
    print("SUCCESS: Model loaded correctly!")
    
except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()
