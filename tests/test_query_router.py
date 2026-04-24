"""Unit tests for query routing behavior and keyword-signal edge cases."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.query_router import (  # noqa: E402
    Route,
    MemoryScope,
    classify_query_route,
)


class TestQueryRouter(unittest.TestCase):
    def test_empty_query_routes_to_unclear(self):
        route = classify_query_route("")
        self.assertEqual(route.mode, Route.UNCLEAR)
        self.assertEqual(route.confidence, 0.0)

    def test_official_site_route_for_campus_info(self):
        route = classify_query_route("admission fees and hostel details")
        self.assertEqual(route.mode, Route.OFFICIAL_SITE)
        self.assertEqual(route.source_type, "official_site")
        self.assertEqual(route.memory_scope, MemoryScope.OFFICIAL_SITE)

    def test_document_route_for_uploaded_policy_query(self):
        route = classify_query_route("show uploaded pdf policy")
        self.assertEqual(route.mode, Route.DOCUMENT)
        self.assertEqual(route.source_type, "uploaded")
        self.assertEqual(route.memory_scope, MemoryScope.DOCUMENT)

    def test_faq_route_for_scholarship_question(self):
        # Regression case: should not match general chat via "hi" inside "scholarship".
        route = classify_query_route("how to apply scholarship")
        self.assertEqual(route.mode, Route.FAQ)
        self.assertIn(route.memory_scope, (MemoryScope.OFFICIAL_SITE, MemoryScope.DOCUMENT))

    @patch("rag.query_router.ENABLE_GENERAL_CHAT_ROUTING", True)
    def test_general_chat_for_greeting_when_enabled(self):
        route = classify_query_route("good morning")
        self.assertEqual(route.mode, Route.GENERAL_CHAT)
        self.assertEqual(route.memory_scope, MemoryScope.GENERAL_CHAT)

    @patch("rag.query_router.ENABLE_GENERAL_CHAT_ROUTING", True)
    def test_no_false_general_chat_substring_hit(self):
        route = classify_query_route("how to apply scholarship")
        self.assertNotEqual(route.mode, Route.GENERAL_CHAT)

    @patch("rag.query_router.ENABLE_GENERAL_CHAT_ROUTING", False)
    def test_general_chat_disabled_falls_back(self):
        route = classify_query_route("hello")
        self.assertEqual(route.mode, Route.UNCLEAR)


if __name__ == "__main__":
    unittest.main()
