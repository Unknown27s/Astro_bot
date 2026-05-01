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
RETRIEVAL_MODE = os.getenv("RETRIEVAL_MODE", "hybrid")  # dense | hybrid
HYBRID_DENSE_WEIGHT = float(os.getenv("HYBRID_DENSE_WEIGHT", "0.7"))
HYBRID_BM25_CANDIDATES = int(os.getenv("HYBRID_BM25_CANDIDATES", "40"))
HYBRID_DENSE_CANDIDATES = int(os.getenv("HYBRID_DENSE_CANDIDATES", "20"))
FULL_PAGE_RAG_ENABLED = os.getenv("FULL_PAGE_RAG_ENABLED", "true").lower() == "true"
FULL_PAGE_MAX_CHARS_PER_PAGE = int(os.getenv("FULL_PAGE_MAX_CHARS_PER_PAGE", "4000"))
HYDE_ENABLED = os.getenv("HYDE_ENABLED", "false").lower() == "true"
HYDE_TRIGGER_SCORE = float(os.getenv("HYDE_TRIGGER_SCORE", "0.58"))
HYDE_SCORE_BLEND = float(os.getenv("HYDE_SCORE_BLEND", "0.6"))
HYDE_MAX_TOKENS = int(os.getenv("HYDE_MAX_TOKENS", "180"))
HYDE_MAX_CHARS = int(os.getenv("HYDE_MAX_CHARS", "1400"))
HYDE_TEMPERATURE = float(os.getenv("HYDE_TEMPERATURE", "0.2"))
ENABLE_GENERAL_CHAT_ROUTING = os.getenv("ENABLE_GENERAL_CHAT_ROUTING", "true").lower() == "true"
FAQ_COLLECTION = os.getenv("FAQ_COLLECTION", "ims_faq")
FAQ_TOP_K = int(os.getenv("FAQ_TOP_K", "5"))
FAQ_MIN_SCORE = float(os.getenv("FAQ_MIN_SCORE", "0.45"))

# ── Query Expansion ──
QUERY_EXPANSION_ENABLED = os.getenv("QUERY_EXPANSION_ENABLED", "false").lower() == "true"
QUERY_EXPANSION_TRIGGER_SCORE = float(os.getenv("QUERY_EXPANSION_TRIGGER_SCORE", "0.50"))
QUERY_EXPANSION_N = int(os.getenv("QUERY_EXPANSION_N", "3"))
QUERY_EXPANSION_MAX_TOKENS = int(os.getenv("QUERY_EXPANSION_MAX_TOKENS", "150"))
QUERY_EXPANSION_RRF_K = int(os.getenv("QUERY_EXPANSION_RRF_K", "60"))
QUERY_EXPANSION_TEMPERATURE = float(os.getenv("QUERY_EXPANSION_TEMPERATURE", "0.3"))

# ── Official Site Ingestion ──
OFFICIAL_SITE_ALLOWED_DOMAINS = [
	domain.strip().lower()
	for domain in os.getenv("OFFICIAL_SITE_ALLOWED_DOMAINS", "").split(",")
	if domain.strip()
]
OFFICIAL_SITE_TIMEOUT_SECONDS = int(os.getenv("OFFICIAL_SITE_TIMEOUT_SECONDS", "15"))
OFFICIAL_SITE_USER_AGENT = os.getenv(
	"OFFICIAL_SITE_USER_AGENT",
	"AstroBot/2.0 official-site-ingestion",
)

# ── Supported file types ──
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".xlsx", ".csv", ".pptx", ".html", ".htm"}

# ── System Prompt (editable from Admin AI Settings) ──
_DEFAULT_SYSTEM_PROMPT = """You are IMS AstroBot, the AI assistant for Rajalakshmi Institute of Technology (RIT).

Guidelines:
1. Prefer uploaded institutional context when it is available and relevant.
2. If the question is unclear, infer likely intent and provide a best-effort helpful answer.
3. If institutional context is missing, use your broader knowledge and reasoning to answer clearly.
4. For official policy-like topics, mention when the response is general guidance and recommend verification with the institute office.
5. Keep responses concise, practical, and student-friendly."""

SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", _DEFAULT_SYSTEM_PROMPT)
SYSTEM_PROMPT = SYSTEM_PROMPT.replace("\\n", "\n")

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

# ── Observability (Langfuse) ──
LANGFUSE_ENABLED = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")

#  ── Document Tagging (Phase 3) ──
DEFAULT_CLASSIFICATIONS = ["Policy", "Handbook", "Procedure", "Academic", "Administrative", "Finance", "HR", "Archived", "Other"]

