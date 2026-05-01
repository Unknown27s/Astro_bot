"""
IMS AstroBot — RAG Retriever

Performs hybrid semantic + keyword search against ChromaDB and ranks
results by page/document groups.

Fixes applied vs original:
  - BM25 index built once; no per-query full corpus scan
  - _merge_candidates split into deduplicate / fuse / label — no mid-loop mutation bug
  - BM25 raw scores fused before normalisation so IDF scale is preserved
  - Hybrid score computed exactly once per candidate
  - _candidate_key defined once and shared
  - list-query boost extracted into a pure function
  - MIN_SCORE_THRESHOLD drops irrelevant chunks before returning
  - Embedding result cached with lru_cache (swap for Redis in production)
  - trace / obs_trace hooks actually called
  - Magic literals replaced with named constants
  - format_context_for_llm / get_source_citations stay here for now but
    are isolated at the bottom so they're easy to move to formatter.py
"""

from __future__ import annotations

import math
import re
import time
from collections import Counter, defaultdict
from functools import lru_cache
from typing import NamedTuple

from ingestion.embedder import get_collection, generate_embeddings
from rag.providers.manager import get_manager
from rag.observability.trace_context import get_trace_id, get_obs_trace
from tests.config import (
    FULL_PAGE_MAX_CHARS_PER_PAGE,
    FULL_PAGE_RAG_ENABLED,
    HYDE_ENABLED,
    HYDE_MAX_CHARS,
    HYDE_MAX_TOKENS,
    HYDE_SCORE_BLEND,
    HYDE_TEMPERATURE,
    HYDE_TRIGGER_SCORE,
    HYBRID_BM25_CANDIDATES,
    HYBRID_DENSE_CANDIDATES,
    HYBRID_DENSE_WEIGHT,
    RETRIEVAL_MODE,
    TOP_K_RESULTS,
)


# ---------------------------------------------------------------------------
# Tuneable constants  (keep all magic numbers here, not buried in functions)
# ---------------------------------------------------------------------------

_BM25_K1: float = 1.5
_BM25_B: float = 0.75

# Page-rank score formula weights  (must sum to 1.0)
_PAGE_RANK_BEST_WEIGHT: float = 0.6
_PAGE_RANK_AVG_WEIGHT: float = 0.3
_PAGE_RANK_COVERAGE_WEIGHT: float = 0.1
_PAGE_RANK_TOP_CHUNKS: int = 3        # chunks considered for avg score
_PAGE_RANK_COVERAGE_CAP: int = 6      # chunk count above which coverage = 1.0

# List-query score boosts
_LIST_BOOST_PAGE_INDEX: float = 0.05
_LIST_BOOST_BM25: float = 0.05
_LIST_BOOST_HEADING: float = 0.03

# Candidates fetched per retrieval mode (multipliers over top_k)
_DENSE_MULTIPLIER_DEFAULT: int = 6
_DENSE_MULTIPLIER_LIST: int = 8
_BM25_MULTIPLIER_DEFAULT: int = 6
_BM25_MULTIPLIER_LIST: int = 10

# Chunks whose final score is below this threshold are discarded.
# Prevents the LLM receiving irrelevant context when nothing matches.
MIN_SCORE_THRESHOLD: float = 0.20

_STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "could", "do",
    "for", "from", "how", "i", "in", "is", "it", "list", "of", "on", "or",
    "please", "show", "that", "the", "this", "to", "was", "were", "what",
    "when", "where", "which", "who", "why", "with", "would", "you", "your",
    "available",
})

_LIST_QUERY_PHRASES: tuple[str, ...] = (
    "what courses are available",
    "what is available",
    "what are available",
    "list",
    "show",
    "available courses",
    "course list",
    "courses available",
    "what programs are available",
)


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class Candidate(NamedTuple):
    """Typed key used to deduplicate candidates across retrieval methods."""
    doc_id: str
    page_key: str   # "page:<n>", "url:<u>", "heading:<h>", or "chunk:<i>"
    chunk_index: int | str


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    return " ".join((text or "").lower().split())


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]


def _is_list_style_query(query_text: str, query_tokens: list[str]) -> bool:
    if not query_text:
        return False
    if any(phrase in query_text for phrase in _LIST_QUERY_PHRASES):
        return True
    token_set = set(query_tokens)
    return bool(
        token_set & {"course", "courses", "program", "programs", "available"}
        and token_set & {"what", "list", "show", "which"}
    )


def _cosine_from_distance(distance: float) -> float:
    """Convert ChromaDB L2 distance to a cosine similarity in [0, 1]."""
    return max(0.0, min(1.0, 1.0 - distance / 2.0))


def _safe_source_type(metadata: dict, source_type: str | None) -> bool:
    if not source_type:
        return True
    meta = (metadata.get("source_type") or "uploaded").strip().lower()
    requested = source_type.strip().lower()
    if requested == "uploaded":
        return meta in {"", "uploaded"}
    return meta == requested


def _safe_doc_id(metadata: dict, doc_id: str | None) -> bool:
    """Optional doc_id filter for single-document retrieval testing."""
    if not doc_id:
        return True
    return str(metadata.get("doc_id") or "") == str(doc_id)


# ---------------------------------------------------------------------------
# Candidate key — defined ONCE, used everywhere
# ---------------------------------------------------------------------------

def _candidate_key(candidate: dict) -> Candidate:
    doc_id = str(candidate.get("doc_id") or candidate.get("source") or "")
    chunk_index = candidate.get("chunk_index", 0)
    page_index = candidate.get("page_index")

    if page_index is not None:
        page_key = f"page:{page_index}"
    elif url := candidate.get("source_url"):
        page_key = f"url:{url}"
    elif heading := (candidate.get("heading") or "").strip().lower():
        page_key = f"heading:{heading}"
    else:
        page_key = f"chunk:{chunk_index}"

    return Candidate(doc_id=doc_id, page_key=page_key, chunk_index=chunk_index)


def _group_key(candidate: dict) -> tuple[str, str]:
    key = _candidate_key(candidate)
    return key.doc_id, key.page_key


# ---------------------------------------------------------------------------
# BM25  (index built once per collection snapshot)
# ---------------------------------------------------------------------------

class _BM25Index:
    """
    Lightweight in-process BM25 index over a ChromaDB collection.

    Build once at startup (or whenever the collection changes) via
    `_BM25Index.build(collection)`, then call `.score(query_tokens)`.
    """

    __slots__ = ("_docs", "_metadatas", "_tokenized", "_df", "_avg_len")

    def __init__(
        self,
        docs: list[str],
        metadatas: list[dict],
        tokenized: list[list[str]],
        df: Counter[str],
        avg_len: float,
    ) -> None:
        self._docs = docs
        self._metadatas = metadatas
        self._tokenized = tokenized
        self._df = df
        self._avg_len = avg_len

    @classmethod
    def build(cls, collection) -> "_BM25Index":
        records = collection.get(include=["documents", "metadatas"])
        docs: list[str] = records.get("documents") or []
        metas: list[dict] = records.get("metadatas") or [{}] * len(docs)

        tokenized = [_tokenize(d) for d in docs]
        df: Counter[str] = Counter()
        for tokens in tokenized:
            df.update(set(tokens))

        lengths = [len(t) for t in tokenized]
        avg_len = sum(lengths) / max(len(lengths), 1)

        return cls(docs, metas, tokenized, df, avg_len)

    def query(
        self,
        query_tokens: list[str],
        source_type: str | None,
        doc_id: str | None,
        limit: int,
    ) -> list[dict]:
        """Return up to `limit` candidates ranked by raw BM25 score."""
        if not query_tokens:
            return []

        n = len(self._tokenized)
        raw_scores: list[float] = []

        for idx, tokens in enumerate(self._tokenized):
            if not _safe_source_type(self._metadatas[idx], source_type):
                raw_scores.append(0.0)
                continue
            if not _safe_doc_id(self._metadatas[idx], doc_id):
                raw_scores.append(0.0)
                continue

            tf = Counter(tokens)
            dl = len(tokens)
            score = 0.0
            for term in query_tokens:
                tf_t = tf.get(term, 0)
                if not tf_t:
                    continue
                df_t = self._df.get(term, 0)
                if not df_t:
                    continue
                idf = math.log(1 + (n - df_t + 0.5) / (df_t + 0.5))
                denom = tf_t + _BM25_K1 * (
                    1 - _BM25_B + _BM25_B * dl / max(self._avg_len, 1e-9)
                )
                score += idf * (tf_t * (_BM25_K1 + 1)) / denom
            raw_scores.append(score)

        # Pair with metadata; drop zeros; sort descending; take limit
        ranked = sorted(
            (
                (score, idx)
                for idx, score in enumerate(raw_scores)
                if score > 0
            ),
            key=lambda t: t[0],
            reverse=True,
        )[:limit]

        results: list[dict] = []
        for raw_score, idx in ranked:
            meta = self._metadatas[idx]
            results.append({
                "text": self._docs[idx],
                "source": meta.get("source", "Unknown"),
                "heading": meta.get("heading", ""),
                "doc_id": meta.get("doc_id", ""),
                "page_index": meta.get("page_index"),
                "chunk_index": meta.get("chunk_index", idx),
                "source_type": meta.get("source_type", "uploaded"),
                "source_url": meta.get("source_url", ""),
                "page_title": meta.get("page_title", ""),
                "bm25_score": raw_score,   # raw — normalised after fusion
                "dense_score": 0.0,
                "retrieval_method": "bm25",
            })

        return results


# Module-level index cache.  Call `invalidate_bm25_index()` when the
# collection is updated (e.g. after a new document is ingested).
_bm25_index: _BM25Index | None = None


def invalidate_bm25_index() -> None:
    global _bm25_index
    _bm25_index = None


def _get_bm25_index(collection) -> _BM25Index:
    global _bm25_index
    if _bm25_index is None:
        _bm25_index = _BM25Index.build(collection)
    return _bm25_index


# ---------------------------------------------------------------------------
# Embedding cache  (LRU — replace with Redis/Memcached in production)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=512)
def _cached_embedding(query_text: str) -> tuple[float, ...]:
    """Cache embedding by query text. Returns a tuple so it's hashable."""
    return tuple(generate_embeddings([query_text])[0])


# ---------------------------------------------------------------------------
# Dense retrieval
# ---------------------------------------------------------------------------

def _dense_candidates(
    collection,
    query_embedding: list[float],
    source_type: str | None,
    doc_id: str | None,
    limit: int,
) -> list[dict]:
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit,
        include=["documents", "metadatas", "distances"],
    )

    if not results or not (results.get("documents") or [[]])[0]:
        return []

    candidates: list[dict] = []
    for idx, doc in enumerate(results["documents"][0]):
        meta = (results.get("metadatas") or [[{}] * limit])[0][idx]
        if not _safe_source_type(meta, source_type):
            continue
        if not _safe_doc_id(meta, doc_id):
            continue
        distance = (results.get("distances") or [[0.0] * limit])[0][idx]
        candidates.append({
            "text": doc,
            "source": meta.get("source", "Unknown"),
            "heading": meta.get("heading", ""),
            "doc_id": meta.get("doc_id", ""),
            "page_index": meta.get("page_index"),
            "chunk_index": meta.get("chunk_index", idx),
            "source_type": meta.get("source_type", "uploaded"),
            "source_url": meta.get("source_url", ""),
            "page_title": meta.get("page_title", ""),
            "dense_score": _cosine_from_distance(float(distance)),
            "bm25_score": 0.0,
            "retrieval_method": "dense",
        })

    return candidates


# ---------------------------------------------------------------------------
# Score fusion  (fixed: normalise AFTER merging, not before)
# ---------------------------------------------------------------------------

def _deduplicate(candidates: list[dict]) -> dict[Candidate, dict]:
    """
    Merge duplicate candidates, keeping the max component scores.
    Returns a dict keyed by Candidate so downstream steps share the same key.
    """
    merged: dict[Candidate, dict] = {}
    for c in candidates:
        key = _candidate_key(c)
        existing = merged.get(key)
        if existing is None:
            merged[key] = {**c, "dense_score": float(c.get("dense_score") or 0.0),
                           "bm25_score": float(c.get("bm25_score") or 0.0)}
        else:
            existing["dense_score"] = max(existing["dense_score"],
                                          float(c.get("dense_score") or 0.0))
            existing["bm25_score"] = max(existing["bm25_score"],
                                         float(c.get("bm25_score") or 0.0))
            # Keep the candidate with the higher metadata richness
            if c.get("heading") and not existing.get("heading"):
                existing.update({k: v for k, v in c.items()
                                  if k not in ("dense_score", "bm25_score")})
    return merged


def _fuse_scores(merged: dict[Candidate, dict], bm25_max: float) -> list[dict]:
    """
    Normalise BM25 raw scores across all candidates (not per-result-set),
    then compute a single hybrid score.  Returns a flat list.
    """
    result: list[dict] = []
    for c in merged.values():
        bm25_norm = (c["bm25_score"] / bm25_max) if bm25_max > 0 else 0.0
        dense = c["dense_score"]
        hybrid = round(
            HYBRID_DENSE_WEIGHT * dense + (1 - HYBRID_DENSE_WEIGHT) * bm25_norm,
            4,
        )
        c["bm25_score_norm"] = round(bm25_norm, 4)
        c["score"] = hybrid
        c["retrieval_method"] = (
            "hybrid" if c["bm25_score"] > 0 and c["dense_score"] > 0
            else ("bm25" if c["bm25_score"] > 0 else "dense")
        )
        result.append(c)
    return result


def _merge_candidates(
    dense: list[dict],
    bm25: list[dict],
) -> list[dict]:
    """Deduplicate, fuse scores, return ranked list."""
    all_candidates = dense + bm25
    merged = _deduplicate(all_candidates)
    bm25_max = max((c["bm25_score"] for c in merged.values()), default=0.0)
    fused = _fuse_scores(merged, bm25_max)
    fused.sort(key=lambda c: c["score"], reverse=True)
    return fused


# ---------------------------------------------------------------------------
# List-query boost  (pure function — easy to test / disable)
# ---------------------------------------------------------------------------

def _apply_list_boost(candidates: list[dict]) -> list[dict]:
    for c in candidates:
        boost = 0.0
        if c.get("page_index") is not None:
            boost += _LIST_BOOST_PAGE_INDEX
        if c.get("bm25_score", 0.0) > 0:
            boost += _LIST_BOOST_BM25
        if c.get("heading"):
            boost += _LIST_BOOST_HEADING
        c["score"] = round(min(1.0, c.get("score", 0.0) + boost), 4)
    return candidates


def _generate_hypothetical_passage(query: str) -> str:
    """
    Generate a short hypothetical answer passage for HyDE retrieval.
    Returns an empty string when generation is unavailable.
    """
    if not query.strip():
        return ""

    try:
        mgr = get_manager()
        hyde_prompt = (
            "Write a short factual passage (3-6 sentences) that likely answers "
            "the user question using institutional/policy language. "
            "Do not include disclaimers or markdown.\n\n"
            f"Question: {query}"
        )
        generated = mgr.generate(
            system_prompt=(
                "You create concise retrieval-oriented hypothetical passages "
                "for semantic search expansion."
            ),
            user_message=hyde_prompt,
            temperature=HYDE_TEMPERATURE,
            max_tokens=HYDE_MAX_TOKENS,
        )
        if not generated:
            return ""
        return generated.strip()[:HYDE_MAX_CHARS]
    except Exception:
        return ""


def _retrieve_candidates_for_text(
    collection,
    retrieval_text: str,
    source_type: str | None,
    doc_id: str | None,
    top_k: int,
    list_query: bool,
) -> list[dict]:
    """Run dense/hybrid retrieval for a given text and return scored candidates."""
    retrieval_tokens = _tokenize(retrieval_text)
    query_embedding = list(_cached_embedding(retrieval_text))

    dense_mult = _DENSE_MULTIPLIER_LIST if list_query else _DENSE_MULTIPLIER_DEFAULT
    bm25_mult = _BM25_MULTIPLIER_LIST if list_query else _BM25_MULTIPLIER_DEFAULT
    dense_limit = min(max(top_k * dense_mult, HYBRID_DENSE_CANDIDATES), collection.count())
    bm25_limit = min(max(top_k * bm25_mult, HYBRID_BM25_CANDIDATES), collection.count())

    dense = _dense_candidates(collection, query_embedding, source_type, doc_id, dense_limit)

    if RETRIEVAL_MODE == "dense":
        all_candidates = dense
        for c in all_candidates:
            c["score"] = round(c["dense_score"], 4)
    else:
        index = _get_bm25_index(collection)
        bm25 = index.query(retrieval_tokens, source_type, doc_id, bm25_limit)
        all_candidates = _merge_candidates(dense, bm25)

    if list_query:
        all_candidates = _apply_list_boost(all_candidates)

    return all_candidates


def _blend_hyde_candidates(base_candidates: list[dict], hyde_candidates: list[dict]) -> list[dict]:
    """Merge base and HyDE candidates, blending scores when both overlap."""
    merged: dict[Candidate, dict] = {_candidate_key(c): {**c} for c in base_candidates}

    for h in hyde_candidates:
        key = _candidate_key(h)
        existing = merged.get(key)
        hyde_score = float(h.get("score", 0.0))

        if existing is None:
            merged[key] = {
                **h,
                "score": round(hyde_score * HYDE_SCORE_BLEND, 4),
                "retrieval_method": f"{h.get('retrieval_method', 'dense')}_hyde",
                "hyde_score": round(hyde_score, 4),
            }
            continue

        base_score = float(existing.get("score", 0.0))
        blended = ((1 - HYDE_SCORE_BLEND) * base_score) + (HYDE_SCORE_BLEND * hyde_score)
        existing["score"] = round(max(base_score, blended), 4)
        existing["hyde_score"] = round(hyde_score, 4)

        method = str(existing.get("retrieval_method", "dense"))
        if "hyde" not in method:
            existing["retrieval_method"] = f"{method}+hyde"

    fused = list(merged.values())
    fused.sort(key=lambda c: c.get("score", 0.0), reverse=True)
    return fused


# ---------------------------------------------------------------------------
# Page-group ranking
# ---------------------------------------------------------------------------

def _rank_by_page(candidates: list[dict], top_k: int) -> list[dict]:
    if not candidates:
        return []

    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for c in candidates:
        groups[_group_key(c)].append(c)

    ranked_groups: list[dict] = []
    for gk, items in groups.items():
        ordered = sorted(items, key=lambda c: c.get("score", 0.0), reverse=True)
        top_scores = [float(c.get("score", 0.0)) for c in ordered[:_PAGE_RANK_TOP_CHUNKS]]
        best = top_scores[0] if top_scores else 0.0
        avg = sum(top_scores) / len(top_scores) if top_scores else 0.0
        coverage = min(len(items), _PAGE_RANK_COVERAGE_CAP) / _PAGE_RANK_COVERAGE_CAP
        page_score = round(
            _PAGE_RANK_BEST_WEIGHT * best
            + _PAGE_RANK_AVG_WEIGHT * avg
            + _PAGE_RANK_COVERAGE_WEIGHT * coverage,
            4,
        )
        ranked_groups.append({"group_key": gk, "page_score": page_score, "items": ordered})

    ranked_groups.sort(key=lambda g: g["page_score"], reverse=True)

    # Two-pass selection: first pick the best chunk from each group,
    # then fill remaining slots with second-best chunks, etc.
    final: list[dict] = []
    seen: set[Candidate] = set()

    for pass_idx in range(2):
        for group in ranked_groups:
            for chunk in group["items"]:
                key = _candidate_key(chunk)
                if key in seen:
                    continue
                final.append(chunk)
                seen.add(key)
                if len(final) >= top_k:
                    return final
                if pass_idx == 0:
                    break  # one chunk per group on the first pass

    return final


def _to_int(value) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _chunk_sort_key(metadata: dict) -> int:
    chunk_index = _to_int((metadata or {}).get("chunk_index"))
    return chunk_index if chunk_index is not None else 0


def _clean_page_text(text: str) -> str:
    """Normalize common PDF extraction artifacts for full-page context."""
    if not text:
        return ""
    text = text.replace(" | ", " ").replace("|", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _truncate_page_text(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    clipped = text[:max_chars]
    if " " in clipped:
        clipped = clipped.rsplit(" ", 1)[0]
    return f"{clipped} ... [truncated]"


def _fetch_full_page_text(
    collection,
    doc_id: str,
    page_index: int,
    source_type: str | None,
) -> tuple[str, int]:
    """
    Return full text for a single page by stitching all page chunks in order.

    Returns:
        (page_text, chunk_count)
    """
    records = None

    # Preferred path: query exactly one page from one document.
    try:
        records = collection.get(
            where={"$and": [{"doc_id": doc_id}, {"page_index": page_index}]},
            include=["documents", "metadatas"],
        )
    except Exception:
        records = None

    docs = (records or {}).get("documents") or []
    metas = (records or {}).get("metadatas") or []

    # Fallback path for backends that do not support combined where clauses.
    if not docs:
        try:
            fallback = collection.get(where={"doc_id": doc_id}, include=["documents", "metadatas"])
            raw_docs = fallback.get("documents") or []
            raw_metas = fallback.get("metadatas") or []
            filtered: list[tuple[str, dict]] = []
            for idx, raw_doc in enumerate(raw_docs):
                meta = raw_metas[idx] if idx < len(raw_metas) else {}
                if not _safe_source_type(meta, source_type):
                    continue
                if _to_int(meta.get("page_index")) != page_index:
                    continue
                filtered.append((raw_doc, meta))
        except Exception:
            return "", 0
    else:
        filtered = []
        for idx, raw_doc in enumerate(docs):
            meta = metas[idx] if idx < len(metas) else {}
            if not _safe_source_type(meta, source_type):
                continue
            filtered.append((raw_doc, meta))

    if not filtered:
        return "", 0

    filtered.sort(key=lambda item: _chunk_sort_key(item[1]))
    page_parts: list[str] = []

    for raw_text, meta in filtered:
        text = str(raw_text or "").strip()
        heading = str((meta or {}).get("heading") or "").strip()
        if heading and text.lower().startswith(heading.lower()):
            text = text[len(heading):].strip()
        cleaned = _clean_page_text(text)
        if cleaned:
            page_parts.append(cleaned)

    full_page_text = _clean_page_text("\n".join(page_parts))
    full_page_text = _truncate_page_text(full_page_text, FULL_PAGE_MAX_CHARS_PER_PAGE)
    return full_page_text, len(filtered)


def _expand_to_full_pages(
    collection,
    ranked_chunks: list[dict],
    source_type: str | None,
    top_k: int,
) -> list[dict]:
    """Expand top ranked chunk hits into full-page blocks for LLM context."""
    if not ranked_chunks:
        return []

    expanded: list[dict] = []
    seen_pages: set[tuple[str, int]] = set()

    for chunk in ranked_chunks:
        if len(expanded) >= top_k:
            break

        doc_id = str(chunk.get("doc_id") or "")
        page_index = _to_int(chunk.get("page_index"))

        # If this hit is not page-addressable, keep the original chunk.
        if not doc_id or page_index is None:
            expanded.append(chunk)
            continue

        page_key = (doc_id, page_index)
        if page_key in seen_pages:
            continue
        seen_pages.add(page_key)

        page_text, chunk_count = _fetch_full_page_text(
            collection=collection,
            doc_id=doc_id,
            page_index=page_index,
            source_type=source_type,
        )

        if not page_text:
            expanded.append(chunk)
            continue

        enriched = {**chunk}
        enriched["text"] = page_text
        enriched["heading"] = enriched.get("heading") or f"Page {page_index}"
        enriched["chunk_count"] = chunk_count
        method = str(enriched.get("retrieval_method") or "dense")
        if "full_page" not in method:
            enriched["retrieval_method"] = f"{method}+full_page"
        expanded.append(enriched)

    return expanded[:top_k]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def retrieve_context(
    query: str,
    top_k: int = TOP_K_RESULTS,
    source_type: str | None = None,
    doc_id: str | None = None,
    trace=None,
    obs_trace=None,
    **_kwargs,
) -> list[dict]:
    """
    Retrieve the most relevant document chunks for a given query.

    Args:
        query:       The user's question.
        top_k:       Number of results to return.
        source_type: Optional source filter — "uploaded" or "official_site".
        doc_id:      Optional document ID filter for single-document retrieval.
        trace:       Optional tracing span (Langfuse / OpenTelemetry).
        obs_trace:   Optional secondary observability handle.

    Returns:
        List of dicts with keys: text, source, heading, score, doc_id,
        page_index, source_type, source_url, retrieval_method.
        When FULL_PAGE_RAG_ENABLED is true, page-addressable hits are expanded
        into full page text blocks before returning.
        Chunks below MIN_SCORE_THRESHOLD are excluded.
    """
    obs_span = _start_obs_span(
        obs_trace,
        name="rag.retrieve_context",
        input_payload={"query": query, "top_k": top_k, "source_type": source_type, "doc_id": doc_id},
    )

    trace_start = time.perf_counter()

    collection = get_collection()
    if collection.count() == 0:
        _finish_obs_span(obs_span, output={"returned": 0}, metadata={"collection_size": 0})
        return []

    query_text = _normalize(query)
    query_tokens = _tokenize(query_text)
    list_query = _is_list_style_query(query_text, query_tokens)

    from rag.query_expansion import expand_and_retrieve
    from tests.config import QUERY_EXPANSION_ENABLED, QUERY_EXPANSION_TRIGGER_SCORE

    # Step 1: Retrieve with original query first
    original_candidates = _retrieve_candidates_for_text(
        collection=collection,
        retrieval_text=query_text or query,
        source_type=source_type,
        doc_id=doc_id,
        top_k=top_k,
        list_query=list_query,
    )

    # Step 2: Check top score to decide if expansion is needed
    top_score = max((float(c.get("score", 0.0)) for c in original_candidates), default=0.0)

    # Step 3: Apply query expansion if enabled and score is below threshold
    if QUERY_EXPANSION_ENABLED and top_score < QUERY_EXPANSION_TRIGGER_SCORE:
        all_candidates = expand_and_retrieve(
            query=query_text or query,
            retrieve_fn=_retrieve_candidates_for_text,
            retrieve_kwargs={
                "collection": collection,
                "source_type": source_type,
                "doc_id": doc_id,
                "top_k": top_k,
                "list_query": list_query,
            },
            trace=trace,
            top_score=top_score,
        )
    else:
        # Score is good or expansion disabled - use original results
        all_candidates = original_candidates

    hyde_applied = False
    top_score = max((float(c.get("score", 0.0)) for c in all_candidates), default=0.0)
    if HYDE_ENABLED and top_score < HYDE_TRIGGER_SCORE:
        hyde_text = _generate_hypothetical_passage(query)
        if hyde_text:
            hyde_applied = True
            hyde_candidates = _retrieve_candidates_for_text(
                collection=collection,
                retrieval_text=_normalize(hyde_text),
                source_type=source_type,
                doc_id=doc_id,
                top_k=top_k,
                list_query=list_query,
            )
            all_candidates = _blend_hyde_candidates(all_candidates, hyde_candidates)

    # Drop low-confidence chunks before page ranking
    all_candidates = [c for c in all_candidates if c.get("score", 0.0) >= MIN_SCORE_THRESHOLD]

    ranked = _rank_by_page(all_candidates, top_k)
    if FULL_PAGE_RAG_ENABLED:
        ranked = _expand_to_full_pages(
            collection=collection,
            ranked_chunks=ranked,
            source_type=source_type,
            top_k=top_k,
        )

    elapsed_ms = round((time.perf_counter() - trace_start) * 1000, 2)
    _trace_event(trace, "retrieve_context.done", {
        "candidates_before_threshold": len(all_candidates),
        "returned": len(ranked),
        "collection_size": collection.count(),
        "top_k": top_k,
        "doc_id": doc_id or "",
        "full_page_rag": FULL_PAGE_RAG_ENABLED,
        "hyde_applied": hyde_applied,
        "top_score": round(top_score, 4),
        "elapsed_ms": elapsed_ms,
    })
    _finish_obs_span(
        obs_span,
        output={"returned": len(ranked)},
        metadata={
            "candidates_before_threshold": len(all_candidates),
            "collection_size": collection.count(),
            "top_k": top_k,
            "doc_id": doc_id or "",
            "full_page_rag": FULL_PAGE_RAG_ENABLED,
            "hyde_applied": hyde_applied,
            "top_score": round(top_score, 4),
            "elapsed_ms": elapsed_ms,
        },
    )

    context_chunks: list[dict] = []
    for c in ranked:
        page_index = c.get("page_index")
        page_label = (
            f"Page {page_index}" if page_index is not None
            else str(c.get("page_title", ""))
        )
        context_chunks.append({
            "text": c.get("text", ""),
            "source": c.get("source", "Unknown"),
            "heading": c.get("heading", "") or page_label,
            "score": round(float(c.get("score", 0.0)), 4),
            "doc_id": c.get("doc_id", ""),
            "page_index": page_index,
            "source_type": c.get("source_type", "uploaded"),
            "source_url": c.get("source_url", ""),
            "retrieval_method": c.get("retrieval_method", "dense"),
        })

    return context_chunks


def _trace_event(trace, name: str, data: dict) -> None:
    """Fire a trace event if a tracer is attached — no-op otherwise."""
    if trace is None:
        return
    try:
        if hasattr(trace, "event"):
            trace.event(name=name, metadata=data)
            return

        if name == "retrieve_context.done" and hasattr(trace, "record_search"):
            trace.record_search(
                collection_size=int(data.get("collection_size", 0)),
                top_k=int(data.get("top_k", 0)),
                time_ms=float(data.get("elapsed_ms", 0.0)),
            )
            return

        if hasattr(trace, "update"):
            trace.update(metadata={"name": name, **data})
    except Exception:
        pass  # never let observability break retrieval


def _start_obs_span(obs_trace, name: str, input_payload: dict | None = None):
    """Start an ObservationTrace span if available."""
    if obs_trace is None or not hasattr(obs_trace, "start_span"):
        return None
    try:
        return obs_trace.start_span(name, input_payload=input_payload or {}, metadata=input_payload or {})
    except Exception:
        return None


def _finish_obs_span(span, output: dict | None = None, metadata: dict | None = None) -> None:
    """End an ObservationTrace span if one was started."""
    if span is None or not hasattr(span, "end"):
        return
    try:
        span.end(output=output, metadata=metadata)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Formatting helpers  (move to formatter.py when this module grows further)
# ---------------------------------------------------------------------------

def format_context_for_llm(chunks: list[dict]) -> str:
    """Format retrieved chunks into a context string for the LLM prompt."""
    if not chunks:
        return "No relevant documents found in the knowledge base."

    parts: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        source_info = f"[Source: {chunk['source']}"
        if chunk.get("heading"):
            source_info += f" > {chunk['heading']}"
        if chunk.get("page_index") is not None:
            source_info += f" | Page {chunk['page_index']}"
        source_info += f" | Relevance: {chunk['score']:.0%}]"
        parts.append(f"--- Context {i} {source_info} ---\n{chunk['text']}")

    return "\n\n".join(parts)


def get_source_citations(chunks: list[dict]) -> str:
    """Format source citations for display."""
    if not chunks:
        return ""

    seen: set[tuple] = set()
    citations: list[str] = []
    for chunk in chunks:
        source = chunk.get("source", "Unknown")
        page_index = chunk.get("page_index")
        key = (source, page_index if page_index is not None else chunk.get("heading", ""))
        if key in seen:
            continue
        seen.add(key)
        heading = chunk.get("heading", "")
        score = chunk.get("score", 0.0)
        citation = f"[doc] {source}"
        if heading:
            citation += f" — {heading}"
        if page_index is not None:
            citation += f" (Page {page_index})"
        citation += f" ({score:.0%} match)"
        citations.append(citation)

    return "\n".join(citations)