import os
import sys

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🎙️ Whisper Voice-to-Text Setup & Test Script")
    print("------------------------------------------")
    print("📝 How model downloading works:")
    print("The 'base.en' model (approx. 140MB) is AUTOMATICALLY downloaded")
    print("from HuggingFace directly into your computer's local cache")
    print("the very first time the model is initialized. No manual steps needed!")
    print("\nPlease make sure you have internet access and 'ffmpeg' installed.\n")
    
    if len(sys.argv) < 2:
        print("Usage: python test_whisper.py <path_to_audio_file>")
        print("\nExample: python test_whisper.py my_voice_memo.mp3")
        print("\n[Optional] Initializing model to trigger download if not present...")
        try:
            from faster_whisper import WhisperModel
            import time
            start = time.time()
            model = WhisperModel("base.en", device="cpu", compute_type="int8")
            end = time.time()
            print(f"✅ Model initialized successfully in {end-start:.2f} seconds!")
            print("You are ready to use the Voice-to-Text feature.")
        except Exception as e:
            print(f"❌ Failed to initialize model: {e}")
            print("\nPlease ensure ffmpeg is installed and added to your PATH.")
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
