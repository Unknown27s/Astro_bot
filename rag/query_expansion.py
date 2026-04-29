"""
IMS AstroBot — Query Expansion

Generates semantically diverse sub-queries from the original user query
and merges their retrieval candidates back into a single ranked list.

Strategy
--------
1. Call the LLM once to produce N rewrite variants.
2. Run _retrieve_candidates_for_text for each variant (+ the original).
3. Merge all candidate lists with reciprocal rank fusion (RRF) so no
   single variant dominates and duplicates are handled cleanly.

Why RRF instead of raw score averaging?
  - Different query texts embed into slightly different score ranges.
    RRF is rank-based so it's scale-invariant and robust to that drift.
  - It's cheap: O(variants × candidates) with small constants.

Config keys (add to tests/config.py):
    QUERY_EXPANSION_ENABLED  bool   = False   # feature flag
    QUERY_EXPANSION_N        int    = 3        # rewrites to generate
    QUERY_EXPANSION_MAX_TOKENS int  = 150      # LLM budget
    QUERY_EXPANSION_RRF_K    int    = 60       # RRF constant (default 60)
    QUERY_EXPANSION_TEMPERATURE float = 0.3
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Config defaults  (overridden by tests/config.py values when imported)
# ---------------------------------------------------------------------------

_DEFAULTS = {
    "QUERY_EXPANSION_ENABLED": False,
    "QUERY_EXPANSION_N": 3,
    "QUERY_EXPANSION_MAX_TOKENS": 150,
    "QUERY_EXPANSION_RRF_K": 60,
    "QUERY_EXPANSION_TEMPERATURE": 0.3,
}


def _cfg(key: str):
    try:
        from tests import config as _c
        return getattr(_c, key, _DEFAULTS[key])
    except Exception:
        return _DEFAULTS[key]


# ---------------------------------------------------------------------------
# LLM-based query rewriting
# ---------------------------------------------------------------------------

_EXPANSION_SYSTEM = (
    "You are a query rewriting assistant for a university information retrieval system. "
    "Given a user question, produce semantically diverse paraphrases that cover different "
    "ways the same information might be expressed in institutional documents."
)

_EXPANSION_PROMPT_TMPL = (
    "Rewrite the following question into {n} alternative search queries. "
    "Each query should use different vocabulary or perspective but seek the same information. "
    "Output ONLY the queries, one per line, no numbering, no explanation.\n\n"
    "Original question: {query}"
)


@lru_cache(maxsize=256)
def _cached_expand(query: str, n: int, temperature: float, max_tokens: int) -> tuple[str, ...]:
    """
    LRU-cached expansion so repeated identical queries skip the LLM call.
    Returns a tuple of expansion strings (hashable for the cache).
    """
    try:
        from rag.providers.manager import get_manager
        mgr = get_manager()
        prompt = _EXPANSION_PROMPT_TMPL.format(n=n, query=query)
        raw = mgr.generate(
            system_prompt=_EXPANSION_SYSTEM,
            user_message=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if not raw:
            return ()
        lines = [l.strip() for l in raw.strip().splitlines()]
        # Strip leading bullets / numbers the model sometimes adds anyway
        cleaned = [re.sub(r"^[\d\.\-\*\)]+\s*", "", l) for l in lines if l]
        return tuple(q for q in cleaned if len(q) > 5)[:n]
    except Exception:
        return ()


def expand_query(query: str) -> list[str]:
    """
    Return a list of expansion queries for *query*.
    Returns an empty list when expansion is disabled or the LLM fails.
    The original query is NOT included — callers prepend it themselves.
    """
    if not _cfg("QUERY_EXPANSION_ENABLED"):
        return []
    if not (query or "").strip():
        return []

    n = int(_cfg("QUERY_EXPANSION_N"))
    temperature = float(_cfg("QUERY_EXPANSION_TEMPERATURE"))
    max_tokens = int(_cfg("QUERY_EXPANSION_MAX_TOKENS"))

    expansions = _cached_expand(query.strip(), n, temperature, max_tokens)
    return list(expansions)


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion
# ---------------------------------------------------------------------------

def reciprocal_rank_fusion(
    ranked_lists: list[list[dict]],
    rrf_k: int | None = None,
    candidate_key_fn=None,
) -> list[dict]:
    """
    Merge multiple ranked candidate lists using Reciprocal Rank Fusion.

    Args:
        ranked_lists:      Each inner list is already sorted best→worst.
        rrf_k:             RRF constant k (default: QUERY_EXPANSION_RRF_K).
        candidate_key_fn:  Callable(dict) → hashable key.  Defaults to
                           a (doc_id, page_key, chunk_index) tuple derived
                           from the candidate dict.

    Returns:
        Single merged list sorted by RRF score descending.
        Each dict retains all fields from the highest-scoring occurrence and
        gains an `rrf_score` field.
    """
    k = rrf_k if rrf_k is not None else int(_cfg("QUERY_EXPANSION_RRF_K"))

    if candidate_key_fn is None:
        def candidate_key_fn(c: dict):
            doc_id = str(c.get("doc_id") or c.get("source") or "")
            chunk_index = c.get("chunk_index", 0)
            page_index = c.get("page_index")
            if page_index is not None:
                page_key = f"page:{page_index}"
            elif url := c.get("source_url"):
                page_key = f"url:{url}"
            elif heading := (c.get("heading") or "").strip().lower():
                page_key = f"heading:{heading}"
            else:
                page_key = f"chunk:{chunk_index}"
            return (doc_id, page_key, chunk_index)

    rrf_scores: dict = {}
    best_candidate: dict = {}

    for ranked_list in ranked_lists:
        for rank, candidate in enumerate(ranked_list, start=1):
            key = candidate_key_fn(candidate)
            contribution = 1.0 / (k + rank)
            rrf_scores[key] = rrf_scores.get(key, 0.0) + contribution

            # Keep candidate dict with the highest original score
            existing = best_candidate.get(key)
            if existing is None or float(candidate.get("score", 0.0)) > float(existing.get("score", 0.0)):
                best_candidate[key] = candidate

    merged: list[dict] = []
    for key, rrf_score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True):
        c = {**best_candidate[key], "rrf_score": round(rrf_score, 6)}
        # Promote rrf_score to the primary score field so downstream
        # threshold / page-rank logic uses a consistent field.
        c["score"] = round(rrf_score, 6)
        merged.append(c)

    return merged


# ---------------------------------------------------------------------------
# High-level helper used by retriever.py
# ---------------------------------------------------------------------------

def expand_and_retrieve(
    query: str,
    retrieve_fn,          # callable: (text, **kwargs) -> list[dict]
    retrieve_kwargs: dict,
    trace=None,
) -> list[dict]:
    """
    Generate expansions, retrieve candidates for each (including the
    original query), and return a single RRF-merged list.

    Args:
        query:           Original user query (already normalised).
        retrieve_fn:     _retrieve_candidates_for_text from retriever.py.
        retrieve_kwargs: Keyword arguments forwarded to retrieve_fn
                         (collection, source_type, doc_id, top_k, list_query).
        trace:           Optional PipelineTrace for terminal output.

    Returns:
        RRF-merged candidate list, sorted by rrf_score descending.
        Falls back to the original query's candidates if expansion fails.
    """
    is_enabled = _cfg("QUERY_EXPANSION_ENABLED")
    expansions = expand_query(query) if is_enabled else []
    
    if trace and hasattr(trace, 'record_expansion'):
        trace.record_expansion(enabled=is_enabled, expansions=expansions)

    # Always include the original query
    texts = [query] + expansions

    if len(texts) == 1:
        # Expansion disabled or failed — avoid unnecessary overhead
        return retrieve_fn(retrieval_text=query, **retrieve_kwargs)

    ranked_lists: list[list[dict]] = []
    for text in texts:
        try:
            candidates = retrieve_fn(retrieval_text=text, **retrieve_kwargs)
            if candidates:
                ranked_lists.append(candidates)
        except Exception:
            continue

    if not ranked_lists:
        return []

    if len(ranked_lists) == 1:
        return ranked_lists[0]

    return reciprocal_rank_fusion(ranked_lists)