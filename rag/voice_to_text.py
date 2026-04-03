"""
IMS AstroBot — Voice to Text Module
Uses faster-whisper to transcribe audio files into text locally.
"""
import os
import time
from typing import Tuple, Optional
from faster_whisper import WhisperModel
from functools import lru_cache

from log_config import get_logger

logger = get_logger(__name__)

# Use base.en for fast inference. This is automatically downloaded from HuggingFace on first use.
MODEL_SIZE = "base.en"

# We use lru_cache to keep the model loaded in memory for faster subsequent inferences.
@lru_cache(maxsize=1)
def get_whisper_model() -> WhisperModel:
    logger.info(f"Loading Whisper model: {MODEL_SIZE}")
    # Run on CPU with int8 quantization for balance of speed/memory on typical backend servers.
    # If the system has a GPU with CUDA, this could be changed to device="cuda", compute_type="float16"
    return WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

def transcribe_audio(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Transcribes an audio file and returns the text.
    Returns (transcription_text, error_message).
    """
    try:
        start_time = time.time()
        model = get_whisper_model()
        
        # Transcribe
        segments, info = model.transcribe(file_path, beam_size=5)
        
        text_parts = []
        for segment in segments:
            text_parts.append(segment.text)
            
        transcription = " ".join(text_parts).strip()
        elapsed = time.time() - start_time
        
        logger.info(f"Transcription completed in {elapsed:.2f}s: '{transcription[:50]}...'")
        return transcription, None
        
    except Exception as e:
        logger.error(f"Whisper transcription failed for {file_path}: {e}", exc_info=True)
        return None, str(e)
