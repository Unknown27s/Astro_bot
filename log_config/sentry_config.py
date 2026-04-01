"""
Sentry Error Tracking Configuration
Initializes Sentry SDK for production error tracking and performance monitoring
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from config import SENTRY_DSN, SENTRY_ENVIRONMENT, SENTRY_TRACES_SAMPLE_RATE, SENTRY_ERROR_SAMPLE_RATE


def init_sentry():
    """Initialize Sentry SDK for error tracking."""
    if not SENTRY_DSN:
        return False

    try:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=SENTRY_ENVIRONMENT,
            traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
            sample_rate=SENTRY_ERROR_SAMPLE_RATE,
            integrations=[
                FastApiIntegration(),
                StarletteIntegration(),
            ],
            before_send=_before_send_handler,
            attach_stacktrace=True,
            max_breadcrumbs=50,
            debug=False,
        )
        return True
    except Exception as e:
        print(f"[Sentry] Failed to initialize: {e}")
        return False


def _before_send_handler(event, hint):
    """
    Filter events before sending to Sentry.
    Exclude noisy errors or sensitive information.
    """
    # Exclude SQLite database locked errors (transient)
    if "database is locked" in str(event.get("message", "")):
        return None

    # Exclude rate limit errors (expected)
    if "rate_limit" in str(event.get("tags", {})):
        return None

    return event


def add_sentry_context(user_id: str = None, username: str = None, **kwargs):
    """Add contextual information to Sentry."""
    with sentry_sdk.push_scope() as scope:
        if user_id:
            scope.set_user({"id": user_id, "username": username})
        for key, value in kwargs.items():
            scope.set_context(key, value)
