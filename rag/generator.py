"""
IMS AstroBot — LLM Generator
Interfaces with a local GGUF model via llama-cpp-python.
Falls back to a simple echo mode if the model is not available.
"""

import threading
from pathlib import Path
from typing import Optional
from config import MODEL_PATH, MODEL_N_CTX, MODEL_N_THREADS, MODEL_MAX_TOKENS, MODEL_TEMPERATURE, SYSTEM_PROMPT

# ── Thread-safe singleton for LLM ──
_llm_instance = None
_llm_lock = threading.Lock()
_llm_checked = False
_llm_load_error: str | None = None


def _load_llm():
    """Load the GGUF model via llama-cpp-python. Thread-safe singleton."""
    global _llm_instance, _llm_checked, _llm_load_error

    if _llm_instance is not None:
        return _llm_instance
    if _llm_checked and _llm_load_error:
        return None

    with _llm_lock:
        # Double-check after acquiring lock
        if _llm_instance is not None:
            return _llm_instance
        if _llm_checked and _llm_load_error:
            return None

        _llm_checked = True
        model_path = Path(MODEL_PATH)
        if not model_path.exists():
            msg = f"Model not found at {model_path}"
            print(f"[Generator] WARNING: {msg}")
            print("[Generator] Running in FALLBACK mode (no LLM generation).")
            print(f"[Generator] Download a GGUF model and place it at: {model_path}")
            _llm_load_error = msg
            return None

        try:
            from llama_cpp import Llama

            print(f"[Generator] Loading LLM from {model_path}...")
            llm = Llama(
                model_path=str(model_path),
                n_ctx=MODEL_N_CTX,
                n_threads=MODEL_N_THREADS,
                n_gpu_layers=0,  # CPU only
                verbose=False,
            )
            print("[Generator] LLM loaded successfully.")
            _llm_load_error = None
            _llm_instance = llm
            return llm
        except Exception as e:
            msg = str(e)
            print(f"[Generator] Failed to load LLM: {msg}")
            _llm_load_error = msg
            return None


def get_llm_status() -> dict:
    """
    Get LLM status WITHOUT triggering a load.
    Used by health checks to report status quickly.
    """
    model_path = Path(MODEL_PATH)
    if not model_path.exists():
        return {"status": "error", "message": f"Model file missing — place GGUF in models/"}

    # If we've already tried loading, report the result
    if _llm_checked:
        if _llm_load_error:
            return {"status": "warning", "message": f"Load failed: {_llm_load_error}"}
        return {"status": "ok", "message": "Loaded and ready"}

    # Haven't tried loading yet — model file exists but not loaded
    size_mb = model_path.stat().st_size / (1024 * 1024)
    return {
        "status": "ok",
        "message": f"Ready — will load on first query ({size_mb:.0f} MB)",
    }


def is_llm_available() -> bool:
    """Check if the LLM is loaded and ready. Triggers load if not yet done."""
    llm = _load_llm()
    return llm is not None


def generate_response(query: str, context: str) -> str:
    """
    Generate a response using the local LLM with retrieved context.
    
    Args:
        query: User's question
        context: Formatted context from retrieved documents
    
    Returns:
        Generated response string
    """
    llm = _load_llm()

    # ── Build the prompt ──
    prompt = f"""<|system|>
{SYSTEM_PROMPT}
<|end|>
<|user|>
Based on the following institutional documents, answer the question accurately.

CONTEXT:
{context}

QUESTION: {query}
<|end|>
<|assistant|>
"""

    if llm is None:
        return _fallback_response(query, context)

    try:
        response = llm(
            prompt,
            max_tokens=MODEL_MAX_TOKENS,
            temperature=MODEL_TEMPERATURE,
            stop=["<|end|>", "<|user|>", "\n\nQUESTION:"],
            echo=False,
        )

        text = response["choices"][0]["text"].strip()
        return text if text else "I could not generate a response. Please try rephrasing your question."

    except Exception as e:
        print(f"[Generator] Error during generation: {e}")
        return f"An error occurred during response generation. Please try again."


def _fallback_response(query: str, context: str) -> str:
    """
    Fallback response when no LLM is available.
    Returns the retrieved context in a formatted way.
    """
    if "No relevant documents found" in context:
        return (
            "⚠️ **LLM model not loaded** and no relevant documents were found.\n\n"
            "Please ask your administrator to:\n"
            "1. Upload relevant institutional documents\n"
            "2. Place a GGUF model file in the `models/` directory"
        )

    return (
        "⚠️ **LLM model not loaded** — showing retrieved context directly:\n\n"
        f"---\n\n{context}\n\n---\n\n"
        "*To enable AI-generated answers, place a GGUF model file in the `models/` directory and restart the application.*"
    )
