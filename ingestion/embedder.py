"""
IMS AstroBot — Embedding & ChromaDB Storage
Generates embeddings using sentence-transformers and stores in ChromaDB.
"""

import os
import logging
import threading
from typing import Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from config import CHROMA_PERSIST_DIR, EMBEDDING_MODEL

logger = logging.getLogger(__name__)

# Use cached model files without making network requests
os.environ.setdefault("HF_HUB_OFFLINE", "1")

# ── Thread-safe singletons ──
_embedding_model = None
_chroma_client = None
_model_lock = threading.Lock()
_chroma_lock = threading.Lock()


def get_embedding_model() -> SentenceTransformer:
    """Load embedding model. Thread-safe singleton."""
    global _embedding_model
    if _embedding_model is not None:
        return _embedding_model
    with _model_lock:
        if _embedding_model is not None:
            return _embedding_model
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}...")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("Embedding model loaded successfully")
        return _embedding_model


def get_chroma_client() -> Any:
    """Get persistent ChromaDB client. Thread-safe singleton."""
    global _chroma_client
    if _chroma_client is not None:
        return _chroma_client
    with _chroma_lock:
        if _chroma_client is not None:
            return _chroma_client
        logger.info("Initializing ChromaDB client...")
        _chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_PERSIST_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        logger.info("ChromaDB client ready")
        return _chroma_client


def get_collection():
    """Get or create the main document collection."""
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name="ims_documents",
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def _invalidate_retrieval_cache() -> None:
    """Clear retriever-side caches after the collection changes."""
    try:
        from rag.retriever import invalidate_bm25_index

        invalidate_bm25_index()
    except Exception as exc:  # pragma: no cover - best effort only
        logger.debug("Unable to invalidate BM25 cache: %s", exc)


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts."""
    model = get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return embeddings.tolist()


def store_chunks(chunks: list[dict], doc_id: str) -> int:
    """
    Store document chunks in ChromaDB.
    
    Args:
        chunks: List of {"text": str, "metadata": {...}} dicts from chunker
        doc_id: Document ID from the database
    
    Returns:
        Number of chunks stored
    """
    if not chunks:
        return 0

    collection = get_collection()
    texts = [c["text"] for c in chunks]
    embeddings = generate_embeddings(texts)

    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = []
    for c in chunks:
        meta = dict(c.get("metadata", {}))
        meta["doc_id"] = doc_id
        meta.setdefault("source_type", "uploaded")

        # ChromaDB metadata must stay primitive and cannot include null values.
        meta = {key: value for key, value in meta.items() if value is not None}
        metadatas.append(meta)

    # ChromaDB add in batches (max 5461 per batch)
    batch_size = 5000
    for i in range(0, len(ids), batch_size):
        embeddings_batch = embeddings[i : i + batch_size]
        collection.add(
            ids=ids[i : i + batch_size],
            embeddings=embeddings_batch,  # type: ignore[arg-type]
            documents=texts[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
        )

    _invalidate_retrieval_cache()
    return len(chunks)


def delete_doc_chunks(doc_id: str):
    """Delete all chunks belonging to a specific document."""
    collection = get_collection()
    # Query for chunk IDs belonging to this document
    try:
        results = collection.get(where={"doc_id": doc_id})
        if results and results["ids"]:
            collection.delete(ids=results["ids"])
            logger.debug(f"Deleted {len(results['ids'])} chunks for document: {doc_id}")
            _invalidate_retrieval_cache()
    except Exception as e:
        logger.error(f"Error deleting chunks for doc {doc_id}: {e}", exc_info=True)


def get_collection_stats() -> dict:
    """Get stats about the ChromaDB collection."""
    collection = get_collection()
    count = collection.count()
    return {"total_chunks": count}
