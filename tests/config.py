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
RETRIEVAL_MODE = os.getenv("TEST_RETRIEVAL_MODE", str(RETRIEVAL_MODE))
HYBRID_DENSE_WEIGHT = float(os.getenv("TEST_HYBRID_DENSE_WEIGHT", str(HYBRID_DENSE_WEIGHT)))
HYBRID_BM25_CANDIDATES = int(os.getenv("TEST_HYBRID_BM25_CANDIDATES", str(HYBRID_BM25_CANDIDATES)))
HYBRID_DENSE_CANDIDATES = int(os.getenv("TEST_HYBRID_DENSE_CANDIDATES", str(HYBRID_DENSE_CANDIDATES)))
FULL_PAGE_RAG_ENABLED = os.getenv("TEST_FULL_PAGE_RAG_ENABLED", str(FULL_PAGE_RAG_ENABLED)).lower() == "true"
FULL_PAGE_MAX_CHARS_PER_PAGE = int(
	os.getenv("TEST_FULL_PAGE_MAX_CHARS_PER_PAGE", str(FULL_PAGE_MAX_CHARS_PER_PAGE))
)
HYDE_ENABLED = os.getenv("TEST_HYDE_ENABLED", str(HYDE_ENABLED)).lower() == "true"
HYDE_TRIGGER_SCORE = float(os.getenv("TEST_HYDE_TRIGGER_SCORE", str(HYDE_TRIGGER_SCORE)))
HYDE_SCORE_BLEND = float(os.getenv("TEST_HYDE_SCORE_BLEND", str(HYDE_SCORE_BLEND)))
HYDE_MAX_TOKENS = int(os.getenv("TEST_HYDE_MAX_TOKENS", str(HYDE_MAX_TOKENS)))
HYDE_MAX_CHARS = int(os.getenv("TEST_HYDE_MAX_CHARS", str(HYDE_MAX_CHARS)))
HYDE_TEMPERATURE = float(os.getenv("TEST_HYDE_TEMPERATURE", str(HYDE_TEMPERATURE)))

QUERY_EXPANSION_ENABLED = os.getenv("TEST_QUERY_EXPANSION_ENABLED", str(QUERY_EXPANSION_ENABLED)).lower() == "true"
QUERY_EXPANSION_TRIGGER_SCORE = float(os.getenv("TEST_QUERY_EXPANSION_TRIGGER_SCORE", str(QUERY_EXPANSION_TRIGGER_SCORE)))
QUERY_EXPANSION_N = int(os.getenv("TEST_QUERY_EXPANSION_N", str(QUERY_EXPANSION_N)))
QUERY_EXPANSION_MAX_TOKENS = int(os.getenv("TEST_QUERY_EXPANSION_MAX_TOKENS", str(QUERY_EXPANSION_MAX_TOKENS)))
QUERY_EXPANSION_RRF_K = int(os.getenv("TEST_QUERY_EXPANSION_RRF_K", str(QUERY_EXPANSION_RRF_K)))
QUERY_EXPANSION_TEMPERATURE = float(os.getenv("TEST_QUERY_EXPANSION_TEMPERATURE", str(QUERY_EXPANSION_TEMPERATURE)))

OFFICIAL_SITE_ALLOWED_DOMAINS = [
	domain.strip().lower()
	for domain in os.getenv("TEST_OFFICIAL_SITE_ALLOWED_DOMAINS", ",".join(OFFICIAL_SITE_ALLOWED_DOMAINS)).split(",")
	if domain.strip()
]
OFFICIAL_SITE_TIMEOUT_SECONDS = int(os.getenv("TEST_OFFICIAL_SITE_TIMEOUT_SECONDS", str(OFFICIAL_SITE_TIMEOUT_SECONDS)))
OFFICIAL_SITE_USER_AGENT = os.getenv("TEST_OFFICIAL_SITE_USER_AGENT", OFFICIAL_SITE_USER_AGENT)
