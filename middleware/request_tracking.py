"""
Request Tracking Middleware
Adds request IDs and user context to all API requests
"""

import uuid
import logging
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import sentry_sdk

logger = logging.getLogger(__name__)


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that tracks each request with a unique ID and logs performance metrics.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Extract user info from headers/auth (if available)
        user_id = request.headers.get("X-User-ID", "anonymous")
        username = request.headers.get("X-Username", "anonymous")

        # Add to Sentry context
        with sentry_sdk.push_scope() as scope:
            scope.set_context("request", {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
            })
            scope.set_user({
                "id": user_id,
                "username": username,
            })

            # Log request start
            logger.debug(
                f"Request started",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "user_id": user_id,
                }
            )

            start_time = time.time()

            try:
                response = await call_next(request)
                elapsed_ms = (time.time() - start_time) * 1000

                # Log request completion
                logger.info(
                    f"Request completed",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status": response.status_code,
                        "elapsed_ms": round(elapsed_ms, 2),
                        "user_id": user_id,
                    }
                )

                # Add request ID to response headers
                response.headers["X-Request-ID"] = request_id

                return response

            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Request failed with exception",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "error": str(e),
                        "elapsed_ms": round(elapsed_ms, 2),
                        "user_id": user_id,
                    },
                    exc_info=True,
                )
                raise


class ErrorContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds contextual information to error responses
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.exception(
                f"Unhandled exception in {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "user_id": request.headers.get("X-User-ID", "anonymous"),
                }
            )
            raise
