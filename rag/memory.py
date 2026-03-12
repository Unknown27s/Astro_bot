"""
IMS AstroBot — Conversation Memory (Semantic Cache)
Manages semantic caching of Q&A pairs to avoid redundant LLM calls.
Uses ChromaDB to store and retrieve similar queries with cosine similarity search.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Optional

from ingestion.embedder import generate_embeddings, get_chroma_client
from config import (
    CONV_ENABLED, CONV_MATCH_THRESHOLD, CONV_PERSIST_COLLECTION,
    CONV_PER_USER, CONV_TTL_DAYS, CONV_MIN_USAGE_FOR_KEEP, EMBEDDING_MODEL
)


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
        
        # Embed query
        query_embedding = generate_embeddings([query])[0]
        
        # Search with filter if per-user memory enabled
        where_filter = None
        if CONV_PER_USER and user_id:
            where_filter = {"user_id": user_id}
        elif CONV_PER_USER:
            # If per-user but no user_id provided, don't match anything from other users
            where_filter = {"user_id": {"$exists": False}}
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=1,
            where=where_filter,
        )
        
        if results and results["ids"] and len(results["ids"]) > 0:
            # Get similarity score (distance converted to similarity)
            distance = results["distances"][0][0] if results["distances"] else 2.0
            similarity = 1 - (distance / 2)
            
            if similarity >= CONV_MATCH_THRESHOLD:
                # Good match found
                metadata = results["metadatas"][0][0] if results["metadatas"] else {}
                memory_id = results["ids"][0][0]
                
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
        
        return None
    
    except Exception as e:
        print(f"[Memory] Error querying memory: {e}")
        return None


def add_memory_entry(
    query: str,
    response: str,
    sources: list,
    user_id: Optional[str] = None
) -> bool:
    """
    Store a new Q&A pair in memory.
    
    Args:
        query: User question
        response: Generated answer
        sources: List of source documents used
        user_id: Optional user ID for per-user memory
    
    Returns:
        True if stored successfully
    """
    if not CONV_ENABLED:
        return False
    
    try:
        collection = get_memory_collection()
        memory_id = str(uuid.uuid4())
        
        # Embed query
        query_embedding = generate_embeddings([query])[0]
        
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
        
        # Also store in SQLite for admin access and cleanup
        from database.db import store_memory_in_db
        store_memory_in_db(
            memory_id=memory_id,
            user_id=user_id,
            query_text=query,
            response_preview=response[:500],
            sources_json=json.dumps(sources),
            created_at=metadata["created_at"]
        )
        
        return True
    
    except Exception as e:
        print(f"[Memory] Error adding memory entry: {e}")
        return False


def delete_memory_entry(memory_id: str) -> bool:
    """Delete a specific memory entry from both ChromaDB and database."""
    try:
        collection = get_memory_collection()
        collection.delete(ids=[memory_id])
        
        from database.db import delete_memory_from_db
        delete_memory_from_db(memory_id)
        
        return True
    except Exception as e:
        print(f"[Memory] Error deleting memory entry: {e}")
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
        collection = get_memory_collection()
        
        # Get all entries that reference this document
        from database.db import get_memory_by_source
        entries = get_memory_by_source(source_doc_id)
        
        deleted_count = 0
        for entry in entries:
            try:
                collection.delete(ids=[entry["memory_id"]])
                from database.db import delete_memory_from_db
                delete_memory_from_db(entry["memory_id"])
                deleted_count += 1
            except Exception as e:
                print(f"[Memory] Error deleting entry {entry['memory_id']}: {e}")
        
        return deleted_count
    
    except Exception as e:
        print(f"[Memory] Error invalidating memory by source: {e}")
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
        from database.db import cleanup_memory_entries
        deleted_count = cleanup_memory_entries(
            ttl_days=CONV_TTL_DAYS,
            min_usage=CONV_MIN_USAGE_FOR_KEEP
        )
        
        # Also clean from ChromaDB if using filtering
        collection = get_memory_collection()
        cutoff_date = (datetime.now() - timedelta(days=CONV_TTL_DAYS)).isoformat()
        
        # Get all entries older than cutoff
        from database.db import get_old_memory_entries
        old_entries = get_old_memory_entries(cutoff_date)
        
        for entry in old_entries:
            try:
                collection.delete(ids=[entry["memory_id"]])
            except:
                pass
        
        return deleted_count
    
    except Exception as e:
        print(f"[Memory] Error cleaning up memory: {e}")
        return 0


def get_memory_stats() -> dict:
    """Get memory usage statistics."""
    try:
        collection = get_memory_collection()
        total_entries = collection.count()
        
        from database.db import get_memory_db_stats
        db_stats = get_memory_db_stats()
        
        return {
            "chromadb_entries": total_entries,
            "database_entries": db_stats.get("total", 0),
            "memory_hits": db_stats.get("hits", 0),
            "avg_similarity": db_stats.get("avg_similarity", 0),
            "total_storage_saved_ms": db_stats.get("total_saved_ms", 0),
        }
    except Exception as e:
        print(f"[Memory] Error getting memory stats: {e}")
        return {"error": str(e)}


def clear_all_memory() -> bool:
    """Clear all conversation memory (admin action)."""
    try:
        client = get_chroma_client()
        client.delete_collection(name=CONV_PERSIST_COLLECTION)
        
        from database.db import clear_all_memory_db
        clear_all_memory_db()
        
        # Recreate collection
        get_memory_collection()
        
        return True
    except Exception as e:
        print(f"[Memory] Error clearing memory: {e}")
        return False
