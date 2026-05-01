"""
Thread-safe trace context for propagating trace_id through RAG pipeline.
Allows any RAG component to access the current trace_id and add spans.
"""

import contextvars
from typing import Optional

# Context variable for trace_id (thread-safe, async-safe)
_trace_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "trace_id", default=None
)

# Context variable for the current observation trace
_obs_trace_var: contextvars.ContextVar[Optional[object]] = contextvars.ContextVar(
    "obs_trace", default=None
)


def set_trace_id(trace_id: str):
    """Set the current trace_id for this execution context."""
    _trace_id_var.set(trace_id)


def get_trace_id() -> Optional[str]:
    """Get the current trace_id, or None if not set."""
    return _trace_id_var.get()


def set_obs_trace(obs_trace: object):
    """Set the current ObservationTrace for this execution context."""
    _obs_trace_var.set(obs_trace)


def get_obs_trace() -> Optional[object]:
    """Get the current ObservationTrace, or None if not set."""
    return _obs_trace_var.get()


def clear_trace_context():
    """Clear all trace context (call at end of request)."""
    _trace_id_var.set(None)
    _obs_trace_var.set(None)
