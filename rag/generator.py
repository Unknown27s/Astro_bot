"""
IMS AstroBot — LLM Generator
Routes queries through the configured LLM provider(s) via ProviderManager.
Falls back to context-only mode if no provider is available.
"""

import logging
import time
import config as runtime_config
from rag.providers.manager import get_manager
from rag.memory import query_memory, add_memory_entry

logger = logging.getLogger(__name__)


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

    # Report status of the primary provider
    primary_status = statuses.get(primary, {"status": "error", "message": "Unknown provider"})

    label = f"[{mode}] {primary_status['message']}"
    return {"status": primary_status["status"], "message": label}


def is_llm_available() -> bool:
    """Check if at least one provider in the chain is available."""
    mgr = get_manager()
    return mgr.is_any_available()


def generate_response(query: str, context: str, user_id: str = None, sources: list = None, trace=None, obs_trace=None, route_mode: str = None) -> dict:
    """
    Generate a response using the configured LLM provider(s) with retrieved context.
    Checks conversation memory first for similar cached answers.

    Args:
        query: User's question
        context: Formatted context from retrieved documents
        user_id: User ID for per-user memory scoping (optional)
        sources: List of source documents used in context
        trace: Optional PipelineTrace for terminal explainability

    Returns:
        Dictionary with keys: response (str), from_memory (bool), memory_id (str or None)
    """
    start_time = time.time()
    conv_enabled = runtime_config.CONV_ENABLED
    conv_match_threshold = runtime_config.CONV_MATCH_THRESHOLD
    system_prompt = runtime_config.SYSTEM_PROMPT
    model_temperature = runtime_config.MODEL_TEMPERATURE
    model_max_tokens = runtime_config.MODEL_MAX_TOKENS

    generation_span = obs_trace.start_span(
        name="generation.pipeline",
        input_payload={
            "query_preview": query[:160],
            "context_chars": len(context or ""),
            "sources_count": len(sources or []),
        },
        metadata={
            "memory_enabled": conv_enabled,
        },
    ) if obs_trace else None

    # Step 1: Check conversation memory if enabled
    if conv_enabled and query:
        memory_span = obs_trace.start_span(
            name="memory.lookup",
            input_payload={"query_preview": query[:120]},
            metadata={"threshold": conv_match_threshold},
        ) if obs_trace else None
        memory_start = time.time()
        try:
            memory_result = query_memory(query, user_id=user_id, route_mode=route_mode)
            memory_ms = (time.time() - memory_start) * 1000

            if memory_result:
                elapsed = (time.time() - start_time) * 1000
                logger.info(f"Memory cache hit - returned in {elapsed:.1f}ms")

                # Record memory HIT in trace
                if trace:
                    trace.record_memory_check(
                        hit=True,
                        best_similarity=memory_result.get("similarity"),
                        threshold=conv_match_threshold,
                        time_ms=memory_ms,
                    )

                if memory_span:
                    memory_span.end(
                        metadata={
                            "cache_hit": True,
                            "similarity": memory_result.get("similarity"),
                            "elapsed_ms": round(memory_ms, 2),
                        }
                    )

                if generation_span:
                    generation_span.end(
                        metadata={
                            "from_memory": True,
                            "elapsed_ms": round(elapsed, 2),
                        }
                    )

                return {
                    "response": memory_result["response"],
                    "from_memory": True,
                    "memory_id": memory_result.get("memory_id")
                }
            else:
                # Record memory MISS in trace
                if trace:
                    trace.record_memory_check(
                        hit=False,
                        best_similarity=None,
                        threshold=conv_match_threshold,
                        time_ms=memory_ms,
                    )
                if memory_span:
                    memory_span.end(
                        metadata={
                            "cache_hit": False,
                            "elapsed_ms": round(memory_ms, 2),
                        }
                    )
        except Exception as e:
            # Memory check failed, continue with LLM generation
            logger.warning(f"Memory query failed: {e}")
            if trace:
                trace.record_memory_check(
                    hit=False,
                    best_similarity=None,
                    threshold=conv_match_threshold,
                    time_ms=(time.time() - memory_start) * 1000,
                )
            if memory_span:
                memory_span.end(
                    metadata={
                        "cache_hit": False,
                        "memory_error": str(e),
                    }
                )

    # Step 2: Generate response via LLM provider
    mgr = get_manager()

    # Build conversation history for follow-up context
    from rag.conversation_history import format_history_for_prompt
    history_block = format_history_for_prompt(user_id) if user_id else ""

    user_message = (
        "Based on the following institutional documents, answer the question accurately.\n\n"
    )
    if history_block:
        user_message += f"{history_block}\n"
    user_message += (
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {query}"
    )

    # Record prompt construction in trace
    if trace:
        trace.record_prompt(
            system_prompt=system_prompt,
            user_message=user_message,
            context_chars=len(context),
        )

    logger.debug(f"Generating response for query: {query[:100]}...")
    llm_span = obs_trace.start_span(
        name="llm.generate",
        input_payload={"query_preview": query[:120]},
        metadata={"temperature": model_temperature, "max_tokens": model_max_tokens},
    ) if obs_trace else None
    gen_start = time.time()

    result = mgr.generate(
        system_prompt=system_prompt,
        user_message=user_message,
        temperature=model_temperature,
        max_tokens=model_max_tokens,
        trace=trace,
    )

    gen_elapsed = (time.time() - gen_start) * 1000
    logger.info(f"LLM generation completed in {gen_elapsed:.1f}ms")

    if llm_span:
        llm_span.end(
            metadata={
                "elapsed_ms": round(gen_elapsed, 2),
                "provider": trace.provider_used if trace else None,
                "model": trace.model_used if trace else None,
                "result_empty": not bool(result),
            }
        )

    # Update generation timing in trace (manager records provider info but not total time)
    if trace and trace.provider_used:
        trace.generation_time_ms = gen_elapsed

    if not result:
        # All providers failed — use fallback
        logger.warning("All LLM providers failed, using fallback response")
        result = _fallback_response(query, context)

    # Step 3: Store in memory for future queries (if enabled)
    if conv_enabled and query and result:
        try:
            memory_entry = add_memory_entry(
                query=query,
                response=result,
                sources=sources or [],
                user_id=user_id,
                route_mode=route_mode,
            )
            if generation_span:
                generation_span.end(
                    metadata={
                        "from_memory": False,
                        "memory_write": bool(memory_entry),
                        "response_chars": len(result),
                        "elapsed_ms": round((time.time() - start_time) * 1000, 2),
                    }
                )
            return {
                "response": result,
                "from_memory": False,
                "memory_id": memory_entry.get("id") if isinstance(memory_entry, dict) else None
            }
        except Exception as e:
            # Memory storage failed, but still return the response
            logger.warning(f"Failed to store response in memory: {e}")
            if generation_span:
                generation_span.end(
                    metadata={
                        "from_memory": False,
                        "memory_write": False,
                        "memory_error": str(e),
                        "response_chars": len(result),
                        "elapsed_ms": round((time.time() - start_time) * 1000, 2),
                    }
                )
            return {
                "response": result,
                "from_memory": False,
                "memory_id": None
            }

    if generation_span:
        generation_span.end(
            metadata={
                "from_memory": False,
                "response_chars": len(result) if result else 0,
                "elapsed_ms": round((time.time() - start_time) * 1000, 2),
            }
        )

    return {
        "response": result,
        "from_memory": False,
        "memory_id": None
    }


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
