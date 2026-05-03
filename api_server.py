"""
IMS AstroBot — FastAPI REST API Server
Exposes all RAG, auth, document, and admin functionality as REST endpoints.
This server runs alongside or instead of the Streamlit UI, allowing
Spring Boot (or any HTTP client) to consume the RAG pipeline.
"""

import os
import sys
import time
import re
import uuid
from pathlib import Path
from urllib.parse import urlparse
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
from rag.observability import start_observation, record_feedback

limiter = get_limiter()
app_instance_limiter = limiter  # Will be assigned after app creation

# ── Initialize database on import ──
from database.db import (
    init_db, authenticate_user, create_user, get_all_users,
    toggle_user_active, delete_user, add_document, get_all_documents,
    delete_document, log_query, get_query_logs, get_analytics, get_connection, log_feedback,
    log_trace_event, get_trace_events, get_trace_event_summary,
    store_memory, invalidate_memory_by_source,
    get_memory_stats,
    store_document_question_suggestions,
    get_all_rate_limits, get_rate_limit, update_rate_limit, toggle_rate_limit, reset_rate_limits_to_default,
    get_suggestions, create_announcement, get_recent_announcements,
)
from rag.memory import delete_memory_entry, cleanup_old_memory, clear_all_memory as clear_all_cache_memory
from tests.config import (
    UPLOAD_DIR, SUPPORTED_EXTENSIONS, EMBEDDING_MODEL,
    CHROMA_PERSIST_DIR, LLM_MODE, BASE_DIR, CONV_ENABLED, ADMIN_USERNAME,
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


def _route_query(query: str):
    from rag.query_router import classify_query_route

    return classify_query_route(query)


def _search_query_with_history(user_id: str, query: str) -> str:
    from rag.conversation_history import get_history

    history = get_history(user_id)
    search_query = query
    if history:
        previous_queries = " ".join([q for q, r in history])
        search_query = f"{previous_queries} {query}"
    return search_query


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
    route_mode: Optional[str] = None
    transcribed_text: Optional[str] = None
    trace_id: Optional[str] = None

class FeedbackRequest(BaseModel):
    trace_id: str
    rating: int  # 1 helpful, -1 not helpful
    user_id: Optional[str] = None
    comment: Optional[str] = None

class IngestUrlRequest(BaseModel):
    url: str
    title: Optional[str] = None
    uploaded_by: Optional[str] = None
    crawl_site: bool = False
    max_pages: int = 25
    max_depth: int = 2
    delay_seconds: float = 0.5

class FAQEntryRequest(BaseModel):
    question: str
    answer: str
    metadata: Optional[dict] = None

class FAQBulkRequest(BaseModel):
    entries: list[FAQEntryRequest]

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
    system_prompt: Optional[str] = None


def _safe_site_filename(domain: str, page_url: str, title: str | None = None, index: int | None = None) -> str:
    """Build a stable, filesystem-safe filename for crawled pages."""
    parsed = urlparse(page_url)
    path_bits = (parsed.path.strip("/") or "home").split("/")
    path_slug = "_".join(path_bits)
    if title:
        title_slug = re.sub(r"[^a-zA-Z0-9]+", "_", title).strip("_")
        if title_slug:
            path_slug = title_slug
    path_slug = re.sub(r"[^a-zA-Z0-9]+", "_", path_slug).strip("_") or "page"
    suffix = f"_{index}" if index is not None else ""
    return f"web_{domain}_{path_slug[:60]}{suffix}.html"


def _resolve_document_owner_id(uploaded_by: str | None) -> str:
    """Resolve a valid user id for document ownership."""
    if uploaded_by:
        return uploaded_by

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ? AND is_active = 1",
            (ADMIN_USERNAME,),
        ).fetchone()
        if row:
            return row["id"]

        row = conn.execute(
            "SELECT id FROM users WHERE role = 'admin' AND is_active = 1 ORDER BY created_at ASC LIMIT 1",
        ).fetchone()
        if row:
            return row["id"]
    finally:
        conn.close()

    raise HTTPException(
        status_code=422,
        detail="No active admin account is available to own crawled documents",
    )


def _extract_zero_ai_metadata(url_or_filename: str) -> tuple[str | None, str | None]:
    """
    Zero-AI metadata extraction based on URL or filename heuristics.
    Returns (department, document_type).
    """
    if not url_or_filename:
        return None, None

    text = url_or_filename.lower()
    department = None
    document_type = None

    # Department rules
    if "library" in text:
        department = "library"
    elif "admission" in text:
        department = "admissions"
    elif "placement" in text:
        department = "placements"
    elif "hostel" in text:
        department = "hostel"

    # Document type rules
    if "policy" in text or "rules" in text:
        document_type = "policy"
    elif "syllabus" in text:
        document_type = "syllabus"
    elif "schedule" in text or "calendar" in text or "timetable" in text:
        document_type = "schedule"

    return department, document_type


def _ingest_official_site_page(page: dict, uploaded_by: str | None, source_hint: str | None = None, index: int | None = None) -> dict:
    """Store one official-site page in SQLite, ChromaDB, and suggestion cache."""
    from ingestion.chunker import chunk_document
    from ingestion.embedder import store_chunks
    from ingestion.question_suggester import generate_document_questions

    page_url = page["url"]
    page_domain = page.get("domain") or (urlparse(page_url).hostname or "site").lower().removeprefix("www.")
    page_title = page.get("title") or source_hint or page_url
    page_text = page.get("text", "")
    page_file_size = int(page.get("file_size") or len(page_text.encode("utf-8")))
    owner_id = _resolve_document_owner_id(uploaded_by)

    department, document_type = _extract_zero_ai_metadata(page_url)

    chunks = chunk_document(
        page_text,
        source_name=page_title,
        source_type="official_site",
        source_url=page_url,
        source_domain=page_domain,
        page_title=page_title,
        department=department,
        document_type=document_type,
    )
    if not chunks:
        raise HTTPException(status_code=422, detail=f"No chunks generated from website page: {page_title}")

    suggested_questions = generate_document_questions(page_title, page_text, chunks, limit=10)

    doc_id = add_document(
        filename=_safe_site_filename(page_domain, page_url, page_title, index=index),
        original_name=page_title,
        file_type="web",
        file_size=page_file_size,
        chunk_count=len(chunks),
        uploaded_by=owner_id,
        source_type="official_site",
        source_domain=page_domain,
        source_url=page_url,
    )

    stored = store_chunks(chunks, doc_id)
    stored_q = store_document_question_suggestions(
        document_id=doc_id,
        questions=suggested_questions,
        source_hint=source_hint or page_url,
    )

    return {
        "doc_id": doc_id,
        "url": page_url,
        "domain": page_domain,
        "title": page_title,
        "chunks_indexed": stored,
        "suggested_questions": suggested_questions,
        "questions_indexed": stored_q,
        "file_size": page_file_size,
    }


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


@app.delete("/api/announcements/{announcement_id}")
def api_delete_announcement(announcement_id: str, request: Request):
    """Delete an announcement. Admins can delete any; authors can delete their own."""
    from database.db import delete_announcement
    
    user_id = request.headers.get("X-User-ID", "")
    user_role = request.headers.get("X-User-Role", "")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    success = delete_announcement(announcement_id, user_id, user_role)
    if not success:
        raise HTTPException(status_code=404, detail="Announcement not found or you don't have permission to delete it")
    
    logger.info(f"Announcement {announcement_id} deleted by user {user_id}")
    return {"message": "Announcement deleted", "id": announcement_id}

@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("5/minute")  # Expensive LLM operation - strict limit
def api_chat(req: ChatRequest, request: Request):
    """Send a query through the RAG pipeline and get a response."""
    from rag.retriever import retrieve_context, format_context_for_llm, get_source_citations
    from rag.faq_retriever import retrieve_faq_context
    from rag.generator import generate_response, generate_response_direct
    from rag.pipeline_trace import PipelineTrace

    start_time = time.time()
    route = _route_query(req.query)
    obs_trace = start_observation(
        name="api.chat",
        user_id=req.user_id,
        input_payload={
            "query_preview": req.query[:200],
            "username": req.username,
        },
        metadata={
            "endpoint": "/api/chat",
            "voice": False,
            "route_mode": route.mode,
        },
    )

    try:
        # --- Announcement Feature Intercept ---
        if req.query.strip().lower().startswith("@announcement"):
            from database.db import get_connection
            conn = get_connection()
            user_row = conn.execute("SELECT role FROM users WHERE id = ?", (req.user_id,)).fetchone()
            conn.close()

            if not user_row or user_row['role'] not in ('admin', 'faculty'):
                raise HTTPException(status_code=403, detail="Only faculty and admins can post announcements")

            # Bypass RAG AND memory cache — call LLM directly so each announcement is unique
            from rag.providers.manager import get_manager
            from tests.config import SYSTEM_PROMPT, MODEL_TEMPERATURE, MODEL_MAX_TOKENS

            raw_text = req.query[13:].strip()
            announcement_prompt = (
                "You are an institutional announcer. Please format the following raw text "
                "into a professional, clear, and engaging announcement with suitable emojis. "
                "Do not add conversational filler, just output the announcement text.\n\n"
                f"Raw text: {raw_text}"
            )

            mgr = get_manager()
            formatted_announcement = mgr.generate(
                system_prompt=SYSTEM_PROMPT,
                user_message=announcement_prompt,
                temperature=MODEL_TEMPERATURE,
                max_tokens=MODEL_MAX_TOKENS,
            )

            if not formatted_announcement:
                formatted_announcement = f"📢 **New Announcement**\n\n{req.query[13:].strip()}"

            create_announcement(req.user_id, req.username, formatted_announcement)

            elapsed_ms = (time.time() - start_time) * 1000
            obs_trace.end(
                metadata={
                    "announcement_post": True,
                    "elapsed_ms": round(elapsed_ms, 2),
                    "status": "ok",
                }
            )
            try:
                log_trace_event(
                    trace_id=obs_trace.trace_id,
                    endpoint="/api/chat",
                    user_id=req.user_id,
                    username=req.username,
                    status="ok",
                    query_preview=req.query,
                    response_time_ms=elapsed_ms,
                    route_mode="announcement",
                    retrieval_mode="announcement",
                    chunks_count=0,
                    provider="",
                    model="",
                )
            except Exception as event_exc:
                logger.warning("Failed to log trace monitor event: %s", event_exc)
            return ChatResponse(
                response="✅ Announcement generated and posted successfully!\n\n---\n\n" + formatted_announcement,
                sources=[],
                citations="",
                response_time_ms=round(elapsed_ms, 1),
                trace_id=obs_trace.trace_id,
            )

        # ── Pipeline Trace (terminal transparency for jury demo) ──
        trace = PipelineTrace(query=req.query, username=req.username)
        trace.record_route(route.mode, confidence=route.confidence, reason=route.reason)

        chunks = []
        citations = ""
        if route.mode == "timetable":
            from rag.tools.timetable_agent import execute_timetable_agent
            response_text = execute_timetable_agent(req.query, trace=trace)
            gen_result = {"response": response_text, "from_memory": False}
        elif route.mode == "general_chat":
            # Bypass retrieval for non-institutional small-talk/general questions.
            gen_result = generate_response_direct(req.query, user_id=req.user_id)
        else:
            search_query = _search_query_with_history(req.user_id, req.query)
            if route.mode == "faq":
                chunks = retrieve_faq_context(req.query)
                if not chunks:
                    chunks = retrieve_context(
                        search_query, trace=trace, obs_trace=obs_trace, source_type=route.source_type, 
                        filters=route.filters, complexity_score=route.complexity_score
                    )
            else:
                chunks = retrieve_context(
                    search_query, trace=trace, obs_trace=obs_trace, source_type=route.source_type,
                    filters=route.filters, complexity_score=route.complexity_score
                )

            # Step 2: Format context for LLM
            context = format_context_for_llm(chunks)

            # Step 3: Generate response (now includes memory handling)
            gen_result = generate_response(
                req.query,
                context,
                user_id=req.user_id,
                sources=[c.get("source", "") for c in chunks],
                trace=trace,
                obs_trace=obs_trace,
                route_mode=route.memory_scope,
            )
            citations = get_source_citations(chunks)

        # Extract response from dict
        response_text = gen_result.get("response", "") if isinstance(gen_result, dict) else gen_result
        from_memory = gen_result.get("from_memory", False) if isinstance(gen_result, dict) else False

        elapsed_ms = (time.time() - start_time) * 1000

        # Record final response stats and print trace to terminal
        unique_sources = len(set(c.get("source", "") for c in chunks))
        trace.record_response(
            response_length=len(response_text) if response_text else 0,
            unique_sources=unique_sources,
            from_memory=from_memory,
        )
        trace.print_summary()

        # Store turn in conversation history for follow-up support
        from rag.conversation_history import add_turn
        if response_text and req.user_id:
            add_turn(req.user_id, req.query, response_text)

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

        obs_trace.end(
            metadata={
                "status": "ok",
                "from_memory": from_memory,
                "elapsed_ms": round(elapsed_ms, 2),
                "sources_count": unique_sources,
            },
            output={
                "response_chars": len(response_text) if response_text else 0,
            },
        )

        try:
            retrieval_scores = [float(c.get("score", 0.0)) for c in chunks if isinstance(c.get("score", 0.0), (int, float))]
            retrieval_methods = {str(c.get("retrieval_method", "dense")) for c in chunks}
            hyde_applied = any("hyde" in m for m in retrieval_methods)
            retrieval_mode = "hybrid" if any(("hybrid" in m or "bm25" in m) for m in retrieval_methods) else "dense"
            providers_tried = [
                {"name": name, "success": bool(ok)}
                for name, ok in (trace.providers_tried or [])
            ]

            log_trace_event(
                trace_id=obs_trace.trace_id,
                endpoint="/api/chat",
                user_id=req.user_id,
                username=req.username,
                status="ok",
                query_preview=req.query,
                response_time_ms=elapsed_ms,
                route_mode=route.mode,
                retrieval_top_score=max(retrieval_scores) if retrieval_scores else None,
                retrieval_avg_score=(sum(retrieval_scores) / len(retrieval_scores)) if retrieval_scores else None,
                retrieval_mode=retrieval_mode,
                hyde_applied=hyde_applied,
                chunks_count=len(chunks),
                from_memory=from_memory,
                provider=trace.provider_used or "",
                model=trace.model_used or "",
                fallback_chain=providers_tried,
            )
        except Exception as event_exc:
            logger.warning("Failed to log trace monitor event: %s", event_exc)

        return ChatResponse(
            response=response_text,
            sources=chunks,
            citations=citations,
            response_time_ms=round(elapsed_ms, 1),
            route_mode=route.mode,
            trace_id=obs_trace.trace_id,
        )
    except HTTPException as exc:
        obs_trace.end(
            metadata={
                "status": "http_error",
                "status_code": exc.status_code,
            },
            error=str(exc.detail),
        )
        try:
            elapsed_ms = (time.time() - start_time) * 1000
            log_trace_event(
                trace_id=obs_trace.trace_id,
                endpoint="/api/chat",
                user_id=req.user_id,
                username=req.username,
                status="http_error",
                query_preview=req.query,
                response_time_ms=elapsed_ms,
                route_mode=route.mode,
                error_message=str(exc.detail),
            )
        except Exception as event_exc:
            logger.warning("Failed to log trace monitor event: %s", event_exc)
        raise
    except Exception as exc:
        obs_trace.end(
            metadata={
                "status": "error",
            },
            error=str(exc),
        )
        try:
            elapsed_ms = (time.time() - start_time) * 1000
            log_trace_event(
                trace_id=obs_trace.trace_id,
                endpoint="/api/chat",
                user_id=req.user_id,
                username=req.username,
                status="error",
                query_preview=req.query,
                response_time_ms=elapsed_ms,
                route_mode=route.mode,
                error_message=str(exc),
            )
        except Exception as event_exc:
            logger.warning("Failed to log trace monitor event: %s", event_exc)
        raise


@app.post("/api/chat/stream")
@limiter.limit("5/minute")
async def api_chat_stream(req: ChatRequest, request: Request):
    """Send a query through the RAG pipeline and get a streaming response via SSE."""
    from rag.retriever import retrieve_context, format_context_for_llm, get_source_citations
    from rag.faq_retriever import retrieve_faq_context
    from rag.generator import generate_response_stream, generate_response_direct_stream
    from rag.pipeline_trace import PipelineTrace
    from rag.conversation_history import add_turn
    from fastapi.responses import StreamingResponse
    import json
    import asyncio

    start_time = time.time()
    route = _route_query(req.query)
    
    obs_trace = start_observation(
        name="api.chat.stream",
        user_id=req.user_id,
        input_payload={"query_preview": req.query[:200], "username": req.username},
        metadata={"endpoint": "/api/chat/stream", "voice": False, "route_mode": route.mode},
    )

    async def event_stream():
        try:
            # --- Announcement Feature Intercept ---
            if req.query.strip().lower().startswith("@announcement"):
                from database.db import get_connection
                conn = get_connection()
                user_row = conn.execute("SELECT role FROM users WHERE id = ?", (req.user_id,)).fetchone()
                conn.close()

                if not user_row or user_row['role'] not in ('admin', 'faculty'):
                    yield f"data: {json.dumps({'error': 'Only faculty and admins can post announcements'})}\n\n"
                    return

                from rag.providers.manager import get_manager
                from tests.config import SYSTEM_PROMPT, MODEL_TEMPERATURE, MODEL_MAX_TOKENS

                raw_text = req.query[13:].strip()
                announcement_prompt = (
                    "You are an institutional announcer. Please format the following raw text "
                    "into a professional, clear, and engaging announcement with suitable emojis. "
                    "Do not add conversational filler, just output the announcement text.\n\n"
                    f"Raw text: {raw_text}"
                )

                mgr = get_manager()
                stream = mgr.generate_stream(
                    system_prompt=SYSTEM_PROMPT,
                    user_message=announcement_prompt,
                    temperature=MODEL_TEMPERATURE,
                    max_tokens=MODEL_MAX_TOKENS,
                )
                
                full_text = "✅ Announcement generated and posted successfully!\n\n---\n\n"
                yield f"data: {json.dumps({'chunk': full_text})}\n\n"
                
                generated_announcement = ""
                if stream:
                    for chunk in stream:
                        generated_announcement += chunk
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                        await asyncio.sleep(0.01)
                else:
                    generated_announcement = f"📢 **New Announcement**\n\n{req.query[13:].strip()}"
                    yield f"data: {json.dumps({'chunk': generated_announcement})}\n\n"

                create_announcement(req.user_id, req.username, generated_announcement)
                yield f"data: {json.dumps({'done': True})}\n\n"
                return

            trace = PipelineTrace(query=req.query, username=req.username)
            trace.record_route(route.mode, confidence=route.confidence, reason=route.reason)

            chunks = []
            citations = ""
            
            if route.mode == "timetable":
                from rag.tools.timetable_agent import execute_timetable_agent
                response_text = execute_timetable_agent(req.query, trace=trace)
                yield f"data: {json.dumps({'chunk': response_text, 'done': False})}\n\n"
                yield f"data: {json.dumps({'done': True, 'citations': '', 'sources': []})}\n\n"
                return

            elif route.mode == "general_chat":
                gen_stream = generate_response_direct_stream(req.query, user_id=req.user_id)
            else:
                search_query = _search_query_with_history(req.user_id, req.query)
                if route.mode == "faq":
                    chunks = retrieve_faq_context(req.query)
                    if not chunks:
                        chunks = retrieve_context(
                            search_query, trace=trace, obs_trace=obs_trace, source_type=route.source_type, 
                            filters=route.filters, complexity_score=route.complexity_score
                        )
                else:
                    chunks = retrieve_context(
                        search_query, trace=trace, obs_trace=obs_trace, source_type=route.source_type,
                        filters=route.filters, complexity_score=route.complexity_score
                    )

                context = format_context_for_llm(chunks)
                gen_stream = generate_response_stream(
                    req.query,
                    context,
                    user_id=req.user_id,
                    sources=[c.get("source", "") for c in chunks],
                    trace=trace,
                    obs_trace=obs_trace,
                    route_mode=route.memory_scope,
                )
                citations = get_source_citations(chunks)

            full_response = ""
            from_memory = False
            for item in gen_stream:
                if item.get("chunk"):
                    chunk_text = item["chunk"]
                    full_response += chunk_text
                    yield f"data: {json.dumps({'chunk': chunk_text, 'from_memory': item.get('from_memory', False)})}\n\n"
                    await asyncio.sleep(0.005)
                
                if item.get("done"):
                    from_memory = item.get("from_memory", False)
                    break
            
            final_data = {
                "done": True,
                "citations": citations,
                "sources": chunks,
                "from_memory": from_memory,
                "route_mode": route.mode
            }
            yield f"data: {json.dumps(final_data)}\n\n"
            
            elapsed_ms = (time.time() - start_time) * 1000
            if full_response and req.user_id:
                add_turn(req.user_id, req.query, full_response)
                
            try:
                source_names = ", ".join([c.get("source", "") for c in chunks[:3]])
                log_response_text = f"[⚡ CACHED] {full_response}" if from_memory else full_response
                log_query(
                    user_id=req.user_id,
                    username=req.username,
                    query_text=req.query,
                    response_text=log_response_text[:500],
                    sources=source_names,
                    response_time_ms=elapsed_ms,
                )
            except Exception as e:
                logger.error(f"Error logging query: {e}")
                
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


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
    from rag.faq_retriever import retrieve_faq_context
    from rag.generator import generate_response, generate_response_direct
    from rag.pipeline_trace import PipelineTrace
    import shutil
    from rag.voice_to_text import transcribe_audio

    start_time = time.time()
    route = None
    obs_trace = start_observation(
        name="api.chat.audio",
        user_id=user_id,
        input_payload={
            "audio_filename": audio.filename,
            "username": username,
        },
        metadata={
            "endpoint": "/api/chat/audio",
            "voice": True,
            "route_mode": "pending",
        },
    )

    try:
        audio_filename = audio.filename or "audio.webm"
        file_ext = Path(audio_filename).suffix.lower()
        if not file_ext:
            file_ext = ".webm"  # Default from browser

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
        route = _route_query(transcribed_text)

        # ── Pipeline Trace (terminal transparency for jury demo) ──
        trace = PipelineTrace(query=f"[🎤 VOICE] {transcribed_text}", username=username)
        trace.record_route(route.mode, confidence=route.confidence, reason=route.reason)

        chunks = []
        citations = ""
        if route.mode == "timetable":
            from rag.tools.timetable_agent import execute_timetable_agent
            response_text = execute_timetable_agent(transcribed_text, trace=trace)
            gen_result = {"response": response_text, "from_memory": False}
        elif route.mode == "general_chat":
            gen_result = generate_response_direct(transcribed_text, user_id=user_id)
        else:
            search_query = _search_query_with_history(user_id, transcribed_text)
            if route.mode == "faq":
                chunks = retrieve_faq_context(transcribed_text)
                if not chunks:
                    chunks = retrieve_context(
                        search_query, trace=trace, obs_trace=obs_trace, source_type=route.source_type,
                        filters=route.filters, complexity_score=route.complexity_score
                    )
            else:
                chunks = retrieve_context(
                    search_query, trace=trace, obs_trace=obs_trace, source_type=route.source_type,
                    filters=route.filters, complexity_score=route.complexity_score
                )
            context = format_context_for_llm(chunks)

            gen_result = generate_response(
                transcribed_text,
                context,
                user_id=user_id,
                sources=[c.get("source", "") for c in chunks],
                trace=trace,
                obs_trace=obs_trace,
                route_mode=route.memory_scope,
            )
            citations = get_source_citations(chunks)

        response_text = gen_result.get("response", "") if isinstance(gen_result, dict) else gen_result
        from_memory = gen_result.get("from_memory", False) if isinstance(gen_result, dict) else False
        elapsed_ms = (time.time() - start_time) * 1000

        # Record final response stats and print trace to terminal
        unique_sources = len(set(c.get("source", "") for c in chunks))
        trace.record_response(
            response_length=len(response_text) if response_text else 0,
            unique_sources=unique_sources,
            from_memory=from_memory,
        )
        trace.print_summary()

        # Store turn in conversation history for follow-up support
        from rag.conversation_history import add_turn
        if response_text and user_id:
            add_turn(user_id, transcribed_text, response_text)

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

        obs_trace.end(
            metadata={
                "status": "ok",
                "from_memory": from_memory,
                "elapsed_ms": round(elapsed_ms, 2),
                "sources_count": unique_sources,
            },
            output={
                "response_chars": len(response_text) if response_text else 0,
                "transcribed_chars": len(transcribed_text),
            },
        )

        try:
            retrieval_scores = [float(c.get("score", 0.0)) for c in chunks if isinstance(c.get("score", 0.0), (int, float))]
            retrieval_methods = {str(c.get("retrieval_method", "dense")) for c in chunks}
            hyde_applied = any("hyde" in m for m in retrieval_methods)
            retrieval_mode = "hybrid" if any(("hybrid" in m or "bm25" in m) for m in retrieval_methods) else "dense"
            providers_tried = [
                {"name": name, "success": bool(ok)}
                for name, ok in (trace.providers_tried or [])
            ]

            log_trace_event(
                trace_id=obs_trace.trace_id,
                endpoint="/api/chat/audio",
                user_id=user_id,
                username=username,
                status="ok",
                query_preview=transcribed_text,
                response_time_ms=elapsed_ms,
                route_mode=route.mode,
                retrieval_top_score=max(retrieval_scores) if retrieval_scores else None,
                retrieval_avg_score=(sum(retrieval_scores) / len(retrieval_scores)) if retrieval_scores else None,
                retrieval_mode=retrieval_mode,
                hyde_applied=hyde_applied,
                chunks_count=len(chunks),
                from_memory=from_memory,
                provider=trace.provider_used or "",
                model=trace.model_used or "",
                fallback_chain=providers_tried,
            )
        except Exception as event_exc:
            logger.warning("Failed to log trace monitor event: %s", event_exc)

        return ChatResponse(
            response=response_text,
            sources=chunks,
            citations=citations,
            response_time_ms=round(elapsed_ms, 1),
            transcribed_text=transcribed_text,
            route_mode=route.mode,
            trace_id=obs_trace.trace_id,
        )
    except HTTPException as exc:
        obs_trace.end(
            metadata={
                "status": "http_error",
                "status_code": exc.status_code,
            },
            error=str(exc.detail),
        )
        try:
            elapsed_ms = (time.time() - start_time) * 1000
            log_trace_event(
                trace_id=obs_trace.trace_id,
                endpoint="/api/chat/audio",
                user_id=user_id,
                username=username,
                status="http_error",
                query_preview="",
                response_time_ms=elapsed_ms,
                route_mode=route.mode if route else "",
                error_message=str(exc.detail),
            )
        except Exception as event_exc:
            logger.warning("Failed to log trace monitor event: %s", event_exc)
        raise
    except Exception as exc:
        obs_trace.end(
            metadata={
                "status": "error",
            },
            error=str(exc),
        )
        try:
            elapsed_ms = (time.time() - start_time) * 1000
            log_trace_event(
                trace_id=obs_trace.trace_id,
                endpoint="/api/chat/audio",
                user_id=user_id,
                username=username,
                status="error",
                query_preview="",
                response_time_ms=elapsed_ms,
                route_mode=route.mode if route else "",
                error_message=str(exc),
            )
        except Exception as event_exc:
            logger.warning("Failed to log trace monitor event: %s", event_exc)
        raise


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
def api_get_suggestions(request: Request, q: str = "", user_id: Optional[str] = None):
    """Get autocomplete suggestions for the chat input.
    
    Returns recent user questions, popular questions,
    document-derived suggestions, and preset suggestions.
    """
    result = get_suggestions(query_prefix=q, user_id=user_id)
    return result


@app.post("/api/feedback")
@limiter.limit("30/minute")
def api_submit_feedback(req: FeedbackRequest, request: Request):
    """Submit user feedback tied to a trace id for observability and quality tuning."""
    if req.rating not in (-1, 1):
        raise HTTPException(status_code=400, detail="rating must be 1 or -1")

    user_id = req.user_id or get_user_id(request)

    accepted = record_feedback(
        trace_id=req.trace_id,
        rating=float(req.rating),
        comment=req.comment,
        metadata={
            "user_id": user_id,
            "source": "chat_ui",
        },
    )

    try:
        feedback_id = log_feedback(
            trace_id=req.trace_id,
            user_id=user_id,
            rating=req.rating,
            comment=req.comment or "",
            source="chat_ui",
            recorded_in_langfuse=bool(accepted),
        )
    except Exception as exc:
        logger.error("Failed to persist feedback", extra={"trace_id": req.trace_id}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to persist feedback: {str(exc)}")

    return {
        "accepted": True,
        "trace_id": req.trace_id,
        "feedback_id": feedback_id,
        "langfuse_recorded": bool(accepted),
    }



# ═══════════════════════════════════════════════════════
# DOCUMENT MANAGEMENT ENDPOINTS
# ═══════════════════════════════════════════════════════

@app.post("/api/documents/upload")
@limiter.limit("10/minute")  # File uploads are I/O intensive
def api_upload_document(
    request: Request,  # Required for rate limiter key extraction
    file: UploadFile = File(...),
    uploaded_by: Optional[str] = Form(None),  # Make it optional with default None
):
    """Upload, parse, chunk, and index a document (admin only if uploaded_by is provided)."""
    from ingestion.parser import parse_document
    from ingestion.chunker import chunk_document
    from ingestion.embedder import store_chunks
    from ingestion.question_suggester import generate_document_questions

    # ── Admin-only check (only if uploaded_by is provided) ──
    if uploaded_by:
        conn = get_connection()
        user = conn.execute("SELECT id, role FROM users WHERE id = ?", (uploaded_by,)).fetchone()
        conn.close()

        if not user:
            raise HTTPException(status_code=404, detail=f"User ID {uploaded_by} not found")

        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only administrators can upload documents")

    original_filename = file.filename or "uploaded_file"
    file_ext = Path(original_filename).suffix.lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}")

    # Save file to disk
    safe_name = f"{int(time.time())}_{original_filename}"
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
                logger.warning(f"Locked PDF rejected: {original_filename}")
                raise HTTPException(
                    status_code=422,
                    detail=f"❌ PDF is password-protected. Please remove the password and try again."
                )
        except HTTPException:
            raise  # Re-raise our custom error
        except Exception as e:
            logger.debug(f"PDF encryption check error for {original_filename}: {e}")
            # Don't block on encryption check errors, let parsing handle it

    # Parse document
    text, parse_error = parse_document(str(file_path))
    if not text:
        os.remove(file_path)
        error_detail = parse_error or "Failed to extract text from document"
        logger.warning(f"Document parse failed for {original_filename}: {error_detail}")
        raise HTTPException(status_code=422, detail=error_detail)

    # Chunk document
    chunks = chunk_document(text, source_name=original_filename)
    if not chunks:
        os.remove(file_path)
        raise HTTPException(status_code=422, detail="No chunks generated from document (text may be too short)")

    # Build question suggestions from uploaded content
    suggested_questions = generate_document_questions(original_filename, text, chunks, limit=10)

    # Record in database
    try:
        doc_id = add_document(
            filename=safe_name,
            original_name=original_filename,
            file_type=file_ext,
            file_size=len(content),
            chunk_count=len(chunks),
            uploaded_by=uploaded_by,
        )
    except Exception as e:
        os.remove(file_path)
        logger.error(f"Database error for {original_filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record document in database: {str(e)}")

    # Store embeddings in ChromaDB
    try:
        stored = store_chunks(chunks, doc_id)
    except Exception as e:
        logger.error(f"ChromaDB error for doc {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to index document in vector database: {str(e)}")

    # Persist upload-derived suggested questions (best-effort, non-blocking for upload)
    try:
        stored_q = store_document_question_suggestions(
            document_id=doc_id,
            questions=suggested_questions,
            source_hint=original_filename,
        )
    except Exception as exc:
        stored_q = 0
        logger.warning(
            "Failed to persist document question suggestions",
            extra={"doc_id": doc_id, "doc_filename": file.filename, "error": str(exc)},
        )

    logger.info(
        "Document upload indexed",
        extra={
            "doc_id": doc_id,
            "doc_filename": file.filename,
            "chunks_indexed": stored,
            "suggested_questions": stored_q,
        },
    )

    return {
        "doc_id": doc_id,
        "filename": file.filename,
        "chunks_indexed": stored,
        "file_size": len(content),
        "suggested_questions": suggested_questions[:6],
    }


@app.post("/api/documents/timetable/upload")
@limiter.limit("10/minute")
def api_upload_timetable(
    request: Request,
    class_name: str = Form(...),
    file: UploadFile = File(...),
    uploaded_by: Optional[str] = Form(None),
):
    """Upload and parse a timetable (admin/faculty only)."""
    if uploaded_by:
        conn = get_connection()
        user = conn.execute("SELECT id, role FROM users WHERE id = ?", (uploaded_by,)).fetchone()
        conn.close()

        if not user:
            raise HTTPException(status_code=404, detail=f"User ID {uploaded_by} not found")

        if user["role"] not in ("admin", "faculty"):
            raise HTTPException(status_code=403, detail="Only faculty and administrators can upload timetables")

    original_filename = file.filename or "timetable.csv"
    file_ext = Path(original_filename).suffix.lower()
    
    if file_ext not in (".csv", ".xlsx"):
        raise HTTPException(status_code=400, detail="Only .csv and .xlsx files are supported for timetables")

    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    from ingestion.timetable_parser import parse_timetable_to_entries
    try:
        entries = parse_timetable_to_entries(content, file_ext, class_name)
    except Exception as e:
        logger.error(f"Failed to parse timetable: {e}")
        raise HTTPException(status_code=422, detail=f"Failed to parse timetable: {str(e)}")

    if not entries:
        raise HTTPException(status_code=422, detail="No schedule entries found. Check your file format.")

    from database.db import add_timetable_entry, clear_timetable
    try:
        # Clear existing timetable for this class to prevent duplicates
        deleted = clear_timetable(class_name)
        
        for entry in entries:
            add_timetable_entry(
                class_name=entry["class_name"],
                day=entry["day"],
                start_time=entry["start_time"],
                end_time=entry["end_time"],
                subject=entry["subject"],
                room=entry["room"],
                uploaded_by=uploaded_by
            )
    except Exception as e:
        logger.error(f"Database error saving timetable: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save timetable to database: {str(e)}")

    return {
        "status": "success",
        "class_name": class_name,
        "entries_saved": len(entries),
        "deleted_old_entries": deleted,
    }


@app.post("/api/admin/upload/students")
@limiter.limit("10/minute")
def api_upload_students(
    request: Request,
    file: UploadFile = File(...),
    uploaded_by: Optional[str] = Form(None),
):
    """Upload and parse student master data (admin only)."""
    if uploaded_by:
        conn = get_connection()
        user = conn.execute("SELECT id, role FROM users WHERE id = ?", (uploaded_by,)).fetchone()
        conn.close()

        if not user:
            raise HTTPException(status_code=404, detail=f"User ID {uploaded_by} not found")

        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only administrators can upload student data")

    original_filename = file.filename or "students.csv"
    file_ext = Path(original_filename).suffix.lower()
    
    if file_ext not in (".csv", ".xlsx"):
        raise HTTPException(status_code=400, detail="Only .csv and .xlsx files are supported")

    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    from ingestion.student_parser import parse_students_csv
    from database.student_db import bulk_add_students
    try:
        students_list = parse_students_csv(content, file_ext)
    except Exception as e:
        logger.error(f"Failed to parse students file: {e}")
        raise HTTPException(status_code=422, detail=f"Failed to parse students file: {str(e)}")

    if not students_list:
        raise HTTPException(status_code=422, detail="No student records found. Check your file format.")

    try:
        count_added = bulk_add_students(students_list)
        return {
            "status": "success",
            "students_added": count_added,
            "total_records": len(students_list),
        }
    except Exception as e:
        logger.error(f"Database error saving students: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save students: {str(e)}")


@app.post("/api/admin/upload/marks")
@limiter.limit("10/minute")
def api_upload_marks(
    request: Request,
    file: UploadFile = File(...),
    uploaded_by: Optional[str] = Form(None),
):
    """Upload and parse student marks data (admin/faculty)."""
    if uploaded_by:
        conn = get_connection()
        user = conn.execute("SELECT id, role FROM users WHERE id = ?", (uploaded_by,)).fetchone()
        conn.close()

        if not user:
            raise HTTPException(status_code=404, detail=f"User ID {uploaded_by} not found")

        if user["role"] not in ("admin", "faculty"):
            raise HTTPException(status_code=403, detail="Only admins and faculty can upload marks")

    original_filename = file.filename or "marks.csv"
    file_ext = Path(original_filename).suffix.lower()
    
    if file_ext not in (".csv", ".xlsx"):
        raise HTTPException(status_code=400, detail="Only .csv and .xlsx files are supported")

    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    from ingestion.student_parser import parse_marks_csv
    from database.student_db import bulk_add_student_marks
    try:
        marks_list = parse_marks_csv(content, file_ext)
    except Exception as e:
        logger.error(f"Failed to parse marks file: {e}")
        raise HTTPException(status_code=422, detail=f"Failed to parse marks file: {str(e)}")

    if not marks_list:
        raise HTTPException(status_code=422, detail="No marks records found. Check your file format.")

    try:
        count_added = bulk_add_student_marks(marks_list)
        return {
            "status": "success",
            "marks_added": count_added,
            "total_records": len(marks_list),
        }
    except Exception as e:
        logger.error(f"Database error saving marks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save marks: {str(e)}")


@app.get("/api/admin/students")
@limiter.limit("30/minute")
def api_get_students(request: Request):
    """Return list of students (admin only)."""
    # Basic role check via header user id — keep simple for now
    user_id = get_user_id(request)
    conn = get_connection()
    try:
        row = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row or row[0] != 'admin':
            raise HTTPException(status_code=403, detail="Only administrators can list students")
    finally:
        conn.close()

    from database.db import get_connection as _get_conn
    with _get_conn() as c:
        rows = c.execute("SELECT id, roll_no, name, email, phone, department, semester, gpa, uploaded_at FROM students ORDER BY uploaded_at DESC").fetchall()
    return [dict(r) for r in rows]


@app.post("/api/admin/upload/timetable")
@limiter.limit("10/minute")
def api_upload_timetable(request: Request, file: UploadFile = File(...), uploaded_by: Optional[str] = Form(None)):
    """Upload CSV/XLSX timetable and store entries.
    Admin-only.
    """
    if uploaded_by:
        conn = get_connection()
        user = conn.execute("SELECT id, role FROM users WHERE id = ?", (uploaded_by,)).fetchone()
        conn.close()

        if not user:
            raise HTTPException(status_code=404, detail=f"User ID {uploaded_by} not found")

        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only administrators can upload timetable data")

    original_filename = file.filename or "timetable.csv"
    file_ext = Path(original_filename).suffix.lower()
    if file_ext not in (".csv", ".xlsx"):
        raise HTTPException(status_code=400, detail="Only .csv and .xlsx files are supported")

    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    # Parse timetable
    try:
        from ingestion.timetable_parser import parse_timetable_csv
        entries = parse_timetable_csv(content, file_ext)
    except Exception as e:
        logger.error(f"Failed to parse timetable file: {e}")
        raise HTTPException(status_code=422, detail=f"Failed to parse timetable file: {str(e)}")

    if not entries:
        raise HTTPException(status_code=422, detail="No timetable entries found. Check your file format.")

    # Store entries
    from database.db import add_timetable_entry
    added = 0
    try:
        for row in entries:
            # Map expected fields: course_code or class_name -> class_name, subject -> course_name
            class_name = row.get('class_name') or row.get('course_code') or row.get('course') or ''
            subject = row.get('subject') or row.get('course_name') or row.get('subject_name') or ''
            day = row.get('day') or ''
            start_time = row.get('start_time') or ''
            end_time = row.get('end_time') or ''
            room = row.get('room') or ''
            if not (class_name and subject and day and start_time and end_time):
                continue
            add_timetable_entry(class_name, day, start_time, end_time, subject, room, uploaded_by)
            added += 1
        return {"status": "success", "entries_added": added, "total_records": len(entries)}
    except Exception as e:
        logger.error(f"Database error saving timetable: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save timetable: {str(e)}")


@app.post("/api/documents/ingest-url")
@limiter.limit("10/minute")
def api_ingest_document_url(req: IngestUrlRequest, request: Request):
    """Fetch one official-site page or crawl a whole site and index it locally."""
    from ingestion.web_ingest import fetch_official_site_page, crawl_site_for_ingestion, CrawlConfig

    if req.uploaded_by:
        conn = get_connection()
        user = conn.execute("SELECT id, role FROM users WHERE id = ?", (req.uploaded_by,)).fetchone()
        conn.close()

        if not user:
            raise HTTPException(status_code=404, detail=f"User ID {req.uploaded_by} not found")

        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only administrators can ingest official-site pages")

    if req.crawl_site:
        pages = crawl_site_for_ingestion(
            req.url,
            CrawlConfig(
                max_pages=max(1, min(int(req.max_pages), 500)),
                max_depth=max(0, min(int(req.max_depth), 10)),
                delay_seconds=max(0.0, float(req.delay_seconds)),
            ),
        )
        if not pages:
            raise HTTPException(status_code=422, detail="No pages could be crawled from the provided website")

        indexed_pages = []
        total_chunks = 0
        for index, page in enumerate(pages, start=1):
            if not page.get("text", "").strip():
                continue
            try:
                result = _ingest_official_site_page(
                    page,
                    req.uploaded_by,
                    source_hint=req.title or page.get("title"),
                    index=index,
                )
                indexed_pages.append({
                    "doc_id": result["doc_id"],
                    "url": result["url"],
                    "title": result["title"],
                    "chunks_indexed": result["chunks_indexed"],
                    "questions_indexed": result["questions_indexed"],
                })
                total_chunks += result["chunks_indexed"]
            except HTTPException:
                raise
            except Exception as exc:
                logger.warning("Failed to ingest crawled page", extra={"url": page.get("url"), "error": str(exc)}, exc_info=True)

        if not indexed_pages:
            raise HTTPException(status_code=422, detail="Crawl completed but no pages were indexed")

        return {
            "mode": "crawl",
            "seed_url": req.url,
            "pages_indexed": len(indexed_pages),
            "chunks_indexed": total_chunks,
            "indexed_pages": indexed_pages[:20],
            "source_type": "official_site",
        }

    page = fetch_official_site_page(req.url)
    if not page.get("ok"):
        raise HTTPException(status_code=422, detail=page.get("error", "Failed to ingest website page"))

    result = _ingest_official_site_page(
        page,
        req.uploaded_by,
        source_hint=req.title or page.get("title"),
    )

    return {
        "mode": "single_page",
        "doc_id": result["doc_id"],
        "url": result["url"],
        "domain": result["domain"],
        "title": result["title"],
        "pages_indexed": 1,
        "chunks_indexed": result["chunks_indexed"],
        "source_type": "official_site",
        "suggested_questions": result["suggested_questions"][:6],
    }


@app.post("/api/faq")
@limiter.limit("20/minute")
def api_add_faq(req: FAQEntryRequest, request: Request):
    """Store a single FAQ entry for FAQ-aware retrieval."""
    from rag.faq_retriever import store_faq_entries

    question = (req.question or "").strip()
    answer = (req.answer or "").strip()
    if not question or not answer:
        raise HTTPException(status_code=400, detail="Both question and answer are required")

    payload = {
        "question": question,
        "answer": answer,
        "metadata": req.metadata or {},
    }
    stored = store_faq_entries([payload], source="api_faq")
    return {
        "stored": stored,
        "question": question,
    }


@app.post("/api/faq/bulk")
@limiter.limit("10/minute")
def api_add_faq_bulk(req: FAQBulkRequest, request: Request):
    """Store multiple FAQ entries for FAQ-aware retrieval."""
    from rag.faq_retriever import store_faq_entries

    if not req.entries:
        raise HTTPException(status_code=400, detail="entries cannot be empty")

    entries = [
        {
            "question": (entry.question or "").strip(),
            "answer": (entry.answer or "").strip(),
            "metadata": entry.metadata or {},
        }
        for entry in req.entries
        if (entry.question or "").strip() and (entry.answer or "").strip()
    ]
    if not entries:
        raise HTTPException(status_code=400, detail="No valid FAQ entries provided")

    stored = store_faq_entries(entries, source="api_faq_bulk")
    return {
        "stored": stored,
        "received": len(req.entries),
    }


@app.get("/api/faq/stats")
def api_faq_stats():
    """Get FAQ index statistics."""
    from rag.faq_retriever import get_faq_stats

    stats = get_faq_stats()
    return {
        "total_faq_entries": stats.get("total_entries", 0),
    }


@app.post("/api/faq/clear")
@limiter.limit("5/minute")
def api_clear_faq(request: Request):
    """Clear all FAQ entries from the FAQ index."""
    from rag.faq_retriever import clear_faq_entries

    deleted = clear_faq_entries()
    return {
        "deleted": deleted,
        "message": "FAQ index cleared",
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
@app.get("/api/knowledge-base/stats")
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
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None

class ClassificationRequest(BaseModel):
    classification: str
    confidence: float = 1.0
    auto_classified: bool = False
    notes: Optional[str] = None

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
def api_search_documents(
    request: Request,
    tags: Optional[str] = None,
    classification: Optional[str] = None,
):
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


@app.get("/api/monitor/traces")
@limiter.limit("30/minute")
def api_monitor_traces(
    request: Request,
    limit: int = 120,
    status: Optional[str] = None,
    endpoint: Optional[str] = None,
    provider: Optional[str] = None,
):
    """Get recent trace timeline items for admin trace monitor UI."""
    safe_limit = max(1, min(int(limit), 500))
    items = get_trace_events(
        limit=safe_limit,
        status=status,
        endpoint=endpoint,
        provider=provider,
    )
    return {
        "items": items,
        "count": len(items),
    }


@app.get("/api/monitor/overview")
@limiter.limit("30/minute")
def api_monitor_overview(
    request: Request,
    minutes: int = 60,
    include_providers: bool = False,
):
    """Get consolidated monitor view to detect subsystem issues quickly."""
    window_minutes = max(5, min(int(minutes), 24 * 60))
    trace_summary = get_trace_event_summary(window_minutes)
    health = api_health()
    provider_statuses = api_provider_statuses() if include_providers else {}

    system_alerts = []

    for name, comp in (health.get("components") or {}).items():
        status_val = str((comp or {}).get("status", "error"))
        message = str((comp or {}).get("message", ""))
        if status_val in ("error", "warning", "degraded"):
            system_alerts.append({
                "type": "component",
                "name": name,
                "status": status_val,
                "message": message,
            })

    for row in trace_summary.get("by_endpoint", []):
        failed = int(row.get("failed", 0) or 0)
        total = int(row.get("total", 0) or 0)
        if failed <= 0:
            continue
        fail_rate = (failed / total * 100.0) if total else 0.0
        system_alerts.append({
            "type": "endpoint",
            "name": row.get("endpoint", "unknown"),
            "status": "error" if fail_rate >= 20 else "warning",
            "message": f"{failed}/{total} failed in last {window_minutes}m ({fail_rate:.1f}%)",
        })

    if include_providers:
        for provider_name, provider_info in (provider_statuses or {}).items():
            if provider_name.startswith("_"):
                continue
            provider_state = str((provider_info or {}).get("status", "error"))
            if provider_state in ("error", "warning", "degraded"):
                system_alerts.append({
                    "type": "provider",
                    "name": provider_name,
                    "status": provider_state,
                    "message": str((provider_info or {}).get("message", "")),
                })

    overall = "healthy"
    if any(a.get("status") == "error" for a in system_alerts):
        overall = "unhealthy"
    elif system_alerts:
        overall = "degraded"

    return {
        "status": overall,
        "window_minutes": window_minutes,
        "trace_summary": trace_summary,
        "health": health,
        "providers": provider_statuses,
        "alerts": system_alerts,
    }


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
    import tests.config as config
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
        "system_prompt": "SYSTEM_PROMPT",
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
    """Force-reload config modules so module-level variables pick up new os.environ values."""
    import importlib
    import config as runtime_config
    import tests.config as test_config

    # Reload runtime config first, then compatibility re-export module.
    importlib.reload(runtime_config)
    importlib.reload(test_config)


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
        success = delete_memory_entry(memory_id)
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
        deleted = cleanup_old_memory()
        return {"deleted": deleted, "message": f"Cleaned up {deleted} expired entries"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/memory/clear")
def api_memory_clear():
    """Clear all conversation memory entries (admin only, use with caution)."""
    if not CONV_ENABLED:
        raise HTTPException(status_code=400, detail="Conversation memory is disabled")
    try:
        success = clear_all_cache_memory()
        return {"cleared": bool(success)}
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


# ═══════════════════════════════════════════════════════
# CUSTOM SQLITE OBSERVABILITY ENDPOINTS
# ═══════════════════════════════════════════════════════

@app.get("/api/admin/observability/traces")
@limiter.limit(RATE_LIMIT_ADMIN_TIER)
def api_get_observability_traces(request: Request, limit: int = 50, skip: int = 0, days: int = 7):
    """Fetch recent observability traces from SQLite."""
    from database.db import get_traces

    try:
        traces = get_traces(limit=limit, offset=skip, days=days)
        return {
            "traces": traces,
            "total": len(traces),
            "source": "sqlite",
        }
    except Exception as e:
        logger.error(f"Failed to fetch traces: {e}")
        return {
            "traces": [],
            "total": 0,
            "error": str(e),
        }


@app.get("/api/admin/observability/trace/{trace_id}")
@limiter.limit(RATE_LIMIT_ADMIN_TIER)
def api_get_trace_detail(request: Request, trace_id: str):
    """Get detailed trace info with all spans."""
    from database.db import get_spans_for_trace, get_connection

    try:
        conn = get_connection()
        trace_row = conn.execute(
            "SELECT * FROM obs_traces WHERE trace_id = ?", (trace_id,)
        ).fetchone()
        conn.close()

        if not trace_row:
            raise HTTPException(status_code=404, detail="Trace not found")

        spans = get_spans_for_trace(trace_id)

        return {
            "trace": dict(trace_row),
            "spans": spans,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get trace detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/observability/metrics")
@limiter.limit(RATE_LIMIT_ADMIN_TIER)
def api_get_observability_metrics(request: Request, days: int = 7):
    """Get aggregate observability metrics."""
    from database.db import get_observability_metrics

    try:
        metrics = get_observability_metrics(days=days)
        return metrics
    except Exception as e:
        logger.error(f"Failed to compute metrics: {e}")
        return {
            "period_days": days,
            "total_traces": 0,
            "error": str(e),
        }

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
