import os
import sys

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🎙️ Whisper Voice-to-Text Setup & Test Script")
    print("------------------------------------------")
    print("📝 How model loading works:")
    print("The 'base.en' model now lives locally in your project folder:")
    print("=> Astro_bot/models/whisper-base-en")
    print("The AI uses this folder directly rather than relying on internet downloads.")
    print("\nPlease make sure 'ffmpeg' is installed.\n")
    
    if len(sys.argv) < 2:
        print("Usage: python test_whisper.py <path_to_audio_file>")
        print("\nExample: python test_whisper.py my_voice_memo.mp3")
        print("\n[Optional] Initializing local model to verify files...")
        try:
            from faster_whisper import WhisperModel
            import time
            start = time.time()
            local_model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "whisper-base-en")
            # strict local_files_only=True to guarantee no network call
            model = WhisperModel(local_model_dir, device="cpu", compute_type="int8", local_files_only=True)
            end = time.time()
            print(f"✅ Local Model initialized successfully in {end-start:.2f} seconds!")
            print("You are ready to use the Voice-to-Text feature.")
        except Exception as e:
            print(f"❌ Failed to initialize model locally: {e}")
            print("\nPlease ensure ffmpeg is installed and the models folder contains the whisper files.")
        return

    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at '{file_path}'")
        return
        
    print(f"Transcribing audio file: {file_path}")
    print("Processing (this may take a few seconds)...")
    
    try:
        from rag.voice_to_text import transcribe_audio
        text = transcribe_audio(file_path)
        print("\n✅ Transcription Complete:")
        print("="*40)
        print(text)
        print("="*40)
    except Exception as e:
        print(f"\n❌ Error during transcription: {e}")

if __name__ == "__main__":
    main()
