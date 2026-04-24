"""
test_faq_retriever.py - FAQ retriever tests
"""

import pytest
from unittest.mock import MagicMock, patch

from rag.faq_retriever import retrieve_faq_context, get_faq_stats


@pytest.mark.rag
class TestFAQRetriever:
    def test_retrieve_returns_empty_when_query_blank(self):
        assert retrieve_faq_context("   ") == []

    @patch("rag.faq_retriever.get_faq_collection")
    @patch("rag.faq_retriever.generate_embeddings")
    def test_retrieve_filters_low_score(self, mock_embed, mock_collection):
        mock_embed.return_value = [[0.1, 0.2, 0.3]]
        collection = MagicMock()
        collection.count.return_value = 1
        collection.query.return_value = {
            "documents": [["What is admission?"]],
            "metadatas": [[{"answer": "Apply online", "source": "FAQ"}]],
            "distances": [[1.9]],
        }
        mock_collection.return_value = collection

        out = retrieve_faq_context("What is admission?", min_score=0.6)
        assert out == []

    @patch("rag.faq_retriever.get_faq_collection")
    @patch("rag.faq_retriever.generate_embeddings")
    def test_retrieve_returns_ranked_faq(self, mock_embed, mock_collection):
        mock_embed.return_value = [[0.1, 0.2, 0.3]]
        collection = MagicMock()
        collection.count.return_value = 1
        collection.query.return_value = {
            "documents": [["What is admission?"]],
            "metadatas": [[{"answer": "Apply online", "source": "Admission FAQ"}]],
            "distances": [[0.2]],
        }
        mock_collection.return_value = collection

        out = retrieve_faq_context("What is admission?", min_score=0.1)
        assert len(out) == 1
        assert out[0]["retrieval_method"] == "faq"
        assert out[0]["source_type"] == "faq"

    @patch("rag.faq_retriever.get_faq_collection")
    def test_stats_reads_collection_count(self, mock_collection):
        collection = MagicMock()
        collection.count.return_value = 7
        mock_collection.return_value = collection

        stats = get_faq_stats()
        assert stats["total_entries"] == 7
