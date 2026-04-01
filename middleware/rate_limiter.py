"""
Rate Limiting Middleware for FastAPI
Implements tiered rate limiting with slowapi backend
"""

import logging
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config import RATE_LIMIT_GLOBAL, RATE_LIMIT_PER_USER

logger = logging.getLogger(__name__)


def _get_rate_limit_key(request: Request) -> str:
    """
    Get rate limit key based on user_id (if authenticated) or IP address.
    Prioritizes authenticated user for better tracking.
    """
    user_id = request.headers.get("X-User-ID", None)
    if user_id and user_id != "anonymous":
        return f"user:{user_id}"
    return f"ip:{get_remote_address(request)}"


# Initialize limiter with memory backend
limiter = Limiter(key_func=_get_rate_limit_key)


def get_limiter():
    """Get the configured limiter instance."""
    return limiter


def log_rate_limit_exceeded(request: Request, exc: RateLimitExceeded) -> None:
    """Log rate limit violations for monitoring."""
    key = _get_rate_limit_key(request)
    logger.warning(
        f"Rate limit exceeded",
        extra={
            "rate_limit_key": key,
            "path": request.url.path,
            "method": request.method,
            "limit": str(exc.detail),
        }
    )
