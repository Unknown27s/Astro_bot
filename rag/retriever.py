"""
IMS AstroBot — RAG Retriever
Performs hybrid semantic + keyword search against ChromaDB and ranks results by page/document groups.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from ingestion.embedder import get_collection, generate_embeddings
from tests.config import HYBRID_BM25_CANDIDATES, HYBRID_DENSE_CANDIDATES, HYBRID_DENSE_WEIGHT, RETRIEVAL_MODE, TOP_K_RESULTS

_BM25_K1 = 1.5
_BM25_B = 0.75

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "could", "do", "for", "from",
    "how", "i", "in", "is", "it", "list", "of", "on", "or", "please", "show", "that",
    "the", "this", "to", "was", "were", "what", "when", "where", "which", "who", "why",
    "with", "would", "you", "your", "available",
}

_LIST_QUERY_PHRASES = (
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


def _normalize_query_text(query: str) -> str:
    return " ".join((query or "").lower().split())


def _is_list_style_query(query_text: str, query_tokens: list[str]) -> bool:
    if not query_text:
        return False

    if any(phrase in query_text for phrase in _LIST_QUERY_PHRASES):
        return True

    token_set = set(query_tokens)
    return bool(
        token_set.intersection({"course", "courses", "program", "programs", "available"})
        and token_set.intersection({"what", "list", "show", "which"})
    )


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    return [token for token in tokens if token not in _STOPWORDS and len(token) > 1]


def _cosine_similarity_from_distance(distance: float) -> float:
    return max(0.0, min(1.0, 1 - (distance / 2)))


def _safe_source_type(metadata: dict, source_type: str | None) -> bool:
    if not source_type:
        return True

    meta_source_type = (metadata.get("source_type") or "uploaded").strip().lower()
    requested = source_type.strip().lower()
    if requested == "uploaded":
        return meta_source_type in {"", "uploaded"}
    return meta_source_type == requested


def _bm25_scores(documents: list[str], query_tokens: list[str]) -> list[float]:
    if not documents or not query_tokens:
        return [0.0] * len(documents)

    tokenized_docs = [_tokenize(document) for document in documents]
    if not any(tokenized_docs):
        return [0.0] * len(documents)

    doc_lengths = [len(tokens) for tokens in tokenized_docs]
    avg_doc_length = sum(doc_lengths) / max(len(doc_lengths), 1)

    document_frequencies: Counter[str] = Counter()
    for tokens in tokenized_docs:
        document_frequencies.update(set(tokens))

    total_docs = len(tokenized_docs)
    scores: list[float] = []
    for tokens, doc_length in zip(tokenized_docs, doc_lengths):
        term_counts = Counter(tokens)
        score = 0.0
        for term in query_tokens:
            term_frequency = term_counts.get(term, 0)
            if not term_frequency:
                continue

            doc_frequency = document_frequencies.get(term, 0)
            if not doc_frequency:
                continue

            idf = math.log(1 + ((total_docs - doc_frequency + 0.5) / (doc_frequency + 0.5)))
            denominator = term_frequency + _BM25_K1 * (1 - _BM25_B + _BM25_B * (doc_length / max(avg_doc_length, 1e-9)))
            score += idf * (term_frequency * (_BM25_K1 + 1)) / denominator
        scores.append(score)

    return scores


def _group_key(metadata: dict, default_key: str) -> tuple[str, str]:
    doc_id = str(metadata.get("doc_id") or metadata.get("source") or default_key)
    page_index = metadata.get("page_index")
    if page_index is not None:
        return doc_id, f"page:{page_index}"

    source_url = metadata.get("source_url")
    if source_url:
        return doc_id, f"url:{source_url}"

    heading = (metadata.get("heading") or "").strip().lower()
    if heading:
        return doc_id, f"heading:{heading}"

    return doc_id, f"chunk:{metadata.get('chunk_index', default_key)}"


def _dense_candidates(collection, query_embedding: list[float], source_type: str | None, dense_limit: int) -> list[dict]:
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=dense_limit,
        include=["documents", "metadatas", "distances"],
    )

    candidates: list[dict] = []
    if not results or not results.get("documents") or not results["documents"][0]:
        return candidates

    for index, document in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][index] if results.get("metadatas") else {}
        if not _safe_source_type(metadata, source_type):
            continue

        distance = results["distances"][0][index] if results.get("distances") else 0
        candidates.append(
            {
                "text": document,
                "source": metadata.get("source", "Unknown"),
                "heading": metadata.get("heading", ""),
                "doc_id": metadata.get("doc_id", ""),
                "page_index": metadata.get("page_index"),
                "chunk_index": metadata.get("chunk_index", index),
                "source_type": metadata.get("source_type", "uploaded"),
                "source_url": metadata.get("source_url", ""),
                "page_title": metadata.get("page_title", ""),
                "dense_score": _cosine_similarity_from_distance(float(distance)),
                "retrieval_method": "dense",
            }
        )

    return candidates


def _bm25_candidates(collection, source_type: str | None, bm25_limit: int, query_tokens: list[str]) -> list[dict]:
    records = collection.get(include=["documents", "metadatas"])
    if not records or not records.get("documents"):
        return []

    documents: list[str] = []
    metadatas: list[dict] = []
    for index, document in enumerate(records["documents"]):
        metadata = records["metadatas"][index] if records.get("metadatas") else {}
        if not _safe_source_type(metadata, source_type):
            continue
        documents.append(document)
        metadatas.append(metadata)

    if not documents:
        return []

    raw_scores = _bm25_scores(documents, query_tokens)
    max_score = max(raw_scores) if raw_scores else 0.0
    if max_score <= 0:
        return []

    ranked_items: list[dict] = []
    for index, (document, metadata, raw_score) in enumerate(zip(documents, metadatas, raw_scores)):
        ranked_items.append(
            {
                "text": document,
                "source": metadata.get("source", "Unknown"),
                "heading": metadata.get("heading", ""),
                "doc_id": metadata.get("doc_id", ""),
                "page_index": metadata.get("page_index"),
                "chunk_index": metadata.get("chunk_index", index),
                "source_type": metadata.get("source_type", "uploaded"),
                "source_url": metadata.get("source_url", ""),
                "page_title": metadata.get("page_title", ""),
                "bm25_score": raw_score / max_score,
                "retrieval_method": "bm25",
            }
        )

    ranked_items.sort(key=lambda item: item["bm25_score"], reverse=True)
    return ranked_items[:bm25_limit]


def _merge_candidates(candidates: list[dict]) -> list[dict]:
    merged: dict[tuple[str, str, int | str], dict] = {}

    for candidate in candidates:
        doc_id = str(candidate.get("doc_id") or candidate.get("source") or "")
        chunk_index = candidate.get("chunk_index", 0)
        page_index = candidate.get("page_index")
        key = (doc_id, str(page_index) if page_index is not None else f"chunk:{chunk_index}", chunk_index)

        current = merged.get(key)
        if current is None:
            current = {
                **candidate,
                "dense_score": float(candidate.get("dense_score", 0.0) or 0.0),
                "bm25_score": float(candidate.get("bm25_score", 0.0) or 0.0),
            }
            merged[key] = current
        else:
            current["dense_score"] = max(current.get("dense_score", 0.0), float(candidate.get("dense_score", 0.0) or 0.0))
            current["bm25_score"] = max(current.get("bm25_score", 0.0), float(candidate.get("bm25_score", 0.0) or 0.0))
            existing_score = (HYBRID_DENSE_WEIGHT * float(current.get("dense_score", 0.0))) + ((1 - HYBRID_DENSE_WEIGHT) * float(current.get("bm25_score", 0.0)))
            candidate_score = (HYBRID_DENSE_WEIGHT * float(candidate.get("dense_score", 0.0) or 0.0)) + ((1 - HYBRID_DENSE_WEIGHT) * float(candidate.get("bm25_score", 0.0) or 0.0))
            if candidate_score >= existing_score:
                current.update(candidate)
                current["dense_score"] = max(current.get("dense_score", 0.0), float(candidate.get("dense_score", 0.0) or 0.0))
                current["bm25_score"] = max(current.get("bm25_score", 0.0), float(candidate.get("bm25_score", 0.0) or 0.0))

        current = merged[key]
        current["score"] = round(
            (HYBRID_DENSE_WEIGHT * float(current.get("dense_score", 0.0)))
            + ((1 - HYBRID_DENSE_WEIGHT) * float(current.get("bm25_score", 0.0))),
            4,
        )
        current["retrieval_method"] = "hybrid" if float(current.get("bm25_score", 0.0)) > 0 else current.get("retrieval_method", "dense")

    return list(merged.values())


def _rank_by_page(candidates: list[dict], top_k: int) -> list[dict]:
    if not candidates:
        return []

    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for candidate in candidates:
        groups[_group_key(candidate, str(candidate.get("chunk_index", 0)))].append(candidate)

    ranked_groups: list[dict] = []
    for group_key, group_items in groups.items():
        ordered_items = sorted(group_items, key=lambda item: item.get("score", 0.0), reverse=True)
        top_scores = [float(item.get("score", 0.0)) for item in ordered_items[:3]]
        best_score = top_scores[0] if top_scores else 0.0
        average_score = sum(top_scores) / len(top_scores) if top_scores else 0.0
        coverage_bonus = min(len(group_items), 4) / 4.0
        page_score = round((0.6 * best_score) + (0.3 * average_score) + (0.1 * coverage_bonus), 4)
        ranked_groups.append(
            {
                "group_key": group_key,
                "page_score": page_score,
                "items": ordered_items,
            }
        )

    ranked_groups.sort(key=lambda group: group["page_score"], reverse=True)

    final_candidates: list[dict] = []
    seen_keys: set[tuple[str, str, int | str]] = set()

    def _candidate_key(candidate: dict) -> tuple[str, str, int | str]:
        doc_id = str(candidate.get("doc_id") or candidate.get("source") or "")
        chunk_index = candidate.get("chunk_index", 0)
        page_index = candidate.get("page_index")
        return doc_id, str(page_index) if page_index is not None else f"chunk:{chunk_index}", chunk_index

    for pass_index in range(2):
        for group in ranked_groups:
            for candidate in group["items"]:
                key = _candidate_key(candidate)
                if key in seen_keys:
                    continue
                final_candidates.append(candidate)
                seen_keys.add(key)
                if len(final_candidates) >= top_k:
                    return final_candidates[:top_k]
                if pass_index == 0:
                    break

    return final_candidates[:top_k]


def retrieve_context(
    query: str,
    top_k: int = TOP_K_RESULTS,
    source_type: str | None = None,
    trace=None,
    obs_trace=None,
    **_kwargs,
) -> list[dict]:
    """
    Retrieve the most relevant document chunks for a given query.

    Args:
        query: The user's question
        top_k: Number of results to return
        source_type: Optional source filter (uploaded or official_site)

    Returns:
        List of dicts with keys: text, source, heading, score, doc_id, page_index
    """
    collection = get_collection()

    if collection.count() == 0:
        return []

    query_text = _normalize_query_text(query)
    query_tokens = _tokenize(query_text)
    list_style_query = _is_list_style_query(query_text, query_tokens)
    query_embedding = generate_embeddings([query_text or query])[0]

    dense_multiplier = 8 if list_style_query else 6
    bm25_multiplier = 10 if list_style_query else 6
    dense_limit = min(max(top_k * dense_multiplier, HYBRID_DENSE_CANDIDATES), collection.count())
    bm25_limit = min(max(top_k * bm25_multiplier, HYBRID_BM25_CANDIDATES), collection.count())

    dense_candidates = _dense_candidates(collection, query_embedding, source_type, dense_limit)
    if RETRIEVAL_MODE == "dense":
        ranked_candidates = dense_candidates
    else:
        bm25_candidates = _bm25_candidates(collection, source_type, bm25_limit, query_tokens)
        ranked_candidates = _merge_candidates(dense_candidates + bm25_candidates)

    if list_style_query:
        for candidate in ranked_candidates:
            page_boost = 0.0
            if candidate.get("page_index") is not None:
                page_boost += 0.05
            if candidate.get("bm25_score", 0.0) > 0:
                page_boost += 0.05
            if candidate.get("heading"):
                page_boost += 0.03
            candidate["score"] = round(min(1.0, float(candidate.get("score", 0.0)) + page_boost), 4)

    ranked_candidates = _rank_by_page(ranked_candidates, top_k)

    context_chunks: list[dict] = []
    for candidate in ranked_candidates:
        page_index = candidate.get("page_index")
        page_label = ""
        if page_index is not None:
            page_label = f"Page {page_index}"
        elif candidate.get("page_title"):
            page_label = str(candidate.get("page_title"))

        context_chunks.append(
            {
                "text": candidate.get("text", ""),
                "source": candidate.get("source", "Unknown"),
                "heading": candidate.get("heading", "") or page_label,
                "score": round(float(candidate.get("score", 0.0) or 0.0), 4),
                "doc_id": candidate.get("doc_id", ""),
                "page_index": page_index,
                "source_type": candidate.get("source_type", "uploaded"),
                "source_url": candidate.get("source_url", ""),
                "retrieval_method": candidate.get("retrieval_method", "dense"),
            }
        )

    return context_chunks


def format_context_for_llm(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a context string for the LLM prompt.
    """
    if not chunks:
        return "No relevant documents found in the knowledge base."

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source_info = f"[Source: {chunk['source']}"
        if chunk.get("heading"):
            source_info += f" > {chunk['heading']}"
        if chunk.get("page_index") is not None:
            source_info += f" | Page {chunk['page_index']}"
        source_info += f" | Relevance: {chunk['score']:.0%}]"

        context_parts.append(f"--- Context {i} {source_info} ---\n{chunk['text']}")

    return "\n\n".join(context_parts)


def get_source_citations(chunks: list[dict]) -> str:
    """Format source citations for display."""
    if not chunks:
        return ""

    seen = set()
    citations = []
    for chunk in chunks:
        source = chunk.get("source", "Unknown")
        page_index = chunk.get("page_index")
        citation_key = (source, page_index if page_index is not None else chunk.get("heading", ""))
        if citation_key not in seen:
            seen.add(citation_key)
            heading = chunk.get("heading", "")
            score = chunk.get("score", 0)
            citation = f"📄 **{source}**"
            if heading:
                citation += f" — {heading}"
            if page_index is not None:
                citation += f" (Page {page_index})"
            citation += f" ({score:.0%} match)"
            citations.append(citation)

    return "\n".join(citations)
