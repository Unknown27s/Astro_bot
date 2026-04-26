"""Targeted tests for HyDE trigger and blend behavior in rag.retriever."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag import retriever  # noqa: E402


class _DummyCollection:
    def __init__(self, size: int = 10):
        self._size = size

    def count(self) -> int:
        return self._size


def _candidate(
    *,
    text: str,
    score: float,
    doc_id: str,
    page_index: int,
    chunk_index: int,
    retrieval_method: str = "dense",
) -> dict:
    return {
        "text": text,
        "source": "policy.pdf",
        "heading": "Policy",
        "score": score,
        "doc_id": doc_id,
        "page_index": page_index,
        "chunk_index": chunk_index,
        "source_type": "uploaded",
        "source_url": "",
        "page_title": "",
        "retrieval_method": retrieval_method,
        "dense_score": score,
        "bm25_score": 0.0,
    }


def test_blend_hyde_candidates_merges_overlap_and_scales_new():
    base = [
        _candidate(
            text="Base A",
            score=0.30,
            doc_id="doc-a",
            page_index=1,
            chunk_index=0,
            retrieval_method="dense",
        )
    ]
    hyde = [
        _candidate(
            text="HyDE overlap",
            score=0.90,
            doc_id="doc-a",
            page_index=1,
            chunk_index=0,
            retrieval_method="dense",
        ),
        _candidate(
            text="HyDE new",
            score=0.80,
            doc_id="doc-b",
            page_index=2,
            chunk_index=1,
            retrieval_method="bm25",
        ),
    ]

    merged = retriever._blend_hyde_candidates(base, hyde)

    assert len(merged) == 2

    overlap = next(c for c in merged if c["doc_id"] == "doc-a")
    assert overlap["score"] > 0.30
    assert "hyde" in overlap["retrieval_method"]
    assert overlap["hyde_score"] == 0.9

    new_item = next(c for c in merged if c["doc_id"] == "doc-b")
    assert new_item["score"] == round(0.80 * retriever.HYDE_SCORE_BLEND, 4)
    assert new_item["retrieval_method"].endswith("_hyde")


def test_retrieve_context_triggers_hyde_on_low_confidence(monkeypatch):
    monkeypatch.setattr(retriever, "HYDE_ENABLED", True)
    monkeypatch.setattr(retriever, "HYDE_TRIGGER_SCORE", 0.60)
    monkeypatch.setattr(retriever, "MIN_SCORE_THRESHOLD", 0.0)

    monkeypatch.setattr(retriever, "get_collection", lambda: _DummyCollection(20))
    monkeypatch.setattr(retriever, "_rank_by_page", lambda candidates, top_k: candidates[:top_k])

    base_candidates = [
        _candidate(
            text="Base low",
            score=0.25,
            doc_id="doc-a",
            page_index=1,
            chunk_index=0,
            retrieval_method="dense",
        )
    ]
    hyde_candidates = [
        _candidate(
            text="HyDE improved",
            score=0.92,
            doc_id="doc-a",
            page_index=1,
            chunk_index=0,
            retrieval_method="dense",
        )
    ]

    hyde_text = "hypothetical policy answer"

    def _fake_retrieve(collection, retrieval_text, source_type, doc_id, top_k, list_query):
        if retrieval_text == hyde_text:
            return hyde_candidates
        return base_candidates

    hyde_calls = {"count": 0}

    def _fake_hyde(query):
        hyde_calls["count"] += 1
        return hyde_text

    monkeypatch.setattr(retriever, "_retrieve_candidates_for_text", _fake_retrieve)
    monkeypatch.setattr(retriever, "_generate_hypothetical_passage", _fake_hyde)

    chunks = retriever.retrieve_context("what is attendance policy", top_k=1)

    assert hyde_calls["count"] == 1
    assert len(chunks) == 1
    assert chunks[0]["score"] > 0.25
    assert "hyde" in chunks[0]["retrieval_method"]


def test_retrieve_context_skips_hyde_on_high_confidence(monkeypatch):
    monkeypatch.setattr(retriever, "HYDE_ENABLED", True)
    monkeypatch.setattr(retriever, "HYDE_TRIGGER_SCORE", 0.60)
    monkeypatch.setattr(retriever, "MIN_SCORE_THRESHOLD", 0.0)

    monkeypatch.setattr(retriever, "get_collection", lambda: _DummyCollection(20))
    monkeypatch.setattr(retriever, "_rank_by_page", lambda candidates, top_k: candidates[:top_k])

    base_candidates = [
        _candidate(
            text="Base high",
            score=0.91,
            doc_id="doc-a",
            page_index=1,
            chunk_index=0,
            retrieval_method="dense",
        )
    ]

    monkeypatch.setattr(
        retriever,
        "_retrieve_candidates_for_text",
        lambda collection, retrieval_text, source_type, doc_id, top_k, list_query: base_candidates,
    )

    def _should_not_call(_query):
        raise AssertionError("HyDE generation should not be called for high-confidence results")

    monkeypatch.setattr(retriever, "_generate_hypothetical_passage", _should_not_call)

    chunks = retriever.retrieve_context("what is attendance policy", top_k=1)

    assert len(chunks) == 1
    assert chunks[0]["retrieval_method"] == "dense"
