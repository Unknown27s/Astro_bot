"""
IMS AstroBot — Embedding & ChromaDB Storage
Generates embeddings using sentence-transformers and stores in ChromaDB.
"""

import threading
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from config import CHROMA_PERSIST_DIR, EMBEDDING_MODEL

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
        print(f"[Embedder] Loading embedding model: {EMBEDDING_MODEL}...")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        print("[Embedder] Embedding model loaded.")
        return _embedding_model


def get_chroma_client() -> chromadb.ClientAPI:
    """Get persistent ChromaDB client. Thread-safe singleton."""
    global _chroma_client
    if _chroma_client is not None:
        return _chroma_client
    with _chroma_lock:
        if _chroma_client is not None:
            return _chroma_client
        print("[Embedder] Initializing ChromaDB client...")
        _chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_PERSIST_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        print("[Embedder] ChromaDB client ready.")
        return _chroma_client


def get_collection():
    """Get or create the main document collection."""
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name="ims_documents",
        metadata={"hnsw:space": "cosine"},
    )
    return collection


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
        meta = c.get("metadata", {})
        meta["doc_id"] = doc_id
        metadatas.append(meta)

    # ChromaDB add in batches (max 5461 per batch)
    batch_size = 5000
    for i in range(0, len(ids), batch_size):
        collection.add(
            ids=ids[i : i + batch_size],
            embeddings=embeddings[i : i + batch_size],
            documents=texts[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
        )

    return len(chunks)


def delete_doc_chunks(doc_id: str):
    """Delete all chunks belonging to a specific document."""
    collection = get_collection()
    # Query for chunk IDs belonging to this document
    try:
        results = collection.get(where={"doc_id": doc_id})
        if results and results["ids"]:
            collection.delete(ids=results["ids"])
    except Exception as e:
        print(f"[Embedder] Error deleting chunks for doc {doc_id}: {e}")


def get_collection_stats() -> dict:
    """Get stats about the ChromaDB collection."""
    collection = get_collection()
    count = collection.count()
    return {"total_chunks": count}
