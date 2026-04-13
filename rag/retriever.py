"""
IMS AstroBot — RAG Retriever
Performs semantic search against ChromaDB to find relevant document chunks.
"""

import math
import re
import threading
import time
from collections import Counter
from ingestion.embedder import get_collection, generate_embeddings
from rag.providers.manager import get_manager
from config import (
    TOP_K_RESULTS,
    EMBEDDING_MODEL,
    RETRIEVAL_MODE,
    HYBRID_DENSE_WEIGHT,
    HYBRID_BM25_CANDIDATES,
    HYBRID_DENSE_CANDIDATES,
    HYDE_ENABLED,
    HYDE_TRIGGER_SCORE,
    HYDE_SCORE_BLEND,
    HYDE_MAX_TOKENS,
    HYDE_MAX_CHARS,
    HYDE_TEMPERATURE,
)


_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
_BM25_LOCK = threading.Lock()
_BM25_CACHE = {
    "count": -1,
    "ids": [],
    "documents": [],
    "metadatas": [],
    "tf": [],
    "doc_len": [],
    "avgdl": 0.0,
    "idf": {},
}

_HYDE_SYSTEM_PROMPT = (
    "You are a retrieval helper. "
    "Write a concise hypothetical passage that is likely to appear in institutional documents and that "
    "would help a vector retriever find relevant chunks for the user question. "
    "Do not add disclaimers."
)


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


def _normalize_bm25(score: float, max_score: float) -> float:
    if max_score <= 0:
        return 0.0
    return min(max(score / max_score, 0.0), 1.0)


def _build_bm25_cache(collection):
    count = collection.count()
    with _BM25_LOCK:
        if _BM25_CACHE["count"] == count and _BM25_CACHE["ids"]:
            return _BM25_CACHE

        if count == 0:
            _BM25_CACHE.update({
                "count": 0,
                "ids": [],
                "documents": [],
                "metadatas": [],
                "tf": [],
                "doc_len": [],
                "avgdl": 0.0,
                "idf": {},
            })
            return _BM25_CACHE

        all_rows = collection.get(include=["documents", "metadatas"])
        ids = all_rows.get("ids", []) or []
        documents = all_rows.get("documents", []) or []
        metadatas = all_rows.get("metadatas", []) or []

        tf_list = []
        doc_len = []
        df = Counter()

        for doc in documents:
            tokens = _tokenize(doc)
            tf = Counter(tokens)
            tf_list.append(tf)
            doc_len.append(len(tokens))
            for term in tf.keys():
                df[term] += 1

        n_docs = len(documents)
        avgdl = (sum(doc_len) / n_docs) if n_docs else 0.0
        idf = {
            term: math.log(1 + ((n_docs - freq + 0.5) / (freq + 0.5)))
            for term, freq in df.items()
        }

        _BM25_CACHE.update({
            "count": count,
            "ids": ids,
            "documents": documents,
            "metadatas": metadatas,
            "tf": tf_list,
            "doc_len": doc_len,
            "avgdl": avgdl,
            "idf": idf,
        })
        return _BM25_CACHE


def _bm25_rank(query: str, top_k: int, k1: float = 1.5, b: float = 0.75) -> list[tuple[int, float]]:
    cache = _BM25_CACHE
    if not cache["documents"]:
        return []

    q_terms = _tokenize(query)
    if not q_terms:
        return []

    scored = []
    avgdl = cache["avgdl"] or 1.0
    for idx, tf in enumerate(cache["tf"]):
        dl = cache["doc_len"][idx]
        score = 0.0
        for term in q_terms:
            freq = tf.get(term, 0)
            if freq <= 0:
                continue
            term_idf = cache["idf"].get(term, 0.0)
            denom = freq + k1 * (1 - b + b * (dl / avgdl))
            score += term_idf * ((freq * (k1 + 1)) / denom)
        if score > 0:
            scored.append((idx, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def _chunk_key(chunk: dict) -> str:
    chunk_id = chunk.get("chunk_id") or ""
    if chunk_id:
        return chunk_id
    return f"{chunk.get('doc_id','')}::{chunk.get('source','')}::{chunk.get('heading','')}::{hash(chunk.get('text',''))}"


def _generate_hyde_text(query: str) -> str:
    if not query.strip():
        return ""

    mgr = get_manager()
    hyde_user_prompt = (
        f"Question: {query.strip()}\n\n"
        "Write 4-6 factual sentences that could answer this question using likely institutional terms, "
        "entities, and policy wording."
    )
    generated = mgr.generate(
        system_prompt=_HYDE_SYSTEM_PROMPT,
        user_message=hyde_user_prompt,
        temperature=HYDE_TEMPERATURE,
        max_tokens=HYDE_MAX_TOKENS,
        trace=None,
    )
    if not generated:
        return ""

    compact = " ".join(generated.strip().split())
    if HYDE_MAX_CHARS > 0:
        compact = compact[:HYDE_MAX_CHARS]
    return compact


def _merge_hyde_chunks(base_chunks: list[dict], hyde_chunks: list[dict], top_k: int) -> list[dict]:
    blend = min(max(HYDE_SCORE_BLEND, 0.0), 1.0)
    merged: dict[str, dict] = {}

    for chunk in base_chunks:
        item = chunk.copy()
        item["base_score"] = chunk.get("score", 0.0)
        item["hyde_score"] = 0.0
        merged[_chunk_key(item)] = item

    for chunk in hyde_chunks:
        key = _chunk_key(chunk)
        if key not in merged:
            item = chunk.copy()
            item["base_score"] = 0.0
            item["hyde_score"] = chunk.get("score", 0.0)
            item["retrieval_method"] = "hyde"
            merged[key] = item
            continue

        existing = merged[key]
        existing["hyde_score"] = max(existing.get("hyde_score", 0.0), chunk.get("score", 0.0))
        if existing.get("distance") is None and chunk.get("distance") is not None:
            existing["distance"] = chunk.get("distance")

        existing_method = str(existing.get("retrieval_method", "dense"))
        if "hyde" not in existing_method:
            existing["retrieval_method"] = f"{existing_method}+hyde"

    reranked = []
    for item in merged.values():
        base_score = item.get("base_score", item.get("score", 0.0))
        hyde_score = item.get("hyde_score", 0.0)
        if hyde_score > 0:
            blended = (1.0 - blend) * base_score + blend * hyde_score
            final_score = max(base_score, blended)
        else:
            final_score = base_score

        item["score"] = round(final_score, 4)
        item.pop("base_score", None)
        reranked.append(item)

    reranked.sort(key=lambda c: c.get("score", 0.0), reverse=True)
    return reranked[:top_k]


def _dense_retrieve(collection, query_embedding, n_results: int) -> tuple[list[dict], float]:
    search_start = time.time()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    search_ms = (time.time() - search_start) * 1000

    chunks = []
    if results and results.get("documents") and results["documents"][0]:
        ids = results.get("ids", [[]])
        for i, doc in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
            distance = results["distances"][0][i] if results.get("distances") else 0.0
            similarity = 1 - (distance / 2)

            chunk_id = ""
            if ids and len(ids) > 0 and i < len(ids[0]):
                chunk_id = ids[0][i] or ""

            chunks.append({
                "chunk_id": chunk_id,
                "text": doc,
                "source": metadata.get("source", "Unknown"),
                "heading": metadata.get("heading", ""),
                "doc_id": metadata.get("doc_id", ""),
                "distance": distance,
                "dense_score": round(similarity, 6),
                "bm25_score": 0.0,
                "score": round(similarity, 4),
                "retrieval_method": "dense",
            })
    return chunks, search_ms


def retrieve_context(
    query: str,
    top_k: int = TOP_K_RESULTS,
    trace=None,
    obs_trace=None,
    _allow_hyde: bool = True,
) -> list[dict]:
    """
    Retrieve the most relevant document chunks for a given query.
    
    Args:
        query: The user's question
        top_k: Number of results to return
        trace: Optional PipelineTrace instance for terminal explainability
    
    Returns:
        List of dicts with keys: text, source, heading, score
    """
    collection = get_collection()

    if collection.count() == 0:
        if obs_trace:
            obs_trace.update(metadata={"retrieval_empty_collection": True})
        return []

    retrieval_span = obs_trace.start_span(
        name="retrieval",
        input_payload={"query_preview": query[:160], "top_k": top_k},
        metadata={"embedding_model": EMBEDDING_MODEL},
    ) if obs_trace else None

    # Generate query embedding
    embed_start = time.time()
    query_embedding = generate_embeddings([query])[0]
    embed_ms = (time.time() - embed_start) * 1000

    embed_span = obs_trace.start_span(
        name="embedding.query",
        input_payload={"query_length": len(query)},
        metadata={"embedding_model": EMBEDDING_MODEL},
    ) if obs_trace else None
    if embed_span:
        embed_span.end(
            metadata={
                "embedding_dims": len(query_embedding),
                "elapsed_ms": round(embed_ms, 2),
            }
        )

    # Record embedding step in trace
    if trace:
        trace.record_embedding(
            model=EMBEDDING_MODEL,
            dims=len(query_embedding),
            preview=query_embedding[:5],
            time_ms=embed_ms,
        )

    # Search ChromaDB (dense retrieval)
    collection_size = collection.count()
    dense_n = min(max(top_k, HYBRID_DENSE_CANDIDATES), collection_size)
    dense_chunks, search_ms = _dense_retrieve(collection, query_embedding, dense_n)

    search_span = obs_trace.start_span(
        name="vector_search.chromadb",
        input_payload={"top_k": top_k},
        metadata={"collection_size": collection_size},
    ) if obs_trace else None
    if search_span:
        search_span.end(metadata={"elapsed_ms": round(search_ms, 2)})

    # Record search step in trace
    if trace:
        trace.record_search(
            collection_size=collection_size,
            top_k=top_k,
            time_ms=search_ms,
        )

    context_chunks = []
    mode = (RETRIEVAL_MODE or "dense").lower().strip()
    if mode == "hybrid" and collection_size > 0:
        bm25_span = obs_trace.start_span(
            name="keyword_search.bm25",
            input_payload={"query_preview": query[:160], "top_k": top_k},
            metadata={"collection_size": collection_size},
        ) if obs_trace else None

        bm_start = time.time()
        cache = _build_bm25_cache(collection)
        bm_ranked = _bm25_rank(query, top_k=min(max(top_k, HYBRID_BM25_CANDIDATES), len(cache["documents"])))
        bm_ms = (time.time() - bm_start) * 1000
        if bm25_span:
            bm25_span.end(metadata={"elapsed_ms": round(bm_ms, 2), "hits": len(bm_ranked)})

        bm25_chunks = []
        max_bm = bm_ranked[0][1] if bm_ranked else 0.0
        for idx, raw_score in bm_ranked:
            metadata = cache["metadatas"][idx] if idx < len(cache["metadatas"]) else {}
            norm_bm = _normalize_bm25(raw_score, max_bm)
            bm25_chunks.append({
                "chunk_id": cache["ids"][idx] if idx < len(cache["ids"]) else "",
                "text": cache["documents"][idx],
                "source": metadata.get("source", "Unknown"),
                "heading": metadata.get("heading", ""),
                "doc_id": metadata.get("doc_id", ""),
                "distance": None,
                "dense_score": 0.0,
                "bm25_score": round(norm_bm, 6),
                "score": round(norm_bm, 4),
                "retrieval_method": "bm25",
            })

        dense_weight = min(max(HYBRID_DENSE_WEIGHT, 0.0), 1.0)
        merged = {}
        for chunk in dense_chunks + bm25_chunks:
            key = _chunk_key(chunk)
            if key not in merged:
                merged[key] = chunk.copy()
                continue

            existing = merged[key]
            existing["dense_score"] = max(existing.get("dense_score", 0.0), chunk.get("dense_score", 0.0))
            existing["bm25_score"] = max(existing.get("bm25_score", 0.0), chunk.get("bm25_score", 0.0))
            if not existing.get("distance") and chunk.get("distance") is not None:
                existing["distance"] = chunk.get("distance")
            if existing.get("retrieval_method") != chunk.get("retrieval_method"):
                existing["retrieval_method"] = "hybrid"

        merged_chunks = []
        for merged_chunk in merged.values():
            d_score = merged_chunk.get("dense_score", 0.0)
            b_score = merged_chunk.get("bm25_score", 0.0)
            final_score = dense_weight * d_score + (1.0 - dense_weight) * b_score
            merged_chunk["score"] = round(final_score, 4)
            merged_chunks.append(merged_chunk)

        merged_chunks.sort(key=lambda c: c.get("score", 0.0), reverse=True)
        context_chunks = merged_chunks[:top_k]
    else:
        context_chunks = dense_chunks[:top_k]

    hyde_applied = False
    if _allow_hyde and HYDE_ENABLED and context_chunks and query.strip():
        top_score = context_chunks[0].get("score", 0.0)
        if top_score < HYDE_TRIGGER_SCORE:
            hyde_gen_span = obs_trace.start_span(
                name="retrieval.hyde.generate",
                input_payload={"query_preview": query[:160]},
                metadata={"top_score": round(top_score, 4), "threshold": HYDE_TRIGGER_SCORE},
            ) if obs_trace else None

            hyde_text = _generate_hyde_text(query)
            if hyde_gen_span:
                hyde_gen_span.end(
                    metadata={
                        "generated": bool(hyde_text),
                        "hyde_chars": len(hyde_text or ""),
                    }
                )

            if hyde_text:
                hyde_search_span = obs_trace.start_span(
                    name="retrieval.hyde.search",
                    input_payload={"hyde_preview": hyde_text[:160]},
                    metadata={"top_k": top_k},
                ) if obs_trace else None

                hyde_top_k = min(max(top_k, HYBRID_DENSE_CANDIDATES), collection_size)
                hyde_chunks = retrieve_context(
                    hyde_text,
                    top_k=hyde_top_k,
                    trace=None,
                    obs_trace=None,
                    _allow_hyde=False,
                )

                if hyde_search_span:
                    hyde_search_span.end(metadata={"hits": len(hyde_chunks)})

                if hyde_chunks:
                    context_chunks = _merge_hyde_chunks(context_chunks, hyde_chunks, top_k)
                    hyde_applied = True

    # Record chunks in terminal trace (final list after rerank/fusion)
    if trace:
        for i, chunk in enumerate(context_chunks):
            trace.record_chunk(
                rank=i + 1,
                source=chunk.get("source", "Unknown"),
                heading=chunk.get("heading", ""),
                similarity=chunk.get("score", 0.0),
                text=chunk.get("text", ""),
                distance=chunk.get("distance"),
            )

    if retrieval_span:
        max_score = max((c.get("score", 0.0) for c in context_chunks), default=0.0)
        retrieval_span.end(
            metadata={
                "chunks_returned": len(context_chunks),
                "top_score": round(max_score, 4),
                "collection_size": collection_size,
                "retrieval_mode": mode,
                "hyde_applied": hyde_applied,
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
        if source not in seen:
            seen.add(source)
            heading = chunk.get("heading", "")
            score = chunk.get("score", 0)
            citation = f"📄 **{source}**"
            if heading:
                citation += f" — {heading}"
            citation += f" ({score:.0%} match)"
            citations.append(citation)

    return "\n".join(citations)
