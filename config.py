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

# ── Groq Cloud ──
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

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

# ── Conversation Memory (Semantic Cache) ──
# Enable/disable memory feature
CONV_ENABLED = os.getenv("CONV_ENABLED", "true").lower() == "true"
# Similarity threshold for matching cached responses (0.0 to 1.0; higher = stricter)
CONV_MATCH_THRESHOLD = float(os.getenv("CONV_MATCH_THRESHOLD", "0.88"))
# ChromaDB collection name for storing conversation memory
CONV_PERSIST_COLLECTION = os.getenv("CONV_PERSIST_COLLECTION", "conversation_memory")
# If True, memory is per-user; if False, memory is global (shared)
CONV_PER_USER = os.getenv("CONV_PER_USER", "false").lower() == "true"
# TTL for memory entries (days); entries older than this are cleaned up
CONV_TTL_DAYS = int(os.getenv("CONV_TTL_DAYS", "90"))
# Minimum usage count to keep entry during pruning
CONV_MIN_USAGE_FOR_KEEP = int(os.getenv("CONV_MIN_USAGE_FOR_KEEP", "1"))

# ── Error Tracking & Logging (Phase 1) ──
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "development")
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
SENTRY_ERROR_SAMPLE_RATE = float(os.getenv("SENTRY_ERROR_SAMPLE_RATE", "1.0"))

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = BASE_DIR / "logs"
LOG_FILE_PATH = LOG_DIR / "astrobot.log"
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "10"))

# Ensure logs directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ── Rate Limiting (Phase 2) ──
RATE_LIMIT_GLOBAL = os.getenv("RATE_LIMIT_GLOBAL", "100/minute")
RATE_LIMIT_PER_USER = os.getenv("RATE_LIMIT_PER_USER", "30/minute")
RATE_LIMIT_CHAT = os.getenv("RATE_LIMIT_CHAT", "5/minute")
RATE_LIMIT_UPLOAD = os.getenv("RATE_LIMIT_UPLOAD", "10/minute")
RATE_LIMIT_AUTH = os.getenv("RATE_LIMIT_AUTH", "5/minute")

#  ── Document Tagging (Phase 3) ──
DEFAULT_CLASSIFICATIONS = ["Policy", "Handbook", "Procedure", "Academic", "Administrative", "Finance", "HR", "Archived", "Other"]

