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
            tags: Optional[dict] = None, status: str = "success"):
        """End the span and record it in database."""
        duration_ms = (time.time() - self.start_time) * 1000

        record = {
            "duration_ms": round(duration_ms, 2),
            **(tags or {}),
        }

        end_span(self.span_id, status=status, output_data=output_data or {},
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

    def start_span(self, service: str, operation: str,
                   input_data: Optional[dict] = None,
                   parent_span_id: Optional[str] = None) -> ObservationSpan:
        """Start a child span."""
        span_id = str(uuid.uuid4())
        return ObservationSpan(self.trace_id, span_id, service, operation, input_data)

    def end(self, status: str = "success", error: Optional[str] = None):
        """End the trace."""
        duration_ms = (time.time() - self.start_time) * 1000
        end_trace(self.trace_id, status=status, error=error)


def start_observation(
    name: str,
    service: str = "astrobot",
    user_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> ObservationTrace:
    """Create a new observation trace."""
    trace_id = str(uuid.uuid4())
    return ObservationTrace(
        trace_id=trace_id,
        service=service,
        operation=name,
        user_id=user_id,
        metadata={
            "component": "astrobot",
            **(metadata or {}),
        }
    )
