"""
IMS AstroBot — LLM Generator
Routes queries through the configured LLM provider(s) via ProviderManager.
Falls back to context-only mode if no provider is available.
"""

from config import MODEL_MAX_TOKENS, MODEL_TEMPERATURE, SYSTEM_PROMPT, CONV_ENABLED
from rag.providers.manager import get_manager, reset_manager
from rag.memory import query_memory, add_memory_entry


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


def generate_response(query: str, context: str, user_id: str = None, sources: list = None) -> dict:
    """
    Generate a response using the configured LLM provider(s) with retrieved context.
    Checks conversation memory first for similar cached answers.

    Args:
        query: User's question
        context: Formatted context from retrieved documents
        user_id: User ID for per-user memory scoping (optional)
        sources: List of source documents used in context

    Returns:
        Dictionary with keys: response (str), from_memory (bool), memory_id (str or None)
    """
    # Step 1: Check conversation memory if enabled
    if CONV_ENABLED and query:
        try:
            memory_result = query_memory(query, user_id=user_id)
            if memory_result:
                return {
                    "response": memory_result["response"],
                    "from_memory": True,
                    "memory_id": memory_result.get("memory_id")
                }
        except Exception as e:
            # Memory check failed, continue with LLM generation
            print(f"⚠️ Memory query failed: {e}")

    # Step 2: Generate response via LLM provider
    mgr = get_manager()

    user_message = (
        "Based on the following institutional documents, answer the question accurately.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {query}"
    )

    result = mgr.generate(
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        temperature=MODEL_TEMPERATURE,
        max_tokens=MODEL_MAX_TOKENS,
    )

    if not result:
        # All providers failed — use fallback
        result = _fallback_response(query, context)

    # Step 3: Store in memory for future queries (if enabled)
    if CONV_ENABLED and query and result:
        try:
            memory_entry = add_memory_entry(
                query=query,
                response=result,
                sources=sources or [],
                user_id=user_id
            )
            return {
                "response": result,
                "from_memory": False,
                "memory_id": memory_entry.get("id") if isinstance(memory_entry, dict) else None
            }
        except Exception as e:
            # Memory storage failed, but still return the response
            print(f"⚠️ Failed to store in memory: {e}")
            return {
                "response": result,
                "from_memory": False,
                "memory_id": None
            }

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
