"""
IMS AstroBot — Central Configuration
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(DATA_DIR / "uploads")))
CHROMA_PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", str(DATA_DIR / "chroma_db")))
SQLITE_DB_PATH = Path(os.getenv("SQLITE_DB_PATH", str(DATA_DIR / "astrobot.db")))

# ── Ensure directories exist ──
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── LLM Mode ──
# local_only  → Ollama only
# cloud_only  → Primary cloud provider, fallback to secondary cloud
# hybrid      → Primary → fallback → Ollama as last resort
LLM_MODE = os.getenv("LLM_MODE", "local_only")
LLM_PRIMARY_PROVIDER = os.getenv("LLM_PRIMARY_PROVIDER", "ollama")
LLM_FALLBACK_PROVIDER = os.getenv("LLM_FALLBACK_PROVIDER", "none")

# ── Ollama (local) ──
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:0.6b")

# ── Grok (xAI) ──
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-3")

# ── Gemini (Google) ──
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ── Generation Parameters ──
MODEL_MAX_TOKENS = int(os.getenv("MODEL_MAX_TOKENS", 512))
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", 0.3))

# ── Embedding ──
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ── Chunking ──
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))

# ── Auth ──
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# ── Retrieval ──
TOP_K_RESULTS = 5

# ── Supported file types ──
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".xlsx", ".csv", ".pptx", ".html", ".htm"}

# ── System Prompt ──
SYSTEM_PROMPT = """You are IMS AstroBot, a helpful and accurate academic assistant for an institutional management system. 
You answer questions based ONLY on the provided institutional documents and context.
If the context does not contain enough information to answer the question, say so clearly.
Do not make up information. Always be concise, professional, and helpful.
If citing specific regulations or policies, mention the source document when possible."""
