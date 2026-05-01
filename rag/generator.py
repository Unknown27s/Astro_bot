"""
IMS AstroBot — LLM Generator
Routes queries through the configured LLM provider(s) via ProviderManager.
Falls back to context-only mode if no provider is available.
"""

import logging
import time
from typing import Optional
from tests.config import MODEL_MAX_TOKENS, MODEL_TEMPERATURE, SYSTEM_PROMPT, CONV_ENABLED
from rag.providers.manager import get_manager, reset_manager
from rag.memory import query_memory, add_memory_entry
from rag.observability.trace_context import get_obs_trace

logger = logging.getLogger(__name__)


def _estimate_tokens(text: str) -> int:
    """Estimate token count using simple heuristic: ~4 chars per token."""
    return max(1, len(text.split()) // 1) if text else 0


# ---------------------------------------------------------------------------
# Memory helpers — shared by both generate functions
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
    except Exception as e:
        prefix = f"[{label}] " if label else ""
        logger.warning(f"{prefix}Memory query failed: {e}")
        return None


def _store_memory(
    query: str,
    result: str,
    sources: list,
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
    except Exception as e:
        prefix = f"[{label}] " if label else ""
        logger.warning(f"{prefix}Failed to store response in memory: {e}")
        return None


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
    sources: Optional[list] = None,
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
        trace: Optional pipeline trace object (accepted for compatibility)
        obs_trace: Optional observability trace object (accepted for compatibility)
        route_mode: Optional route mode label (accepted for compatibility)

    Returns:
        Dictionary with keys: response (str), from_memory (bool), memory_id (str or None)
    """
    start_time = time.time()
    obs_span = None

    if obs_trace and hasattr(obs_trace, "start_span"):
        try:
            obs_span = obs_trace.start_span(
                name="rag.generate_response",
                input_payload={"query": query[:200], "context_length": len(context)},
                metadata={"route_mode": route_mode}
            )
        except Exception:
            pass

    # Step 1: Check conversation memory
    memory_result = _check_memory(query, user_id)
    if memory_result:
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"Memory cache hit - returned in {elapsed:.1f}ms")
        if obs_span:
            try:
                obs_span.end(
                    output={"response_length": len(memory_result["response"])},
                    metadata={
                        "from_memory": True,
                        "elapsed_ms": round(elapsed, 2),
                        "tokens_output": _estimate_tokens(memory_result["response"]),
                    }
                )
            except Exception:
                pass
        return {
            "response": memory_result["response"],
            "from_memory": True,
            "memory_id": memory_result.get("memory_id"),
        }

    # Step 2: Generate response via LLM provider
    mgr = get_manager()

    user_message = (
        "Based on the following institutional documents, answer the question accurately.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {query}"
    )

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
    if obs_span:
        try:
            obs_span.end(
                output={"response_length": len(result) if result else 0},
                metadata={
                    "from_memory": False,
                    "generation_time_ms": round(gen_elapsed, 2),
                    "tokens_input": _estimate_tokens(user_message),
                    "tokens_output": _estimate_tokens(result) if result else 0,
                    "elapsed_ms": round((time.time() - start_time) * 1000, 2),
                }
            )
        except Exception:
            pass

    # Step 5: Store in memory and always return the result
    memory_id = _store_memory(query, result, sources or [], user_id)
    return {
        "response": result,
        "from_memory": False,
        "memory_id": memory_id,
    }


def generate_response_stream(
    query: str,
    context: str,
    user_id: Optional[str] = None,
    sources: Optional[list] = None,
    trace=None,
    obs_trace=None,
    route_mode: Optional[str] = None,
    **kwargs,
):
    """
    Generate a response stream using the configured LLM provider(s) with retrieved context.
    Yields dicts with chunk data.
    """
    start_time = time.time()

    # Step 1: Check conversation memory
    memory_result = _check_memory(query, user_id)
    if memory_result:
        yield {
            "chunk": memory_result["response"],
            "from_memory": True,
            "memory_id": memory_result.get("memory_id"),
            "done": True,
        }
        return

    # Step 2: Generate response via LLM provider
    mgr = get_manager()

    user_message = (
        "Based on the following institutional documents, answer the question accurately.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {query}"
    )

    full_response = ""
    stream = mgr.generate_stream(
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        temperature=MODEL_TEMPERATURE,
        max_tokens=MODEL_MAX_TOKENS,
    )

    if stream is None:
        logger.warning("All LLM providers failed streaming, using fallback response")
        full_response = _fallback_response(query, context)
        yield {
            "chunk": full_response,
            "from_memory": False,
            "done": True,
        }
    else:
        for chunk in stream:
            full_response += chunk
            yield {
                "chunk": chunk,
                "from_memory": False,
                "done": False,
            }
        
        memory_id = _store_memory(query, full_response, sources or [], user_id)
        yield {
            "chunk": "",
            "from_memory": False,
            "memory_id": memory_id,
            "done": True,
        }



def generate_response_direct(
    query: str,
    user_id: Optional[str] = None,
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

    # Step 1: Check conversation memory
    memory_result = _check_memory(query, user_id, label="direct")
    if memory_result:
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"Direct mode memory cache hit - returned in {elapsed:.1f}ms")
        return {
            "response": memory_result["response"],
            "from_memory": True,
            "memory_id": memory_result.get("memory_id"),
        }

    # Step 2: Generate response
    mgr = get_manager()
    direct_prompt = (
        "Answer the user naturally and helpfully. "
        "If the question is about IMS/RIT institution details, mention that official documents may provide the most accurate answer.\n\n"
        f"USER QUESTION: {query}"
    )

    result = mgr.generate(
        system_prompt=SYSTEM_PROMPT,
        user_message=direct_prompt,
        temperature=MODEL_TEMPERATURE,
        max_tokens=MODEL_MAX_TOKENS,
    )

    if result is None:
        result = "I am unable to generate a response right now. Please try again in a moment."

    # Step 3: Store in memory and always return the result
    memory_id = _store_memory(query, result, [], user_id, label="direct")
    return {
        "response": result,
        "from_memory": False,
        "memory_id": memory_id,
    }


def generate_response_direct_stream(
    query: str,
    user_id: Optional[str] = None,
    trace=None,
    obs_trace=None,
    route_mode: Optional[str] = None,
    **kwargs,
):
    """
    Generate a direct LLM response stream without retrieval context.
    """
    start_time = time.time()

    # Step 1: Check conversation memory
    memory_result = _check_memory(query, user_id, label="direct")
    if memory_result:
        yield {
            "chunk": memory_result["response"],
            "from_memory": True,
            "memory_id": memory_result.get("memory_id"),
            "done": True,
        }
        return

    # Step 2: Generate response
    mgr = get_manager()
    direct_prompt = (
        "Answer the user naturally and helpfully. "
        "If the question is about IMS/RIT institution details, mention that official documents may provide the most accurate answer.\n\n"
        f"USER QUESTION: {query}"
    )

    full_response = ""
    stream = mgr.generate_stream(
        system_prompt=SYSTEM_PROMPT,
        user_message=direct_prompt,
        temperature=MODEL_TEMPERATURE,
        max_tokens=MODEL_MAX_TOKENS,
    )

    if stream is None:
        full_response = "I am unable to generate a response right now. Please try again in a moment."
        yield {
            "chunk": full_response,
            "from_memory": False,
            "done": True,
        }
    else:
        for chunk in stream:
            full_response += chunk
            yield {
                "chunk": chunk,
                "from_memory": False,
                "done": False,
            }

        memory_id = _store_memory(query, full_response, [], user_id, label="direct")
        yield {
            "chunk": "",
            "from_memory": False,
            "memory_id": memory_id,
            "done": True,
        }


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------

def _fallback_response(query: str, context: str) -> str:
    """
    Fallback response when no LLM provider is available.
    Returns the retrieved context in a formatted way.
    """
    if "No relevant documents found" in context:
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