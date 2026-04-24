"""
test_query_router.py - Query routing tests
Tests routing behavior for faq/document/general-chat pre-classification.
"""

import pytest

from rag.query_router import classify_query_route


@pytest.mark.chat
class TestQueryRouterModes:
    """Tests for route classification modes."""

    def test_routes_general_greeting_to_general_chat(self):
        route = classify_query_route("hello how are you")
        assert route.mode == "general_chat"
        assert route.confidence >= 0.6

    def test_routes_institutional_faq_query_to_faq(self):
        route = classify_query_route("What is the admission process for this college?")
        assert route.mode == "faq"
        assert route.source_type in ("official_site", "uploaded")

    def test_routes_document_query_to_document(self):
        route = classify_query_route("What does the attendance policy say?")
        assert route.mode in ("document", "hybrid", "faq")

    def test_routes_empty_query_to_unclear(self):
        route = classify_query_route("   ")
        assert route.mode == "unclear"

    def test_routes_mixed_query_to_non_general(self):
        route = classify_query_route("hi, what are the course fees and admission details?")
        assert route.mode in ("official_site", "document", "hybrid", "faq")
        assert route.mode != "general_chat"
