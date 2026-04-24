"""
IMS AstroBot — Conversation Memory (Semantic Cache)
Manages semantic caching of Q&A pairs to avoid redundant LLM calls.
Uses ChromaDB to store and retrieve similar queries with cosine similarity search.
"""

import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional

from ingestion.embedder import generate_embeddings, get_chroma_client
from tests.config import (
    CONV_ENABLED, CONV_MATCH_THRESHOLD, CONV_PERSIST_COLLECTION,
    CONV_PER_USER, CONV_TTL_DAYS, CONV_MIN_USAGE_FOR_KEEP, EMBEDDING_MODEL
)

logger = logging.getLogger(__name__)


def get_memory_collection():
    """Get or create the conversation memory ChromaDB collection."""
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=CONV_PERSIST_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def query_memory(query: str, user_id: Optional[str] = None) -> Optional[dict]:
    """
    Search for a cached response matching the query.
    
    Args:
        query: User question text
        user_id: Optional user ID for per-user memory (if CONV_PER_USER=true)
    
    Returns:
        Dict with cached response or None if no good match found
    """
    if not CONV_ENABLED:
        return None
    
    try:
        collection = get_memory_collection()
        
        # Debug: Check collection size
        total_count = collection.count()
        logger.debug(f"Collection size: {total_count} entries")

        # Embed query
        query_embedding = generate_embeddings([query])[0]
        logger.debug(f"Querying for: '{query[:60]}...'")

        # Search with filter if per-user memory enabled
        where_filter = None
        if CONV_PER_USER and user_id:
            where_filter = {"user_id": user_id}
            logger.debug(f"Using per-user filter: {user_id}")
        elif CONV_PER_USER:
            where_filter = {"user_id": {"$exists": False}}
            logger.debug(f"Using global-only filter")
        else:
            logger.debug(f"No filter (global memory mode)")

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=1,
            where=where_filter,
        )

        logger.debug(f"Query results: {len(results.get('ids', [[]])[0])} matches found")

        if results and results["ids"] and len(results["ids"]) > 0:
            # Get similarity score (distance converted to similarity)
            distance = results["distances"][0][0] if results["distances"] else 2.0
            similarity = 1 - (distance / 2)

            logger.debug(f"Match found! Distance: {distance:.4f}, Similarity: {similarity:.4f}, Threshold: {CONV_MATCH_THRESHOLD}")

            if similarity >= CONV_MATCH_THRESHOLD:
                # Good match found
                metadata = results["metadatas"][0][0] if results["metadatas"] else {}
                memory_id = results["ids"][0][0]

                logger.info(f"✅ CACHE HIT! Returning cached response (ID: {memory_id})")

                # Update usage in database
                from database.db import update_memory_usage
                update_memory_usage(memory_id, similarity)

                return {
                    "memory_id": memory_id,
                    "response": metadata.get("response_text"),
                    "sources": json.loads(metadata.get("sources_json", "[]")),
                    "similarity": round(similarity, 3),
                    "created_at": metadata.get("created_at"),
                    "usage_count": metadata.get("usage_count", 1)
                }
            else:
                logger.debug(f"❌ Similarity too low ({similarity:.4f} < {CONV_MATCH_THRESHOLD})")
        else:
            logger.debug(f"❌ No matches found in collection")
        
        return None
    
    except Exception as e:
        logger.error(f"Error querying memory: {e}", exc_info=True)
        return None


def add_memory_entry(
    query: str,
    response: str,
    sources: list,
    user_id: Optional[str] = None
) -> dict:
    """
    Store a new Q&A pair in memory.
    
    Args:
        query: User question
        response: Generated answer
        sources: List of source documents used
        user_id: Optional user ID for per-user memory
    
    Returns:
        Dict with memory ID or False if failed
    """
    if not CONV_ENABLED:
        logger.debug("Memory disabled, skipping storage")
        return False

    try:
        collection = get_memory_collection()
        memory_id = str(uuid.uuid4())

        # Embed query
        query_embedding = generate_embeddings([query])[0]

        logger.debug(f"💾 Storing query: '{query[:60]}...' (user_id: {user_id or 'global'})")

        # Prepare metadata
        metadata = {
            "query_text": query[:500],  # Truncate for storage
            "response_text": response[:1000],  # Truncate for storage
            "sources_json": json.dumps(sources),
            "user_id": user_id if user_id else "global",
            "created_at": datetime.now().isoformat(),
            "last_used_at": datetime.now().isoformat(),
            "usage_count": 1,
            "embedding_model": EMBEDDING_MODEL,
        }

        # Store in ChromaDB
        collection.add(
            ids=[memory_id],
            embeddings=[query_embedding],
            documents=[query],
            metadatas=[metadata],
        )

        logger.debug(f"✅ Stored in ChromaDB (ID: {memory_id})")

        # Also store in SQLite for admin access and cleanup
        from database.db import store_memory
        store_memory(
            memory_id=memory_id,
            query_text=query,
            response_text=response[:500],
            sources=json.dumps(sources),
            user_id=user_id,
            expires_at=(datetime.now() + timedelta(days=CONV_TTL_DAYS)).isoformat()
        )

        logger.info(f"✅ Stored in SQLite (ID: {memory_id})")

        return {"id": memory_id}

    except Exception as e:
        logger.error(f"Error adding memory entry: {e}", exc_info=True)
        return False


def delete_memory_entry(memory_id: str) -> bool:
    """Delete a specific memory entry from both ChromaDB and database."""
    try:
        collection = get_memory_collection()
        collection.delete(ids=[memory_id])

        from database.db import delete_memory
        delete_memory(memory_id)

        logger.info(f"Deleted memory entry: {memory_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting memory entry: {e}", exc_info=True)
        return False


def invalidate_memory_by_source(source_doc_id: str) -> int:
    """
    Invalidate (delete) all memory entries that reference a specific document.
    Called when a document is re-uploaded/reprocessed.

    Args:
        source_doc_id: Document ID from database

    Returns:
        Number of entries invalidated
    """
    if not CONV_ENABLED:
        return 0

    try:
        from database.db import invalidate_memory_by_source as db_invalidate
        deleted_count = db_invalidate(source_doc_id)
        logger.debug(f"Invalidated {deleted_count} memory entries for source: {source_doc_id}")
        return deleted_count

    except Exception as e:
        logger.error(f"Error invalidating memory by source: {e}", exc_info=True)
        return 0


def cleanup_old_memory() -> int:
    """
    Clean up old memory entries based on TTL and usage count.
    Should be called periodically (e.g., daily).

    Returns:
        Number of entries cleaned up
    """
    if not CONV_ENABLED:
        return 0

    try:
        from database.db import cleanup_expired_memory
        deleted_count = cleanup_expired_memory()
        logger.info(f"Cleaned up {deleted_count} expired memory entries")

        return deleted_count

    except Exception as e:
        logger.error(f"Error cleaning up memory: {e}", exc_info=True)
        return 0


def get_memory_stats() -> dict:
    """Get memory usage statistics."""
    try:
        from database.db import get_memory_stats
        db_stats = get_memory_stats()

        return {
            "total_entries": db_stats.get("total_entries", 0),
            "avg_usage": db_stats.get("avg_usage_per_entry", 0),
            "by_user": db_stats.get("by_user", []),
            "status": "ok"
        }
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}", exc_info=True)
        return {"total_entries": 0, "avg_usage": 0, "by_user": [], "status": "error", "error": str(e)}


def clear_all_memory() -> bool:
    """Clear all conversation memory (admin action)."""
    try:
        from ingestion.embedder import get_chroma_client
        client = get_chroma_client()
        client.delete_collection(name=CONV_PERSIST_COLLECTION)

        from database.db import clear_all_memory as db_clear_all
        db_clear_all()

        # Recreate collection
        get_memory_collection()

        logger.warning("All conversation memory cleared")
        return True
    except Exception as e:
        logger.error(f"Error clearing memory: {e}", exc_info=True)
        return False
