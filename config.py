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
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = Path(os.getenv("MODEL_PATH", str(MODEL_DIR / "phi-3-mini-4k-instruct-q4.gguf")))

# ── Ensure directories exist ──
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── LLM Settings ──
MODEL_N_CTX = int(os.getenv("MODEL_N_CTX", 4096))
MODEL_N_THREADS = int(os.getenv("MODEL_N_THREADS", 4))
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
