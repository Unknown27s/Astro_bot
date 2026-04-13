"""Langfuse integration helpers with safe no-op fallback behavior."""

from __future__ import annotations

import hashlib
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from config import (
    LANGFUSE_ENABLED,
    LANGFUSE_HOST,
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY,
)

logger = logging.getLogger(__name__)

_langfuse_client = None
_langfuse_initialized = False
_langfuse_disabled_reason = None


def hash_user_identifier(user_id: Optional[str]) -> str:
    """Hash user id for safer observability metadata."""
    if not user_id:
        return "anonymous"
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:16]


def _call_with_fallbacks(target: Any, method_name: str, kwargs_variants: list[dict]) -> Any:
    """Call method with multiple kwargs shapes to tolerate SDK signature changes."""
    method = getattr(target, method_name, None)
    if not callable(method):
        return None

    for kwargs in kwargs_variants:
        try:
            return method(**kwargs)
        except TypeError:
            continue
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Langfuse call failed: %s.%s -> %s", type(target).__name__, method_name, exc)
            return None
    return None


def get_langfuse_client() -> Any:
    """Return initialized Langfuse client or None if disabled/unavailable."""
    global _langfuse_client, _langfuse_initialized, _langfuse_disabled_reason

    if _langfuse_initialized:
        return _langfuse_client

    _langfuse_initialized = True

    if not LANGFUSE_ENABLED:
        _langfuse_disabled_reason = "LANGFUSE_ENABLED=false"
        return None

    if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        _langfuse_disabled_reason = "Missing LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY"
        logger.warning("Langfuse is enabled but keys are missing. Running without observability export.")
        return None

    try:
        from langfuse import Langfuse

        _langfuse_client = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST,
        )
        logger.info("Langfuse client initialized")
        return _langfuse_client
    except Exception as exc:  # pragma: no cover - defensive
        _langfuse_disabled_reason = str(exc)
        logger.warning("Failed to initialize Langfuse client: %s", exc)
        _langfuse_client = None
        return None


@dataclass
class ObservationSpan:
    """Represents an operation span inside an observation trace."""

    name: str
    span_client: Any = None
    start_time: float = field(default_factory=time.time)
    metadata: Optional[dict[str, Any]] = None

    def end(self, output: Any = None, metadata: Optional[dict[str, Any]] = None):
        elapsed_ms = (time.time() - self.start_time) * 1000
        merged_meta = dict(self.metadata or {})
        if metadata:
            merged_meta.update(metadata)
        merged_meta.setdefault("elapsed_ms", round(elapsed_ms, 2))

        if self.span_client is not None:
            _call_with_fallbacks(
                self.span_client,
                "end",
                [
                    {"output": output, "metadata": merged_meta},
                    {"output": output},
                    {},
                ],
            )


@dataclass
class ObservationTrace:
    """Represents a trace around an API request or core flow."""

    trace_id: str
    name: str
    trace_client: Any = None
    start_time: float = field(default_factory=time.time)
    metadata: Optional[dict[str, Any]] = None

    def start_span(
        self,
        name: str,
        input_payload: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ObservationSpan:
        span_client = None
        if self.trace_client is not None:
            span_client = _call_with_fallbacks(
                self.trace_client,
                "span",
                [
                    {"name": name, "input": input_payload, "metadata": metadata or {}},
                    {"name": name, "metadata": metadata or {}},
                    {"name": name},
                ],
            )

        return ObservationSpan(name=name, span_client=span_client, start_time=time.time(), metadata=metadata)

    def update(self, output: Any = None, metadata: Optional[dict[str, Any]] = None):
        merged_meta = dict(self.metadata or {})
        if metadata:
            merged_meta.update(metadata)

        if self.trace_client is not None:
            _call_with_fallbacks(
                self.trace_client,
                "update",
                [
                    {"output": output, "metadata": merged_meta},
                    {"output": output},
                    {"metadata": merged_meta},
                    {},
                ],
            )

    def score(self, name: str, value: float, comment: Optional[str] = None):
        client = get_langfuse_client()
        if client is None:
            return

        _call_with_fallbacks(
            client,
            "score",
            [
                {
                    "trace_id": self.trace_id,
                    "name": name,
                    "value": value,
                    "comment": comment,
                },
                {
                    "traceId": self.trace_id,
                    "name": name,
                    "value": value,
                    "comment": comment,
                },
            ],
        )

    def end(
        self,
        output: Any = None,
        metadata: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        elapsed_ms = (time.time() - self.start_time) * 1000
        merged_meta = dict(self.metadata or {})
        if metadata:
            merged_meta.update(metadata)
        merged_meta.setdefault("elapsed_ms", round(elapsed_ms, 2))

        if error:
            merged_meta["error"] = error

        self.update(output=output, metadata=merged_meta)

        client = get_langfuse_client()
        if client is not None:
            _call_with_fallbacks(client, "flush", [{},])


def start_observation(
    name: str,
    user_id: Optional[str] = None,
    input_payload: Optional[dict[str, Any]] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> ObservationTrace:
    """Start a trace that can collect spans through the pipeline."""
    trace_id = str(uuid.uuid4())
    base_meta = dict(metadata or {})
    base_meta.setdefault("component", "astrobot")
    if user_id:
        base_meta.setdefault("user_hash", hash_user_identifier(user_id))

    trace_client = None
    client = get_langfuse_client()
    if client is not None:
        trace_client = _call_with_fallbacks(
            client,
            "trace",
            [
                {
                    "id": trace_id,
                    "name": name,
                    "user_id": hash_user_identifier(user_id),
                    "input": input_payload or {},
                    "metadata": base_meta,
                },
                {
                    "name": name,
                    "user_id": hash_user_identifier(user_id),
                    "input": input_payload or {},
                    "metadata": base_meta,
                },
                {"name": name, "metadata": base_meta},
                {"name": name},
            ],
        )

    return ObservationTrace(
        trace_id=trace_id,
        name=name,
        trace_client=trace_client,
        start_time=time.time(),
        metadata=base_meta,
    )


def record_feedback(trace_id: str, rating: float, comment: Optional[str] = None,
                    metadata: Optional[dict[str, Any]] = None) -> bool:
    """Record user feedback score against an existing trace id."""
    if not trace_id:
        return False

    client = get_langfuse_client()
    if client is None:
        return False

    payload_comment = comment or ""
    if metadata:
        meta_str = ", ".join(f"{k}={v}" for k, v in metadata.items())
        payload_comment = f"{payload_comment} | meta: {meta_str}" if payload_comment else f"meta: {meta_str}"

    result = _call_with_fallbacks(
        client,
        "score",
        [
            {
                "trace_id": trace_id,
                "name": "user_feedback",
                "value": rating,
                "comment": payload_comment,
            },
            {
                "traceId": trace_id,
                "name": "user_feedback",
                "value": rating,
                "comment": payload_comment,
            },
        ],
    )
    _call_with_fallbacks(client, "flush", [{}])
    return result is not None
