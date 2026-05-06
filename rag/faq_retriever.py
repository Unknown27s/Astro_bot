"""
IMS AstroBot — FAQ Retriever
Stores and retrieves structured FAQ entries for question-to-question matching.
"""

from __future__ import annotations

import uuid

from ingestion.embedder import generate_embeddings, get_chroma_client
from config import FAQ_COLLECTION, FAQ_MIN_SCORE, FAQ_TOP_K


def get_faq_collection():
    """Get or create the FAQ collection."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=FAQ_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


def get_faq_stats() -> dict:
    """Get FAQ index statistics."""
    collection = get_faq_collection()
    return {"total_entries": collection.count()}


def clear_faq_entries() -> int:
    """Delete all FAQ entries and recreate the FAQ collection."""
    client = get_chroma_client()
    current = get_faq_collection()
    current_count = current.count()
    try:
        client.delete_collection(name=FAQ_COLLECTION)
    except Exception:
        pass
    client.get_or_create_collection(
        name=FAQ_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )
    return current_count


def store_faq_entries(entries: list[dict], source: str = "manual_faq") -> int:
    """
    Store structured FAQ entries.

    Each entry supports:
    {
      "question": str,
      "answer": str,
      "metadata": {"category": "...", ...}
    }
    """
    if not entries:
        return 0

    questions: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    for entry in entries:
        question = (entry.get("question") or "").strip()
        answer = (entry.get("answer") or "").strip()
        if not question or not answer:
            continue

        metadata = dict(entry.get("metadata") or {})
        metadata["answer"] = answer
        metadata["source"] = metadata.get("source") or source
        metadata["source_type"] = "faq"

        ids.append(str(entry.get("id") or f"faq_{uuid.uuid4()}"))
        questions.append(question)
        metadatas.append({k: v for k, v in metadata.items() if v is not None})

    if not questions:
        return 0

    embeddings = generate_embeddings(questions)
    collection = get_faq_collection()
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=questions,
        metadatas=metadatas,
    )

    return len(questions)


def retrieve_faq_context(query: str, top_k: int | None = None, min_score: float | None = None) -> list[dict]:
    """Retrieve top FAQ entries matching the user question."""
    question = (query or "").strip()
    if not question:
        return []

    collection = get_faq_collection()
    if collection.count() == 0:
        return []

    k = top_k if top_k is not None else FAQ_TOP_K
    threshold = min_score if min_score is not None else FAQ_MIN_SCORE

    query_embedding = generate_embeddings([question])[0]
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(k * 2, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    documents = result.get("documents", [[]])[0] if result else []
    metadatas = result.get("metadatas", [[]])[0] if result else []
    distances = result.get("distances", [[]])[0] if result else []

    chunks: list[dict] = []
    for idx, question_text in enumerate(documents):
        metadata = metadatas[idx] if idx < len(metadatas) else {}
        distance = float(distances[idx]) if idx < len(distances) else 2.0
        score = max(0.0, min(1.0, 1 - (distance / 2)))
        if score < threshold:
            continue

        answer_text = (metadata.get("answer") or "").strip()
        if not answer_text:
            continue

        chunks.append(
            {
                "text": answer_text,
                "source": metadata.get("source", "FAQ"),
                "heading": f"FAQ: {question_text}",
                "score": round(score, 4),
                "doc_id": metadata.get("doc_id", "faq"),
                "page_index": None,
                "source_type": "faq",
                "source_url": metadata.get("source_url", ""),
                "retrieval_method": "faq",
            }
        )

        if len(chunks) >= k:
            break

    return chunks
