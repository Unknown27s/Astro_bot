"""
IMS AstroBot — LLM Generator
Routes queries through the configured LLM provider(s) via ProviderManager.
Falls back to context-only mode if no provider is available.
"""

from config import MODEL_MAX_TOKENS, MODEL_TEMPERATURE, SYSTEM_PROMPT
from rag.providers.manager import get_manager, reset_manager


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


def generate_response(query: str, context: str) -> str:
    """
    Generate a response using the configured LLM provider(s) with retrieved context.

    Args:
        query: User's question
        context: Formatted context from retrieved documents

    Returns:
        Generated response string
    """
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

    if result:
        return result

    # All providers failed — use fallback
    return _fallback_response(query, context)


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
