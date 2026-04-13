"""
IMS AstroBot — Conversation History (Follow-up Memory)
Maintains per-user conversation history so the LLM can handle follow-up questions
like "tell me more", "what about that", "and the fees?".

This is SEPARATE from memory.py (semantic cache). This module tracks the recent
conversation turns within a session so the LLM has context for follow-ups.
"""

import time
import threading
import logging
from typing import Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

# ── Configuration ──
MAX_HISTORY_TURNS = 5          # Keep last N Q&A pairs per user
HISTORY_TIMEOUT_SECONDS = 1800  # Clear history after 30 min of inactivity

# ── Thread-safe in-memory storage ──
_history_lock = threading.Lock()

# Structure: {user_id: {"turns": [(query, response), ...], "last_active": timestamp}}
_user_histories: dict[str, dict] = defaultdict(lambda: {"turns": [], "last_active": 0})


def add_turn(user_id: str, query: str, response: str):
    """
    Record a conversation turn (query + response) for a user.
    Automatically trims to MAX_HISTORY_TURNS.
    """
    with _history_lock:
        history = _user_histories[user_id]
        history["turns"].append((query, response))
        history["last_active"] = time.time()

        # Trim to max turns
        if len(history["turns"]) > MAX_HISTORY_TURNS:
            history["turns"] = history["turns"][-MAX_HISTORY_TURNS:]

    logger.debug(f"Conversation history for {user_id}: {len(history['turns'])} turns stored")


def get_history(user_id: str) -> list[tuple[str, str]]:
    """
    Get the recent conversation turns for a user.
    Returns empty list if no history or history has timed out.
    
    Returns:
        List of (query, response) tuples, oldest first.
    """
    with _history_lock:
        history = _user_histories.get(user_id)
        if not history:
            return []

        # Check for timeout
        elapsed = time.time() - history["last_active"]
        if elapsed > HISTORY_TIMEOUT_SECONDS:
            # Session expired — clear stale history
            history["turns"] = []
            logger.debug(f"Session expired for {user_id} ({elapsed:.0f}s idle)")
            return []

        return list(history["turns"])


def format_history_for_prompt(user_id: str) -> str:
    """
    Format the conversation history into a string suitable for the LLM prompt.
    Returns empty string if no history exists.
    """
    turns = get_history(user_id)
    if not turns:
        return ""

    lines = ["PREVIOUS CONVERSATION (for follow-up context):"]
    for i, (query, response) in enumerate(turns, 1):
        # Truncate long responses to keep prompt size reasonable
        short_response = response[:300]
        if len(response) > 300:
            short_response += "..."
        lines.append(f"  User [{i}]: {query}")
        lines.append(f"  AstroBot [{i}]: {short_response}")

    lines.append("")  # blank line separator
    return "\n".join(lines)


def clear_history(user_id: str):
    """Clear conversation history for a specific user."""
    with _history_lock:
        if user_id in _user_histories:
            _user_histories[user_id]["turns"] = []
            logger.debug(f"Cleared conversation history for {user_id}")


def clear_all_histories():
    """Clear all conversation histories (admin action)."""
    with _history_lock:
        _user_histories.clear()
        logger.info("All conversation histories cleared")


def get_history_stats() -> dict:
    """Get stats about active conversation histories."""
    with _history_lock:
        active = 0
        total_turns = 0
        now = time.time()
        for user_id, history in _user_histories.items():
            if now - history["last_active"] < HISTORY_TIMEOUT_SECONDS:
                active += 1
                total_turns += len(history["turns"])
        return {
            "active_sessions": active,
            "total_turns": total_turns,
            "max_turns_per_user": MAX_HISTORY_TURNS,
            "timeout_seconds": HISTORY_TIMEOUT_SECONDS,
        }
