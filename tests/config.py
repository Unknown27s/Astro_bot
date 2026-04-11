"""Compatibility config module used by both app runtime and tests.

Many modules currently import from tests.config. To avoid ImportError and keep
behavior consistent, we re-export runtime settings from the main config module
and allow optional test-only overrides via TEST_* environment variables.
"""

import os

# Re-export all runtime settings first.
from config import *  # noqa: F401,F403

# Optional test-only overrides (used by test suite).
CONV_MATCH_THRESHOLD = float(os.getenv("TEST_CONV_MATCH_THRESHOLD", str(CONV_MATCH_THRESHOLD)))
CONV_ENABLED = os.getenv("TEST_CONV_ENABLED", str(CONV_ENABLED)).lower() == "true"
CONV_PER_USER = os.getenv("TEST_CONV_PER_USER", str(CONV_PER_USER)).lower() == "true"

MODEL_TEMPERATURE = float(os.getenv("TEST_MODEL_TEMPERATURE", str(MODEL_TEMPERATURE)))
MODEL_MAX_TOKENS = int(os.getenv("TEST_MODEL_MAX_TOKENS", str(MODEL_MAX_TOKENS)))

CHUNK_SIZE = int(os.getenv("TEST_CHUNK_SIZE", str(CHUNK_SIZE)))
CHUNK_OVERLAP = int(os.getenv("TEST_CHUNK_OVERLAP", str(CHUNK_OVERLAP)))

TOP_K_RESULTS = int(os.getenv("TEST_TOP_K_RESULTS", str(TOP_K_RESULTS)))
