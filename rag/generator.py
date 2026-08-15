"""
IMS AstroBot — LLM Generator
Routes queries through the configured LLM provider(s) via ProviderManager.
Falls back to context-only mode if no provider is available.
"""

import logging
import time
from typing import Any, Dict, Iterator, List, Optional

from tests.config import MODEL_MAX_TOKENS, MODEL_TEMPERATURE, SYSTEM_PROMPT, CONV_ENABLED
from rag.providers.manager import get_manager
from rag.memory import query_memory, add_memory_entry

logger = logging.getLogger(__name__)

# Rough heuristic: ~4 characters per token (better than word-count, still cheap).
CHARS_PER_TOKEN = 4

UNAVAILABLE_MESSAGE = "I am unable to generate a response right now. Please try again in a moment."


def _estimate_tokens(text: Optional[str]) -> int:
    """Estimate token count using a simple heuristic: ~4 chars per token."""
    if not text:
        return 0
    return max(1, len(text) // CHARS_PER_TOKEN)


# ---------------------------------------------------------------------------
# Memory helpers — shared by all generate functions
# ---------------------------------------------------------------------------

def _check_memory(query: str, user_id: Optional[str], label: str = "") -> Optional[dict]:
    """
    Look up a cached response in conversation memory.
    Returns the memory result dict on a hit, or None on a miss / disabled / error.
    """
    if not (CONV_ENABLED and query):
        return None
    try:
        return query_memory(query, user_id=user_id)
    except Exception:
        prefix = f"[{label}] " if label else ""
        logger.warning(f"{prefix}Memory query failed", exc_info=True)
        return None


def _store_memory(
    query: str,
    result: str,
    sources: List[Dict[str, Any]],
    user_id: Optional[str],
    label: str = "",
) -> Optional[str]:
    """
    Persist a response to conversation memory.
    Returns the new memory ID on success, or None on disabled / error.
    """
    if not (CONV_ENABLED and query and result):
        return None
    try:
        entry = add_memory_entry(query=query, response=result, sources=sources, user_id=user_id)
        return entry.get("id") if isinstance(entry, dict) else None
    except Exception:
        prefix = f"[{label}] " if label else ""
        logger.warning(f"{prefix}Failed to store response in memory", exc_info=True)
        return None


def _memory_hit_payload(memory_result: dict, start_time: float, label: str) -> dict:
    """Build the return payload for a memory cache hit, with consistent logging."""
    elapsed = (time.time() - start_time) * 1000
    prefix = f"[{label}] " if label else ""
    logger.info(f"{prefix}Memory cache hit - returned in {elapsed:.1f}ms")
    return {
        "response": memory_result["response"],
        "from_memory": True,
        "memory_id": memory_result.get("memory_id"),
    }


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _build_rag_prompt(query: str, context: str, user_context: Optional[str]) -> str:
    message = (
        "Based on the following institutional documents, answer the question accurately.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {query}"
    )
    if user_context:
        message = (
            "Use the student context to personalize the answer when relevant.\n\n"
            f"STUDENT CONTEXT:\n{user_context}\n\n" + message
        )
    return message


def _build_direct_prompt(query: str, user_context: Optional[str]) -> str:
    message = (
        "Answer the user naturally and helpfully. "
        "If the question is about IMS/RIT institution details, mention that official "
        "documents may provide the most accurate answer.\n\n"
        f"USER QUESTION: {query}"
    )
    if user_context:
        message = (
            "Use the student context to personalize the answer when relevant.\n\n"
            f"STUDENT CONTEXT:\n{user_context}\n\n" + message
        )
    return message


# ---------------------------------------------------------------------------
# Observability helpers — now used consistently by every generate function,
# including the streaming and "direct" variants (previously only
# generate_response created/ended a span).
# ---------------------------------------------------------------------------

def _start_span(obs_trace, name: str, query: str, route_mode: Optional[str], extra_input: Optional[dict] = None):
    if not (obs_trace and hasattr(obs_trace, "start_span")):
        return None
    try:
        input_payload = {"query": (query or "")[:200]}
        if extra_input:
            input_payload.update(extra_input)
        return obs_trace.start_span(
            name=name,
            input_payload=input_payload,
            metadata={"route_mode": route_mode},
        )
    except Exception:
        logger.debug("Failed to start observability span", exc_info=True)
        return None


def _end_span(span, response_text: str, from_memory: bool, start_time: float, extra_metadata: Optional[dict] = None):
    if not span:
        return
    try:
        metadata = {
            "from_memory": from_memory,
            "elapsed_ms": round((time.time() - start_time) * 1000, 2),
            "tokens_output": _estimate_tokens(response_text),
        }
        if extra_metadata:
            metadata.update(extra_metadata)
        span.end(
            output={"response_length": len(response_text) if response_text else 0},
            metadata=metadata,
        )
    except Exception:
        logger.debug("Failed to end observability span", exc_info=True)


# ---------------------------------------------------------------------------
# Status helpers
# ---------------------------------------------------------------------------

def get_llm_status() -> dict:
    """
    Get LLM status WITHOUT triggering a generation.
    Used by health checks to report status quickly.
    """
    mgr = get_manager()
    statuses = mgr.get_all_statuses()
    meta = statuses.get("_mode", {})
    mode = meta.get("mode", "local_only")
    primary = meta.get("primary", "ollama")

    primary_status = statuses.get(primary, {"status": "error", "message": "Unknown provider"})
    label = f"[{mode}] {primary_status['message']}"
    return {"status": primary_status["status"], "message": label}


def is_llm_available() -> bool:
    """Check if at least one provider in the chain is available."""
    mgr = get_manager()
    return mgr.is_any_available()


# ---------------------------------------------------------------------------
# Main generation functions
# ---------------------------------------------------------------------------

def generate_response(
    query: str,
    context: str,
    user_id: Optional[str] = None,
    sources: Optional[List[Dict[str, Any]]] = None,
    user_context: Optional[str] = None,
    skip_memory: bool = False,
    trace=None,
    obs_trace=None,
    route_mode: Optional[str] = None,
    **kwargs,
) -> dict:
    """
    Generate a response using the configured LLM provider(s) with retrieved context.
    Checks conversation memory first for similar cached answers.

    Args:
        query: User's question
        context: Formatted context from retrieved documents
        user_id: User ID for per-user memory scoping (optional)
        sources: List of source documents used in context
        trace: Optional pipeline trace object (accepted for compatibility, unused)
        obs_trace: Optional observability trace object (accepted for compatibility)
        route_mode: Optional route mode label (accepted for compatibility)

    Returns:
        Dictionary with keys: response (str), from_memory (bool), memory_id (str or None)
    """
    start_time = time.time()
    sources = sources or []

    if not query or not query.strip():
        logger.warning("generate_response called with empty query")
        return {"response": "", "from_memory": False, "memory_id": None}

    obs_span = _start_span(
        obs_trace, "rag.generate_response", query, route_mode,
        extra_input={"context_length": len(context or "")},
    )

    # Step 1: Check conversation memory
    if not skip_memory:
        memory_result = _check_memory(query, user_id)
        if memory_result:
            payload = _memory_hit_payload(memory_result, start_time, label="")
            _end_span(obs_span, payload["response"], from_memory=True, start_time=start_time)
            return payload

    # Step 2: Generate response via LLM provider
    mgr = get_manager()
    user_message = _build_rag_prompt(query, context, user_context)

    logger.debug(f"Generating response for query: {query[:100]}...")
    gen_start = time.time()

    result = mgr.generate(
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        temperature=MODEL_TEMPERATURE,
        max_tokens=MODEL_MAX_TOKENS,
    )

    gen_elapsed = (time.time() - gen_start) * 1000
    logger.info(f"LLM generation completed in {gen_elapsed:.1f}ms")

    # Step 3: Fallback if every provider failed (result is None, not just falsy)
    if result is None:
        logger.warning("All LLM providers failed, using fallback response")
        result = _fallback_response(query, context)

    # Step 4: Record observability span
    _end_span(
        obs_span, result, from_memory=False, start_time=start_time,
        extra_metadata={
            "generation_time_ms": round(gen_elapsed, 2),
            "tokens_input": _estimate_tokens(user_message),
        },
    )

    # Step 5: Store in memory and always return the result
    memory_id = None
    if not skip_memory:
        memory_id = _store_memory(query, result, sources, user_id)
    return {
        "response": result,
        "from_memory": False,
        "memory_id": memory_id,
    }


def generate_response_stream(
    query: str,
    context: str,
    user_id: Optional[str] = None,
    sources: Optional[List[Dict[str, Any]]] = None,
    user_context: Optional[str] = None,
    skip_memory: bool = False,
    trace=None,
    obs_trace=None,
    route_mode: Optional[str] = None,
    **kwargs,
) -> Iterator[dict]:
    """
    Generate a response stream using the configured LLM provider(s) with retrieved context.
    Yields dicts with chunk data.
    """
    start_time = time.time()
    sources = sources or []

    if not query or not query.strip():
        logger.warning("generate_response_stream called with empty query")
        yield {"chunk": "", "from_memory": False, "done": True}
        return

    obs_span = _start_span(
        obs_trace, "rag.generate_response_stream", query, route_mode,
        extra_input={"context_length": len(context or "")},
    )

    # Step 1: Check conversation memory
    if not skip_memory:
        memory_result = _check_memory(query, user_id)
        if memory_result:
            payload = _memory_hit_payload(memory_result, start_time, label="stream")
            _end_span(obs_span, payload["response"], from_memory=True, start_time=start_time)
            yield {
                "chunk": payload["response"],
                "from_memory": True,
                "memory_id": payload["memory_id"],
                "done": True,
            }
            return

    # Step 2: Generate response via LLM provider
    mgr = get_manager()
    user_message = _build_rag_prompt(query, context, user_context)

    gen_start = time.time()
    full_response = ""
    stream_failed = False

    try:
        stream = mgr.generate_stream(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_message,
            temperature=MODEL_TEMPERATURE,
            max_tokens=MODEL_MAX_TOKENS,
        )
    except Exception:
        logger.warning("Failed to start LLM stream, using fallback response", exc_info=True)
        stream = None

    if stream is None:
        logger.warning("All LLM providers failed streaming, using fallback response")
        full_response = _fallback_response(query, context)
        yield {"chunk": full_response, "from_memory": False, "done": True}
    else:
        try:
            for chunk in stream:
                full_response += chunk
                yield {"chunk": chunk, "from_memory": False, "done": False}
        except Exception:
            # Stream started but broke partway through — don't let the raw
            # exception propagate to the caller; close out gracefully with
            # whatever we managed to generate (or a fallback if nothing yet).
            logger.warning("LLM stream failed mid-response", exc_info=True)
            stream_failed = True
            if not full_response:
                full_response = _fallback_response(query, context)
                yield {"chunk": full_response, "from_memory": False, "done": False}

        memory_id = None
        if not skip_memory:
            memory_id = _store_memory(query, full_response, sources, user_id)
        yield {
            "chunk": "",
            "from_memory": False,
            "memory_id": memory_id,
            "done": True,
            "stream_failed": stream_failed,
        }

    gen_elapsed = (time.time() - gen_start) * 1000
    logger.info(f"LLM stream generation completed in {gen_elapsed:.1f}ms")
    _end_span(
        obs_span, full_response, from_memory=False, start_time=start_time,
        extra_metadata={
            "generation_time_ms": round(gen_elapsed, 2),
            "tokens_input": _estimate_tokens(user_message),
            "stream_failed": stream_failed,
        },
    )


def generate_response_direct(
    query: str,
    user_id: Optional[str] = None,
    user_context: Optional[str] = None,
    skip_memory: bool = False,
    trace=None,
    obs_trace=None,
    route_mode: Optional[str] = None,
    **kwargs,
) -> dict:
    """
    Generate a direct LLM response without retrieval context.

    Useful for general chat where institutional retrieval is unnecessary.
    """
    start_time = time.time()

    if not query or not query.strip():
        logger.warning("generate_response_direct called with empty query")
        return {"response": "", "from_memory": False, "memory_id": None}

    obs_span = _start_span(obs_trace, "rag.generate_response_direct", query, route_mode)

    # Step 1: Check conversation memory
    if not skip_memory:
        memory_result = _check_memory(query, user_id, label="direct")
        if memory_result:
            payload = _memory_hit_payload(memory_result, start_time, label="direct")
            _end_span(obs_span, payload["response"], from_memory=True, start_time=start_time)
            return payload

    # Step 2: Generate response
    mgr = get_manager()
    direct_prompt = _build_direct_prompt(query, user_context)

    gen_start = time.time()
    result = mgr.generate(
        system_prompt=SYSTEM_PROMPT,
        user_message=direct_prompt,
        temperature=MODEL_TEMPERATURE,
        max_tokens=MODEL_MAX_TOKENS,
    )
    gen_elapsed = (time.time() - gen_start) * 1000
    logger.info(f"Direct LLM generation completed in {gen_elapsed:.1f}ms")

    if result is None:
        logger.warning("All LLM providers failed (direct mode), using fallback response")
        result = UNAVAILABLE_MESSAGE

    _end_span(
        obs_span, result, from_memory=False, start_time=start_time,
        extra_metadata={
            "generation_time_ms": round(gen_elapsed, 2),
            "tokens_input": _estimate_tokens(direct_prompt),
        },
    )

    # Step 3: Store in memory and always return the result
    memory_id = None
    if not skip_memory:
        memory_id = _store_memory(query, result, [], user_id, label="direct")
    return {
        "response": result,
        "from_memory": False,
        "memory_id": memory_id,
    }


def generate_response_direct_stream(
    query: str,
    user_id: Optional[str] = None,
    user_context: Optional[str] = None,
    skip_memory: bool = False,
    trace=None,
    obs_trace=None,
    route_mode: Optional[str] = None,
    **kwargs,
) -> Iterator[dict]:
    """
    Generate a direct LLM response stream without retrieval context.
    """
    start_time = time.time()

    if not query or not query.strip():
        logger.warning("generate_response_direct_stream called with empty query")
        yield {"chunk": "", "from_memory": False, "done": True}
        return

    obs_span = _start_span(obs_trace, "rag.generate_response_direct_stream", query, route_mode)

    # Step 1: Check conversation memory
    if not skip_memory:
        memory_result = _check_memory(query, user_id, label="direct")
        if memory_result:
            payload = _memory_hit_payload(memory_result, start_time, label="direct-stream")
            _end_span(obs_span, payload["response"], from_memory=True, start_time=start_time)
            yield {
                "chunk": payload["response"],
                "from_memory": True,
                "memory_id": payload["memory_id"],
                "done": True,
            }
            return

    # Step 2: Generate response
    mgr = get_manager()
    direct_prompt = _build_direct_prompt(query, user_context)

    gen_start = time.time()
    full_response = ""
    stream_failed = False

    try:
        stream = mgr.generate_stream(
            system_prompt=SYSTEM_PROMPT,
            user_message=direct_prompt,
            temperature=MODEL_TEMPERATURE,
            max_tokens=MODEL_MAX_TOKENS,
        )
    except Exception:
        logger.warning("Failed to start direct LLM stream, using fallback response", exc_info=True)
        stream = None

    if stream is None:
        full_response = UNAVAILABLE_MESSAGE
        yield {"chunk": full_response, "from_memory": False, "done": True}
    else:
        try:
            for chunk in stream:
                full_response += chunk
                yield {"chunk": chunk, "from_memory": False, "done": False}
        except Exception:
            logger.warning("Direct LLM stream failed mid-response", exc_info=True)
            stream_failed = True
            if not full_response:
                full_response = UNAVAILABLE_MESSAGE
                yield {"chunk": full_response, "from_memory": False, "done": False}

        memory_id = None
        if not skip_memory:
            memory_id = _store_memory(query, full_response, [], user_id, label="direct")
        yield {
            "chunk": "",
            "from_memory": False,
            "memory_id": memory_id,
            "done": True,
            "stream_failed": stream_failed,
        }

    gen_elapsed = (time.time() - gen_start) * 1000
    logger.info(f"Direct LLM stream generation completed in {gen_elapsed:.1f}ms")
    _end_span(
        obs_span, full_response, from_memory=False, start_time=start_time,
        extra_metadata={
            "generation_time_ms": round(gen_elapsed, 2),
            "tokens_input": _estimate_tokens(direct_prompt),
            "stream_failed": stream_failed,
        },
    )


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------

def _fallback_response(query: str, context: str) -> str:
    """
    Fallback response when no LLM provider is available.
    Returns the retrieved context in a formatted way.
    """
    if not context or "No relevant documents found" in context:
        return (
            "⚠️ **No LLM provider available** and no relevant documents were found.\n\n"
            "Please ask your administrator to:\n"
            "1. Upload relevant institutional documents\n"
            "2. Configure an LLM provider in AI Settings"
        )

    return (
        "⚠️ **No LLM provider available** — showing retrieved context directly:\n\n"
        f"---\n\n{context}\n\n---\n\n"
        "*To enable AI-generated answers, configure an LLM provider in AI Settings and restart.*"
    )