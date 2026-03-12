"""
IMS AstroBot — FastAPI REST API Server
Exposes all RAG, auth, document, and admin functionality as REST endpoints.
This server runs alongside or instead of the Streamlit UI, allowing
Spring Boot (or any HTTP client) to consume the RAG pipeline.
"""

import os
import sys
import time
import uuid
from pathlib import Path
from typing import Optional

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Initialize database on import ──
from database.db import (
    init_db, authenticate_user, create_user, get_all_users,
    toggle_user_active, delete_user, add_document, get_all_documents,
    delete_document, log_query, get_query_logs, get_analytics, get_connection,
    store_memory, delete_memory, cleanup_expired_memory, invalidate_memory_by_source,
    get_memory_stats, clear_all_memory,
)
from config import (
    UPLOAD_DIR, SUPPORTED_EXTENSIONS, EMBEDDING_MODEL,
    CHROMA_PERSIST_DIR, LLM_MODE, BASE_DIR, CONV_ENABLED,
)

init_db()

app = FastAPI(
    title="IMS AstroBot API",
    description="RAG-powered institutional AI assistant API",
    version="2.0.0",
)

# Allow Spring Boot (or any frontend) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ═══════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "student"
    full_name: str = ""

class ChatRequest(BaseModel):
    query: str
    user_id: str
    username: str

class ChatResponse(BaseModel):
    response: str
    sources: list[dict]
    citations: str
    response_time_ms: float

class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "student"
    full_name: str = ""

class ToggleUserRequest(BaseModel):
    is_active: bool

class UpdateEnvRequest(BaseModel):
    key: str
    value: str

class ProviderSettingsRequest(BaseModel):
    llm_mode: Optional[str] = None
    primary_provider: Optional[str] = None
    fallback_provider: Optional[str] = None
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None
    groq_api_key: Optional[str] = None
    groq_model: Optional[str] = None
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


# ═══════════════════════════════════════════════════════
# AUTH ENDPOINTS
# ═══════════════════════════════════════════════════════

@app.post("/api/auth/login")
def api_login(req: LoginRequest):
    """Authenticate a user and return user info."""
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "full_name": user["full_name"],
    }


@app.post("/api/auth/register")
def api_register(req: RegisterRequest):
    """Register a new user account."""
    if req.role not in ("student", "faculty"):
        raise HTTPException(status_code=400, detail="Role must be 'student' or 'faculty'")
    success = create_user(req.username, req.password, req.role, req.full_name)
    if not success:
        raise HTTPException(status_code=409, detail="Username already exists")
    return {"message": "User registered successfully"}


# ═══════════════════════════════════════════════════════
# CHAT / RAG ENDPOINTS
# ═══════════════════════════════════════════════════════

@app.post("/api/chat", response_model=ChatResponse)
def api_chat(req: ChatRequest):
    """Send a query through the RAG pipeline and get a response."""
    from rag.retriever import retrieve_context, format_context_for_llm, get_source_citations
    from rag.generator import generate_response

    start_time = time.time()

    # Step 1: Retrieve relevant chunks
    chunks = retrieve_context(req.query)

    # Step 2: Format context for LLM
    context = format_context_for_llm(chunks)

    # Step 3: Generate response (now includes memory handling)
    gen_result = generate_response(req.query, context, user_id=req.user_id, sources=[c.get("source", "") for c in chunks])
    
    # Extract response from dict
    response_text = gen_result.get("response", "") if isinstance(gen_result, dict) else gen_result
    from_memory = gen_result.get("from_memory", False) if isinstance(gen_result, dict) else False
    memory_id = gen_result.get("memory_id") if isinstance(gen_result, dict) else None

    # Step 4: Get citations
    citations = get_source_citations(chunks)

    elapsed_ms = (time.time() - start_time) * 1000

    # Log query (but note if from memory for analytics)
    try:
        source_names = ", ".join([c.get("source", "") for c in chunks[:3]])
        if not from_memory:  # Don't log cache hits to reduce clutter
            log_query(
                user_id=req.user_id,
                username=req.username,
                query_text=req.query,
                response_text=response_text[:500],
                sources=source_names,
                response_time_ms=elapsed_ms,
            )
    except Exception as e:
        print(f"[API] Error logging query: {e}")

    return ChatResponse(
        response=response_text,
        sources=chunks,
        citations=citations,
        response_time_ms=round(elapsed_ms, 1),
    )


@app.get("/api/chat/status")
def api_chat_status():
    """Check if the LLM is available."""
    from rag.generator import is_llm_available, get_llm_status
    return {
        "available": is_llm_available(),
        "status": get_llm_status(),
    }


# ═══════════════════════════════════════════════════════
# DOCUMENT MANAGEMENT ENDPOINTS
# ═══════════════════════════════════════════════════════

@app.post("/api/documents/upload")
def api_upload_document(
    file: UploadFile = File(...),
    uploaded_by: str = Form(None),  # Make it optional with default None
):
    """Upload, parse, chunk, and index a document."""
    from ingestion.parser import parse_document
    from ingestion.chunker import chunk_document
    from ingestion.embedder import store_chunks

    # Validate uploaded_by exists if provided
    if uploaded_by:
        conn = get_connection()
        user = conn.execute("SELECT id FROM users WHERE id = ?", (uploaded_by,)).fetchone()
        conn.close()
        if not user:
            raise HTTPException(status_code=400, detail=f"User ID {uploaded_by} not found")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}")

    # Save file to disk
    safe_name = f"{int(time.time())}_{file.filename}"
    file_path = UPLOAD_DIR / safe_name
    content = file.file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Parse document
    text = parse_document(str(file_path))
    if not text:
        os.remove(file_path)
        raise HTTPException(status_code=422, detail="Failed to extract text from document")

    # Chunk document
    chunks = chunk_document(text, source_name=file.filename)
    if not chunks:
        os.remove(file_path)
        raise HTTPException(status_code=422, detail="No chunks generated from document")

    # Record in database
    doc_id = add_document(
        filename=safe_name,
        original_name=file.filename,
        file_type=file_ext,
        file_size=len(content),
        chunk_count=len(chunks),
        uploaded_by=uploaded_by,
    )

    # Store embeddings in ChromaDB
    stored = store_chunks(chunks, doc_id)

    return {
        "doc_id": doc_id,
        "filename": file.filename,
        "chunks_indexed": stored,
        "file_size": len(content),
    }


@app.get("/api/documents")
def api_list_documents():
    """List all uploaded documents."""
    return get_all_documents()


@app.delete("/api/documents/{doc_id}")
def api_delete_document(doc_id: str):
    """Delete a document and its chunks."""
    from ingestion.embedder import delete_doc_chunks

    # Delete from ChromaDB
    delete_doc_chunks(doc_id)

    # Delete from database
    deleted = delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete physical file
    file_path = UPLOAD_DIR / deleted["filename"]
    if file_path.exists():
        os.remove(file_path)

    return {"message": f"Deleted: {deleted['original_name']}"}


# ═══════════════════════════════════════════════════════
# USER MANAGEMENT ENDPOINTS (admin)
# ═══════════════════════════════════════════════════════

@app.get("/api/users")
def api_list_users():
    """List all users."""
    return get_all_users()


@app.post("/api/users")
def api_create_user(req: CreateUserRequest):
    """Create a new user (admin action)."""
    if req.role not in ("student", "faculty", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    success = create_user(req.username, req.password, req.role, req.full_name)
    if not success:
        raise HTTPException(status_code=409, detail="Username already exists")
    return {"message": f"User '{req.username}' created as {req.role}"}


@app.patch("/api/users/{user_id}/toggle")
def api_toggle_user(user_id: str, req: ToggleUserRequest):
    """Enable or disable a user account."""
    try:
        toggle_user_active(user_id, req.is_active)
        return {"message": "User updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


@app.delete("/api/users/{user_id}")
def api_delete_user(user_id: str):
    """Delete a user."""
    try:
        delete_user(user_id)
        return {"message": "User deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")


# ═══════════════════════════════════════════════════════
# ANALYTICS ENDPOINTS
# ═══════════════════════════════════════════════════════

@app.get("/api/analytics")
def api_analytics():
    """Get usage analytics summary."""
    return get_analytics()


@app.get("/api/analytics/logs")
def api_query_logs(limit: int = 50):
    """Get recent query logs."""
    return get_query_logs(limit=limit)


# ═══════════════════════════════════════════════════════
# HEALTH / STATUS ENDPOINTS
# ═══════════════════════════════════════════════════════

@app.get("/api/health")
def api_health():
    """Get system health status for core (fast) components only.

    LLM provider checks are exposed separately via /api/health/providers.
    """
    components = {}

    # SQLite (fast local check)
    try:
        conn = get_connection()
        conn.execute("SELECT 1")
        u = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()["cnt"]
        d = conn.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()["cnt"]
        conn.close()
        components["sqlite"] = {
            "status": "ok",
            "message": f"{u} users, {d} documents",
        }
    except Exception as e:
        components["sqlite"] = {"status": "error", "message": str(e)}

    # ChromaDB
    chroma_path = Path(CHROMA_PERSIST_DIR)
    components["chromadb"] = (
        {"status": "ok", "message": f"Ready at {chroma_path.name}/"}
        if chroma_path.exists()
        else {"status": "warning", "message": "Will create on first use"}
    )

    # Embeddings package presence (no model load here)
    try:
        import sentence_transformers
        components["embeddings"] = {
            "status": "ok",
            "message": f"{EMBEDDING_MODEL} (lazy load)",
        }
    except ImportError:
        components["embeddings"] = {
            "status": "error",
            "message": "Package missing",
        }

    # Uploads
    if UPLOAD_DIR.exists():
        fc = len([f for f in UPLOAD_DIR.iterdir() if f.is_file()])
        components["uploads"] = {
            "status": "ok",
            "message": f"{fc} files",
        }
    else:
        components["uploads"] = {
            "status": "error",
            "message": "Directory missing",
        }

    # Conversation memory (if enabled)
    if CONV_ENABLED:
        try:
            mem_stats = get_memory_stats()
            components["memory"] = {
                "status": "ok",
                "message": f"{mem_stats['total_entries']} cached entries",
            }
        except Exception as e:
            components["memory"] = {
                "status": "warning",
                "message": f"Error: {str(e)}",
            }
    else:
        components["memory"] = {
            "status": "warning",
            "message": "Disabled",
        }

    # Overall status aggregation
    overall_status = "healthy"
    for comp in components.values():
        status = comp.get("status", "error")
        if status == "error":
            overall_status = "unhealthy"
            break
        if status in ("warning", "degraded") and overall_status == "healthy":
            overall_status = "degraded"

    return {
        "status": overall_status,
        "components": components,
        "providers": {},  # populated by /api/health/providers on demand
    }


@app.get("/api/health/providers")
def api_provider_statuses():
    """Get detailed provider statuses (may call external LLM APIs)."""
    from rag.providers.manager import get_manager
    mgr = get_manager()
    return mgr.get_all_statuses()


# ═══════════════════════════════════════════════════════
# AI SETTINGS ENDPOINTS (admin)
# ═══════════════════════════════════════════════════════

@app.get("/api/settings")
def api_get_settings():
    """Get current AI settings (reads live values from os.environ)."""
    import config
    return {
        "llm_mode": config.LLM_MODE,
        "primary_provider": config.LLM_PRIMARY_PROVIDER,
        "fallback_provider": config.LLM_FALLBACK_PROVIDER,
        "ollama_base_url": config.OLLAMA_BASE_URL,
        "ollama_model": config.OLLAMA_MODEL,
        "groq_model": config.GROQ_MODEL,
        "gemini_model": config.GEMINI_MODEL,
        "temperature": config.MODEL_TEMPERATURE,
        "max_tokens": config.MODEL_MAX_TOKENS,
        "embedding_model": config.EMBEDDING_MODEL,
        "system_prompt": config.SYSTEM_PROMPT,
        # Never expose API keys — only show if set
        "groq_api_key_set": bool(os.getenv("GROQ_API_KEY", "")),
        "gemini_api_key_set": bool(os.getenv("GEMINI_API_KEY", "")),
    }


@app.put("/api/settings")
def api_update_settings(req: ProviderSettingsRequest):
    """Update AI settings. Only provided fields are updated."""
    from rag.providers.manager import reset_manager

    field_map = {
        "llm_mode": "LLM_MODE",
        "primary_provider": "LLM_PRIMARY_PROVIDER",
        "fallback_provider": "LLM_FALLBACK_PROVIDER",
        "ollama_base_url": "OLLAMA_BASE_URL",
        "ollama_model": "OLLAMA_MODEL",
        "groq_api_key": "GROQ_API_KEY",
        "groq_model": "GROQ_MODEL",
        "gemini_api_key": "GEMINI_API_KEY",
        "gemini_model": "GEMINI_MODEL",
        "temperature": "MODEL_TEMPERATURE",
        "max_tokens": "MODEL_MAX_TOKENS",
    }

    updated = []
    for field, env_key in field_map.items():
        value = getattr(req, field, None)
        if value is not None:
            _update_env_var(env_key, str(value))
            updated.append(env_key)

    if updated:
        _reload_config_module()
        reset_manager()

    return {"message": "Settings updated", "updated_keys": updated}


@app.post("/api/settings/test-provider/{provider}")
def api_test_provider(provider: str):
    """Test connection to a specific provider (reads live env vars)."""
    if provider == "ollama":
        from rag.providers.ollama_provider import OllamaProvider
        prov = OllamaProvider(
            os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            os.environ.get("OLLAMA_MODEL", "qwen3:0.6b"),
        )
        status = prov.get_status()
        extra = {}
        if status["status"] in ("ok", "warning"):
            extra["models"] = prov.list_models()
        return {**status, **extra}
    elif provider == "groq":
        from rag.providers.groq_provider import GroqProvider
        prov = GroqProvider(
            os.environ.get("GROQ_API_KEY", ""),
            os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
        )
        return prov.get_status()
    elif provider == "gemini":
        from rag.providers.gemini_provider import GeminiProvider
        prov = GeminiProvider(
            os.environ.get("GEMINI_API_KEY", ""),
            os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
        )
        return prov.get_status()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")


@app.get("/api/knowledge-base/stats")
def api_knowledge_base_stats():
    """Get vector DB collection stats."""
    from ingestion.embedder import get_collection_stats
    return get_collection_stats()


# ── Helper: update .env file ──

def _update_env_var(key: str, value: str):
    """Update or add a key=value pair in the .env file AND os.environ."""
    # 1. Update the live process environment immediately
    os.environ[key] = value

    # 2. Persist to .env file
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        env_path.write_text(f"{key}={value}\n")
        _reload_config_module()
        return

    lines = env_path.read_text(encoding="utf-8").splitlines()
    found = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key}=") or stripped.startswith(f"{key} ="):
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{key}={value}")

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def _reload_config_module():
    """Force-reload config.py so module-level variables pick up new os.environ values."""
    import importlib
    import config
    importlib.reload(config)


# ═══════════════════════════════════════════════════════
# CONVERSATION MEMORY ENDPOINTS (Admin)
# ═══════════════════════════════════════════════════════

@app.get("/api/memory/stats")
def api_memory_stats():
    """Get statistics on conversation memory usage."""
    if not CONV_ENABLED:
        return {"enabled": False, "message": "Conversation memory is disabled"}
    try:
        stats = get_memory_stats()
        return {"enabled": True, "stats": stats}
    except Exception as e:
        return {"enabled": True, "error": str(e)}


@app.delete("/api/memory/{memory_id}")
def api_delete_memory(memory_id: str):
    """Delete a specific memory entry by ID."""
    if not CONV_ENABLED:
        raise HTTPException(status_code=400, detail="Conversation memory is disabled")
    try:
        success = delete_memory(memory_id)
        if success:
            return {"deleted": True, "id": memory_id}
        else:
            raise HTTPException(status_code=404, detail="Memory entry not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/memory/cleanup")
def api_memory_cleanup():
    """Trigger manual cleanup of expired memory entries."""
    if not CONV_ENABLED:
        raise HTTPException(status_code=400, detail="Conversation memory is disabled")
    try:
        deleted = cleanup_expired_memory()
        return {"deleted": deleted, "message": f"Cleaned up {deleted} expired entries"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/memory/clear")
def api_memory_clear():
    """Clear all conversation memory entries (admin only, use with caution)."""
    if not CONV_ENABLED:
        raise HTTPException(status_code=400, detail="Conversation memory is disabled")
    try:
        total = clear_all_memory()
        return {"cleared": True, "total_deleted": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
