"""
Custom SQLite-based observability for AstroBot.
Replaces Langfuse with local-only tracing.
No cloud calls, full control, minimal overhead (~3ms per request).
"""

import uuid
import time
from typing import Optional, Any
from database.db import start_trace, end_trace, start_span, end_span


class ObservationSpan:
    """Represents a span within a trace (operation timing)."""

    def __init__(self, trace_id: str, span_id: str, service: str, operation: str,
                 input_data: Optional[dict] = None):
        self.trace_id = trace_id
        self.span_id = span_id
        self.service = service
        self.operation = operation
        self.input_data = input_data or {}
        self.start_time = time.time()

        # Record span start in database
        start_span(trace_id, span_id, service, operation, input_data)

    def end(self, output_data: Optional[dict] = None, error: Optional[str] = None,
            tags: Optional[dict] = None, status: str = "success",
            output: Optional[Any] = None, metadata: Optional[dict] = None):
        """End the span and record it in database.

        Accepts both the original sqlite_tracer kwargs (output_data, tags, status)
        and the Langfuse-style kwargs (output, metadata) for compatibility.
        """
        duration_ms = (time.time() - self.start_time) * 1000

        # Merge both styles of metadata/tags
        record = {
            "duration_ms": round(duration_ms, 2),
            **(tags or {}),
            **(metadata or {}),
        }

        # Prefer explicit output_data, fall back to output kwarg
        final_output = output_data or output or {}

        end_span(self.span_id, status=status, output_data=final_output,
                error=error, tags=record)


class ObservationTrace:
    """Represents a distributed trace (root of all spans)."""

    def __init__(self, trace_id: str, service: str, operation: str,
                 user_id: Optional[str] = None, metadata: Optional[dict] = None):
        self.trace_id = trace_id
        self.service = service
        self.operation = operation
        self.user_id = user_id
        self.metadata = metadata or {}
        self.start_time = time.time()

        # Record trace start in database
        start_trace(trace_id, service, operation, user_id, metadata)

    def start_span(self, service: str = "", operation: str = "",
                   input_data: Optional[dict] = None,
                   parent_span_id: Optional[str] = None,
                   name: Optional[str] = None,
                   input_payload: Optional[dict] = None,
                   metadata: Optional[dict] = None) -> ObservationSpan:
        """Start a child span.

        Accepts both sqlite_tracer-style kwargs (service, operation, input_data)
        and Langfuse-style kwargs (name, input_payload, metadata) for compatibility.
        """
        span_id = str(uuid.uuid4())
        # Langfuse-style: name maps to operation, input_payload maps to input_data
        final_operation = operation or name or "span"
        final_input = input_data or input_payload
        return ObservationSpan(self.trace_id, span_id, service or self.service,
                               final_operation, final_input)

    def end(self, status: str = "success", error: Optional[str] = None,
            metadata: Optional[dict] = None, output: Optional[Any] = None):
        """End the trace.

        Accepts both sqlite_tracer-style kwargs (status, error) and
        Langfuse-style kwargs (metadata, output, error) for compatibility.
        """
        duration_ms = (time.time() - self.start_time) * 1000

        # Derive status from metadata if provided in Langfuse style
        if metadata and "status" in metadata:
            status = metadata["status"]

        end_trace(self.trace_id, status=status, error=error)


def start_observation(
    name: str,
    service: str = "astrobot",
    user_id: Optional[str] = None,
    metadata: Optional[dict] = None,
    input_payload: Optional[dict[str, Any]] = None,
) -> ObservationTrace:
    """Create a new observation trace.

    Accepts both the original sqlite_tracer kwargs and the Langfuse-style
    ``input_payload`` kwarg for compatibility with callers migrated from
    the Langfuse backend.
    """
    trace_id = str(uuid.uuid4())
    merged_metadata = {
        "component": "astrobot",
        **(metadata or {}),
    }
    if input_payload:
        merged_metadata["input_payload"] = input_payload

    return ObservationTrace(
        trace_id=trace_id,
        service=service,
        operation=name,
        user_id=user_id,
        metadata=merged_metadata,
    )


def record_feedback(
    trace_id: str,
    rating: float,
    comment: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> bool:
    """Record user feedback against an existing trace id.

    In the SQLite-only backend this is a no-op for Langfuse scoring but
    returns True so callers can proceed normally.  The actual feedback
    persistence is handled by ``database.db.log_feedback``.
    """
    if not trace_id:
        return False

    # Feedback is persisted via log_feedback() in the caller;
    # this function exists for API parity with the Langfuse backend.
    return True
