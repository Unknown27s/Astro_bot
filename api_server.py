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

# ── Initialize Logging & Error Tracking ──
from log_config import get_logger, setup_logging
from log_config.sentry_config import init_sentry

setup_logging()
init_sentry()
logger = get_logger(__name__)

# Now import standard library logging after custom modules are loaded
import logging
from functools import lru_cache
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ── Constants ──
HEADER_USER_ID = "X-User-ID"
DEFAULT_USER_ID = "system"
RATE_LIMIT_ADMIN_TIER = "30/minute"
RATE_LIMIT_RESET_TIER = "10/minute"

# ── Initialize Rate Limiting ──
from middleware.rate_limiter import get_limiter, log_rate_limit_exceeded
from slowapi.errors import RateLimitExceeded

limiter = get_limiter()
app_instance_limiter = limiter  # Will be assigned after app creation

# ── Initialize database on import ──
from database.db import (
    init_db, authenticate_user, create_user, get_all_users,
    toggle_user_active, delete_user, add_document, get_all_documents,
    delete_document, log_query, get_query_logs, get_analytics, get_connection,
    store_memory, delete_memory, cleanup_expired_memory, invalidate_memory_by_source,
    get_memory_stats, clear_all_memory,
    get_all_rate_limits, get_rate_limit, update_rate_limit, toggle_rate_limit, reset_rate_limits_to_default,
    get_suggestions, create_announcement, get_recent_announcements,
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

# Assign limiter to app
app.state.limiter = limiter

# Import middleware
from middleware.request_tracking import RequestTrackingMiddleware, ErrorContextMiddleware

# Add middleware (order matters: error context first, then request tracking, then CORS)
app.add_middleware(ErrorContextMiddleware)
app.add_middleware(RequestTrackingMiddleware)

# Allow Spring Boot (or any frontend) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Rate Limiting Exception Handler ──
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    log_rate_limit_exceeded(request, exc)
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded",
            "retry_after": "60",
        },
        headers={"Retry-After": "60"},
    )


# ── Global Exception Handler ──
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Capture all unhandled exceptions and log them."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )

    # Return error response
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": request_id,
        },
    )


# ── Helper Functions ──
def get_user_id(request: Request) -> str:
    """Extract user ID from request headers with consistent default."""
    return request.headers.get(HEADER_USER_ID, DEFAULT_USER_ID)


@lru_cache(maxsize=1, typed=False)
def get_all_rate_limits_cached():
    """Get all rate limit configurations with 10-second cache."""
    return get_all_rate_limits()


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
    transcribed_text: Optional[str] = None

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
@limiter.limit("5/minute")  # Brute force protection
def api_login(req: LoginRequest, request: Request):
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
@limiter.limit("5/minute")  # Registration rate limit
def api_register(req: RegisterRequest, request: Request):
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

@app.get("/api/announcements")
def api_list_announcements(limit: int = 50):
    """Get the recent announcements feed."""
    return get_recent_announcements(limit)

@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("5/minute")  # Expensive LLM operation - strict limit
def api_chat(req: ChatRequest, request: Request):
    """Send a query through the RAG pipeline and get a response."""
    from rag.retriever import retrieve_context, format_context_for_llm, get_source_citations
    from rag.generator import generate_response

    start_time = time.time()

    # --- Announcement Feature Intercept ---
    if req.query.strip().lower().startswith("@announcement"):
        from database.db import get_connection
        conn = get_connection()
        user_row = conn.execute("SELECT role FROM users WHERE id = ?", (req.user_id,)).fetchone()
        conn.close()
        
        if not user_row or user_row['role'] not in ('admin', 'faculty'):
            raise HTTPException(status_code=403, detail="Only faculty and admins can post announcements")
            
        # Bypass RAG, just use LLM to format
        prompt = f"You are an institutional announcer. Please format the following raw text into a professional, clear, and engaging announcement with suitable emojis. Do not add conversational filler, just output the announcement text.\n\nRaw text: {req.query[13:].strip()}"
        
        gen_result = generate_response(prompt, context="", user_id=req.user_id)
        formatted_announcement = gen_result.get("response", "") if isinstance(gen_result, dict) else gen_result
        
        if not formatted_announcement:
            formatted_announcement = f"📢 **New Announcement**\n\n{req.query[13:].strip()}"
            
        create_announcement(req.user_id, req.username, formatted_announcement)
        
        elapsed_ms = (time.time() - start_time) * 1000
        return ChatResponse(
            response="✅ Announcement generated and posted successfully!\n\n---\n\n" + formatted_announcement,
            sources=[],
            citations="",
            response_time_ms=round(elapsed_ms, 1)
        )

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
        # ALWAYS log the query (even if from memory) to ensure Admin Analytics is accurate
        # and popular questions are tracked correctly.
        log_response_text = f"[⚡ CACHED] {response_text}" if from_memory else response_text
        
        log_query(
            user_id=req.user_id,
            username=req.username,
            query_text=req.query,
            response_text=log_response_text[:500],
            sources=source_names,
            response_time_ms=elapsed_ms,
        )
        logger.info(
            f"Query logged successfully",
            extra={
                "user_id": req.user_id,
                "response_time_ms": round(elapsed_ms, 2),
                "sources": source_names,
            }
        )
    except Exception as e:
        logger.error(
            f"Error logging query: {str(e)}",
            extra={
                "user_id": req.user_id,
                "query": req.query[:100],
            },
            exc_info=True,
        )

    return ChatResponse(
        response=response_text,
        sources=chunks,
        citations=citations,
        response_time_ms=round(elapsed_ms, 1),
    )


@app.post("/api/chat/audio", response_model=ChatResponse)
@limiter.limit("5/minute")
def api_chat_audio(
    request: Request,
    audio: UploadFile = File(...),
    user_id: str = Form(...),
    username: str = Form(...)
):
    """Receive audio, transcribe to text, and process through RAG pipeline."""
    from rag.retriever import retrieve_context, format_context_for_llm, get_source_citations
    from rag.generator import generate_response
    import shutil
    from rag.voice_to_text import transcribe_audio

    start_time = time.time()
    
    file_ext = Path(audio.filename).suffix.lower()
    if not file_ext:
        file_ext = ".webm" # Default from browser
        
    safe_name = f"audio_{int(time.time())}{file_ext}"
    file_path = UPLOAD_DIR / safe_name
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)
        
    transcribed_text, error = transcribe_audio(str(file_path))
    
    try:
        os.remove(file_path)
    except Exception as e:
        logger.warning(f"Could not delete temp audio file: {e}")
        
    if error or not transcribed_text:
        raise HTTPException(status_code=500, detail=f"Audio transcription failed: {error}")
        
    logger.info(f"User {username} spoke: {transcribed_text}")
    
    # Generate RAG response based on transcribed text
    chunks = retrieve_context(transcribed_text)
    context = format_context_for_llm(chunks)
    
    gen_result = generate_response(transcribed_text, context, user_id=user_id, sources=[c.get("source", "") for c in chunks])
    
    response_text = gen_result.get("response", "") if isinstance(gen_result, dict) else gen_result
    citations = get_source_citations(chunks)
    elapsed_ms = (time.time() - start_time) * 1000
    
    try:
        source_names = ", ".join([c.get("source", "") for c in chunks[:3]])
        log_response_text = f"[🗣️ VOICE] {response_text}" 
        
        log_query(
            user_id=user_id,
            username=username,
            query_text=f"[VOICE] {transcribed_text}",
            response_text=log_response_text[:500],
            sources=source_names,
            response_time_ms=elapsed_ms,
        )
    except Exception as e:
        logger.error(f"Error logging audio query: {str(e)}", exc_info=True)

    return ChatResponse(
        response=response_text,
        sources=chunks,
        citations=citations,
        response_time_ms=round(elapsed_ms, 1),
        transcribed_text=transcribed_text
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
# SUGGESTIONS / AUTOCOMPLETE ENDPOINT
# ═══════════════════════════════════════════════════════

@app.get("/api/suggestions")
@limiter.limit("30/minute")
def api_get_suggestions(request: Request, q: str = "", user_id: str = None):
    """Get autocomplete suggestions for the chat input.
    
    Returns recent user questions, popular questions, and preset suggestions.
    """
    result = get_suggestions(query_prefix=q, user_id=user_id)
    return result



# ═══════════════════════════════════════════════════════
# DOCUMENT MANAGEMENT ENDPOINTS
# ═══════════════════════════════════════════════════════

@app.post("/api/documents/upload")
@limiter.limit("10/minute")  # File uploads are I/O intensive
def api_upload_document(
    request: Request,  # Required for rate limiter key extraction
    file: UploadFile = File(...),
    uploaded_by: str = Form(None),  # Make it optional with default None
):
    """Upload, parse, chunk, and index a document (admin only if uploaded_by is provided)."""
    from ingestion.parser import parse_document
    from ingestion.chunker import chunk_document
    from ingestion.embedder import store_chunks

    # ── Admin-only check (only if uploaded_by is provided) ──
    if uploaded_by:
        conn = get_connection()
        user = conn.execute("SELECT id, role FROM users WHERE id = ?", (uploaded_by,)).fetchone()
        conn.close()

        if not user:
            raise HTTPException(status_code=404, detail=f"User ID {uploaded_by} not found")

        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only administrators can upload documents")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}")

    # Save file to disk
    safe_name = f"{int(time.time())}_{file.filename}"
    file_path = UPLOAD_DIR / safe_name
    content = file.file.read()

    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    # Validate file size (max 50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large ({len(content) / 1024 / 1024:.1f}MB). Maximum: 50MB")

    with open(file_path, "wb") as f:
        f.write(content)

    # ── Check if PDF is password-protected ──
    if file_ext == ".pdf":
        try:
            from PyPDF2 import PdfReader
            pdf_reader = PdfReader(file_path)
            if pdf_reader.is_encrypted:
                os.remove(file_path)
                logger.warning(f"Locked PDF rejected: {file.filename}")
                raise HTTPException(
                    status_code=422,
                    detail=f"❌ PDF is password-protected. Please remove the password and try again."
                )
        except HTTPException:
            raise  # Re-raise our custom error
        except Exception as e:
            logger.debug(f"PDF encryption check error for {file.filename}: {e}")
            # Don't block on encryption check errors, let parsing handle it

    # Parse document
    text, parse_error = parse_document(str(file_path))
    if not text:
        os.remove(file_path)
        error_detail = parse_error or "Failed to extract text from document"
        logger.warning(f"Document parse failed for {file.filename}: {error_detail}")
        raise HTTPException(status_code=422, detail=error_detail)

    # Chunk document
    chunks = chunk_document(text, source_name=file.filename)
    if not chunks:
        os.remove(file_path)
        raise HTTPException(status_code=422, detail="No chunks generated from document (text may be too short)")

    # Record in database
    try:
        doc_id = add_document(
            filename=safe_name,
            original_name=file.filename,
            file_type=file_ext,
            file_size=len(content),
            chunk_count=len(chunks),
            uploaded_by=uploaded_by,
        )
    except Exception as e:
        os.remove(file_path)
        logger.error(f"Database error for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record document in database: {str(e)}")

    # Store embeddings in ChromaDB
    try:
        stored = store_chunks(chunks, doc_id)
    except Exception as e:
        logger.error(f"ChromaDB error for doc {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to index document in vector database: {str(e)}")

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

    try:
        # Delete from ChromaDB first (chunks)
        try:
            delete_doc_chunks(doc_id)
        except Exception as e:
            logger.warning(f"Failed to delete ChromaDB chunks for {doc_id}: {e}")
            # Continue with database deletion even if ChromaDB fails

        # Delete from database
        deleted = delete_document(doc_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete physical file
        file_path = UPLOAD_DIR / deleted["filename"]
        if file_path.exists():
            try:
                os.remove(file_path)
            except OSError as e:
                logger.warning(f"Failed to delete file {file_path}: {e}")

        return {"message": f"Deleted: {deleted['original_name']}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@app.get("/api/documents/stats")
def api_documents_stats():
    """Get knowledge base statistics (total chunks indexed)."""
    from ingestion.embedder import get_collection_stats

    try:
        stats = get_collection_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        return {"total_chunks": 0, "error": str(e)}


# ═══════════════════════════════════════════════════════
# TAGGING & CLASSIFICATION ENDPOINTS (Phase 3)
# ═══════════════════════════════════════════════════════

class TagRequest(BaseModel):
    name: str
    description: str = ""
    color: str = "#808080"

class TagUpdateRequest(BaseModel):
    name: str = None
    description: str = None
    color: str = None

class ClassificationRequest(BaseModel):
    classification: str
    confidence: float = 1.0
    auto_classified: bool = False
    notes: str = None

class UpdateRateLimitRequest(BaseModel):
    limit_requests: int
    limit_window_seconds: int
    enabled: bool = True

class ToggleRateLimitRequest(BaseModel):
    enabled: bool


@app.post("/api/documents/tags")
@limiter.limit("30/minute")  # Create tags - admin feature
def api_create_tag(req: TagRequest, request: Request):
    """Create a new tag."""
    from database.db import create_tag
    user_id = request.headers.get("X-User-ID", "system")
    tag_id = create_tag(req.name, req.description, req.color, user_id)
    if not tag_id:
        raise HTTPException(status_code=409, detail="Tag name already exists")
    logger.info(f"Tag created: {req.name}")
    return {"id": tag_id, "name": req.name}


@app.get("/api/documents/tags")
@limiter.limit("60/minute")  # List tags - read-heavy
def api_list_tags(request: Request):
    """Get all tags with usage counts."""
    from database.db import get_all_tags
    return get_all_tags()


@app.put("/api/documents/tags/{tag_id}")
@limiter.limit("30/minute")  # Update tags
def api_update_tag(tag_id: str, req: TagUpdateRequest, request: Request):
    """Update a tag."""
    from database.db import update_tag
    success = update_tag(tag_id, req.name, req.description, req.color)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update tag")
    logger.info(f"Tag updated: {tag_id}")
    return {"message": "Tag updated"}


@app.delete("/api/documents/tags/{tag_id}")
@limiter.limit("30/minute")  # Delete tags
def api_delete_tag(tag_id: str, request: Request):
    """Delete a tag."""
    from database.db import delete_tag
    success = delete_tag(tag_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete tag")
    logger.info(f"Tag deleted: {tag_id}")
    return {"message": "Tag deleted"}


@app.post("/api/documents/{doc_id}/tags/{tag_id}")
@limiter.limit("30/minute")  # Add tags to documents
def api_add_tag_to_document(doc_id: str, tag_id: str, request: Request):
    """Add a tag to a document."""
    from database.db import add_tag_to_document
    user_id = request.headers.get("X-User-ID", "system")
    success = add_tag_to_document(doc_id, tag_id, user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add tag (may already exist)")
    logger.info(f"Tag {tag_id} added to document {doc_id}")
    return {"message": "Tag added"}


@app.delete("/api/documents/{doc_id}/tags/{tag_id}")
@limiter.limit("30/minute")  # Remove tags
def api_remove_tag_from_document(doc_id: str, tag_id: str, request: Request):
    """Remove a tag from a document."""
    from database.db import remove_tag_from_document
    success = remove_tag_from_document(doc_id, tag_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to remove tag")
    logger.info(f"Tag {tag_id} removed from document {doc_id}")
    return {"message": "Tag removed"}


@app.get("/api/documents/{doc_id}/tags")
@limiter.limit("60/minute")  # Get document tags
def api_get_document_tags(doc_id: str, request: Request):
    """Get all tags for a document."""
    from database.db import get_document_tags
    return {"tags": get_document_tags(doc_id)}


@app.post("/api/documents/{doc_id}/classify")
@limiter.limit("30/minute")  # Set classification
def api_set_classification(doc_id: str, req: ClassificationRequest, request: Request):
    """Set or update a document's classification."""
    from database.db import set_document_classification
    user_id = request.headers.get("X-User-ID", "system")
    success = set_document_classification(
        doc_id,
        req.classification,
        req.confidence,
        req.auto_classified,
        user_id,
        req.notes
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to set classification")
    logger.info(f"Document {doc_id} classified as: {req.classification}")
    return {"message": "Document classified"}


@app.get("/api/documents/{doc_id}/classify")
@limiter.limit("60/minute")  # Get classification
def api_get_classification(doc_id: str, request: Request):
    """Get classification for a document."""
    from database.db import get_document_classification
    classification = get_document_classification(doc_id)
    if not classification:
        return {"classification": None}
    return {"classification": classification}


@app.get("/api/documents/search")
@limiter.limit("30/minute")  # Search with filters
def api_search_documents(request: Request, tags: str = None, classification: str = None):
    """Search/filter documents by tags and/or classification."""
    from database.db import filter_documents_by_tags, get_documents_by_classification, get_all_documents

    results = []

    if tags:
        tag_ids = tags.split(",")
        results = filter_documents_by_tags(tag_ids)
    elif classification:
        results = get_documents_by_classification(classification)
    else:
        results = get_all_documents()

    logger.debug(f"Document search: tags={tags}, classification={classification}, results={len(results)}")
    return {"documents": results, "total": len(results)}


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


@app.get("/api/documents/stats")
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
# RATE LIMITING CONFIGURATION (Admin)
# ═══════════════════════════════════════════════════════

@app.get("/api/admin/rate-limits")
@limiter.limit(RATE_LIMIT_ADMIN_TIER)
def api_get_rate_limits(request: Request):
    """Get all rate limit configurations (admin only)."""
    try:
        limits = get_all_rate_limits()
        return {"rate_limits": limits}
    except Exception as e:
        logger.error(f"Error fetching rate limits: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch rate limits")


@app.put("/api/admin/rate-limits/{endpoint}")
@limiter.limit(RATE_LIMIT_ADMIN_TIER)
def api_update_rate_limit(request: Request, endpoint: str, req: UpdateRateLimitRequest):
    """Update rate limit configuration for an endpoint (admin only)."""
    if req.limit_requests <= 0 or req.limit_window_seconds <= 0:
        raise HTTPException(status_code=400, detail="Limits must be positive integers")

    # Check if endpoint exists
    existing = get_rate_limit(endpoint)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Endpoint '{endpoint}' not found")

    success = update_rate_limit(endpoint, req.limit_requests, req.limit_window_seconds, req.enabled, get_user_id(request))
    if not success:
        raise HTTPException(status_code=500, detail="Database update failed")

    # Return actual stored values, not request params
    updated_limit = get_rate_limit(endpoint)
    logger.info(f"Rate limit updated for {endpoint}: {req.limit_requests} requests/{req.limit_window_seconds}s, enabled={req.enabled}")
    return {"updated": True, "rate_limit": updated_limit}


@app.patch("/api/admin/rate-limits/{endpoint}/toggle")
@limiter.limit(RATE_LIMIT_ADMIN_TIER)
def api_toggle_rate_limit(request: Request, endpoint: str, req: ToggleRateLimitRequest):
    """Enable/disable rate limiting for an endpoint (admin only)."""
    existing = get_rate_limit(endpoint)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Endpoint '{endpoint}' not found")

    success = toggle_rate_limit(endpoint, req.enabled, get_user_id(request))
    if not success:
        raise HTTPException(status_code=500, detail="Database update failed")

    # Return actual stored values
    updated_limit = get_rate_limit(endpoint)
    logger.info(f"Rate limit toggled for {endpoint}: enabled={req.enabled}")
    return {"toggled": True, "rate_limit": updated_limit}


@app.post("/api/admin/rate-limits/reset")
@limiter.limit(RATE_LIMIT_RESET_TIER)
def api_reset_rate_limits(request: Request):
    """Reset all rate limits to default values (admin only, dangerous)."""
    success = reset_rate_limits_to_default()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reset rate limits")

    logger.warning(f"Rate limits reset to default by {get_user_id(request)}")
    return {"reset": True, "message": "All rate limits have been reset to default values"}

@app.get("/api/documents/stats")  # ← ADD THIS
def api_documents_stats():
    from ingestion.embedder import get_collection_stats
    return get_collection_stats()

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
