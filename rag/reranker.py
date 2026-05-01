"""
IMS AstroBot — Reranker Module
Uses FlashRank for ultra-fast, zero-API CPU reranking.
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Lazy initialization
_ranker = None

def _get_ranker():
    global _ranker
    if _ranker is None:
        try:
            from flashrank import Ranker
            logger.info("Initializing FlashRank model...")
            # We use the default ms-marco-MiniLM-L-12-v2 ONNX model (very fast)
            _ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2")
        except ImportError:
            logger.error("FlashRank not installed. Run: pip install flashrank")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize FlashRank: {e}")
            return None
    return _ranker

def rerank_candidates(query: str, candidates: List[Dict], top_k: int) -> List[Dict]:
    """
    Rerank a pool of candidates using FlashRank.
    If the ranker fails or isn't installed, returns the original list truncated to top_k.
    """
    if not candidates:
        return []
        
    ranker = _get_ranker()
    if ranker is None:
        return candidates[:top_k]
        
    try:
        # FlashRank expects a list of dicts with 'id' and 'text' keys
        passages = []
        for c in candidates:
            doc_id = str(c.get("doc_id", ""))
            chunk_idx = str(c.get("chunk_index", 0))
            passages.append({
                "id": f"{doc_id}_{chunk_idx}",
                "text": c.get("text", "")
            })
            
        # Execute reranking
        from flashrank import RerankRequest
        rerankrequest = RerankRequest(query=query, passages=passages)
        results = ranker.rerank(rerankrequest)
        
        # Map back to original candidate objects using 'id'
        candidate_map = {f"{c.get('doc_id', '')}_{c.get('chunk_index', 0)}": c for c in candidates}
        
        reranked_candidates = []
        for res in results[:top_k]:
            original = candidate_map.get(res["id"])
            if original:
                # Add reranking score metadata
                original["rerank_score"] = round(res.get("score", 0.0), 4)
                
                # Append rerank to retrieval method list
                method = str(original.get("retrieval_method", "dense"))
                if "rerank" not in method:
                    original["retrieval_method"] = f"{method}+rerank"
                    
                reranked_candidates.append(original)
                
        return reranked_candidates
        
    except Exception as e:
        logger.error(f"Reranking failed: {e}")
        return candidates[:top_k]
