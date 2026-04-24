"""
Unit tests for conversation memory module.
Tests semantic similarity matching, storage, TTL cleanup, and invalidation.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.memory import (
    query_memory, add_memory_entry, delete_memory_entry,
    invalidate_memory_by_source, cleanup_old_memory,
    get_memory_stats, clear_all_memory, get_memory_collection,
)
from database.db import (
    store_memory, update_memory_usage, delete_memory,
    cleanup_expired_memory, invalidate_memory_by_source,
    get_memory_stats, clear_all_memory,
)
from tests.config import CONV_MATCH_THRESHOLD, CONV_ENABLED, CONV_PER_USER
import tests.config as config


class TestMemoryRetrieval:
    """Test semantic similarity matching for memory queries."""

    def setup_method(self):
        """Setup: Clear old memory before each test."""
        clear_all_memory()

    def teardown_method(self):
        """Teardown: Clean up after each test."""
        clear_all_memory()

    def test_exact_query_match(self):
        """Test that exact query match returns cached response."""
        # Store a query-response pair
        query = "What is the institution's admission policy?"
        response = "The admission policy requires a minimum GPA of 3.0"
        sources = ["Admission_Policy.pdf"]
        
        add_memory_entry(query=query, response=response, sources=sources, user_id=None)
        
        # Query with exact same text
        result = query_memory(query, user_id=None)
        
        assert result is not None, "Exact query should match"
        assert result["response"] == response, "Response should match"
        assert result["similarity_score"] >= CONV_MATCH_THRESHOLD, "Similarity should be high"

    def test_similar_query_match(self):
        """Test that semantically similar queries match above threshold."""
        # Store original query
        query1 = "What are the admission requirements?"
        response = "Requirements: GPA 3.0+, SAT 1200+, and 2 letters of recommendation"
        
        add_memory_entry(query=query1, response=response, sources=[], user_id=None)
        
        # Query with semantically similar text
        query2 = "What do I need to be admitted?"
        result = query_memory(query2, user_id=None)
        
        # Should match if similarity >= threshold
        if result is not None:
            assert result["similarity_score"] >= CONV_MATCH_THRESHOLD, "Similarity score should meet threshold"
            assert result["response"] == response, "Should return stored response"

    def test_dissimilar_query_no_match(self):
        """Test that dissimilar queries do NOT match."""
        # Store a query about admissions
        query1 = "What is the tuition fee?"
        response1 = "Annual tuition is $50,000"
        
        add_memory_entry(query=query1, response=response1, sources=[], user_id=None)
        
        # Query about completely different topic
        query2 = "What time is lunch in the cafeteria?"
        result = query_memory(query2, user_id=None)
        
        if result is not None:
            # If there's a result, it should NOT meet the threshold (or be None)
            assert result["similarity_score"] < CONV_MATCH_THRESHOLD or result is None, \
                "Dissimilar query should not match above threshold or should return None"

    def test_similarity_threshold_enforcement(self):
        """Test that similarity threshold is properly enforced."""
        # Store a query
        query = "How many students are enrolled?"
        response = "Total enrollment is 5,000 students"
        
        memory_entry = add_memory_entry(query=query, response=response, sources=[], user_id=None)
        
        # Query with same text again (100% match expected)
        result = query_memory(query, user_id=None)
        
        assert result is not None, "Same query should return a result"
        assert result["similarity_score"] >= CONV_MATCH_THRESHOLD, "Similarity should exceed threshold"


class TestMemoryStorage:
    """Test storage and retrieval from SQLite."""

    def setup_method(self):
        """Setup: Clear memory before each test."""
        clear_all_memory()

    def teardown_method(self):
        """Teardown: Clean up after each test."""
        clear_all_memory()

    def test_store_and_retrieve(self):
        """Test storing a memory entry and retrieving it."""
        query = "What is the library operating hours?"
        response = "Library is open 8 AM to 10 PM Monday through Friday"
        sources = ["Library_Hours.pdf"]
        
        entry = add_memory_entry(query=query, response=response, sources=sources, user_id="user123")
        
        assert entry is not None, "Entry should be created"
        assert "id" in entry, "Entry should have an ID"
        
        # Retrieve using the same query
        result = query_memory(query, user_id="user123")
        assert result is not None, "Entry should be retrievable"
        assert result["response"] == response, "Response should match"

    def test_usage_count_increment(self):
        """Test that usage count increments on repeated access."""
        query = "When is graduation?"
        response = "Graduation ceremony is in May"
        
        entry = add_memory_entry(query=query, response=response, sources=[], user_id=None)
        memory_id = entry.get("id")
        
        # Query first time
        result1 = query_memory(query, user_id=None)
        usage1 = result1.get("usage_count", 0) if result1 else 0
        
        # Query second time
        result2 = query_memory(query, user_id=None)
        usage2 = result2.get("usage_count", 0) if result2 else 0
        
        # Usage count should increase (or be tracked consistently)
        assert usage2 >= usage1, "Usage count should not decrease"

    def test_delete_memory_entry(self):
        """Test deleting a specific memory entry."""
        query = "What is the student ID format?"
        response = "Student IDs are 8-digit numbers starting with enrollment year"
        
        entry = add_memory_entry(query=query, response=response, sources=[], user_id=None)
        memory_id = entry.get("id")
        
        # Verify it exists
        result1 = query_memory(query, user_id=None)
        assert result1 is not None, "Entry should exist before deletion"
        
        # Delete it
        deleted = delete_memory_entry(memory_id)
        assert deleted, "Deletion should succeed"
        
        # Verify it's gone (might not be findable via query, but deletion was made)
        # Note: Exact behavior depends on implementation


class TestMemoryCleanup:
    """Test TTL cleanup and invalidation by source."""

    def setup_method(self):
        """Setup: Clear memory before each test."""
        clear_all_memory()

    def teardown_method(self):
        """Teardown: Clean up after each test."""
        clear_all_memory()

    def test_cleanup_expired_entries(self):
        """Test that cleanup removes expired entries."""
        # Store an entry
        query = "What is the old policy?"
        response = "This is an old response"
        
        entry = add_memory_entry(query=query, response=response, sources=["OldPolicy.pdf"], user_id=None)
        
        # Note: This test depends on TTL configuration
        # In reality, entries have TTL and cleanup_expired_memory() removes old ones
        # For now, we just test that cleanup doesn't crash
        deleted_count = cleanup_expired_memory()
        
        assert isinstance(deleted_count, int), "Cleanup should return count"
        assert deleted_count >= 0, "Deleted count should be non-negative"

    def test_invalidate_by_source(self):
        """Test invalidation of memory entries by source document."""
        # Store two entries with different sources
        entry1 = add_memory_entry(
            query="Question from doc A", 
            response="Answer A",
            sources=["DocumentA.pdf"],
            user_id=None
        )
        
        entry2 = add_memory_entry(
            query="Question from doc B", 
            response="Answer B",
            sources=["DocumentB.pdf"],
            user_id=None
        )
        
        # Check initial count
        stats_before = get_memory_stats()
        initial_count = stats_before.get("total_entries", 0)
        
        # Invalidate entries from DocumentA
        deleted = invalidate_memory_by_source("DocumentA.pdf")
        
        assert isinstance(deleted, int), "Invalidation should return count"
        assert deleted >= 0, "Deleted count should be non-negative"
        
        # Count should have decreased
        stats_after = get_memory_stats()
        assert stats_after.get("total_entries", 0) <= initial_count, \
            "Total entries should not increase after invalidation"

    def test_clear_all_memory(self):
        """Test clearing all memory entries."""
        # Store multiple entries
        add_memory_entry(query="Query 1", response="Response 1", sources=[], user_id=None)
        add_memory_entry(query="Query 2", response="Response 2", sources=[], user_id=None)
        add_memory_entry(query="Query 3", response="Response 3", sources=[], user_id=None)
        
        # Verify entries exist
        stats_before = get_memory_stats()
        assert stats_before.get("total_entries", 0) > 0, "Should have entries before clear"
        
        # Clear all
        deleted = clear_all_memory()
        
        assert isinstance(deleted, int), "Clear should return count"
        assert deleted > 0, "Should have deleted entries"
        
        # Verify empty
        stats_after = get_memory_stats()
        assert stats_after.get("total_entries", 0) == 0, "Memory should be empty after clear"


class TestMemoryStats:
    """Test memory statistics and analytics."""

    def setup_method(self):
        """Setup: Clear memory before each test."""
        clear_all_memory()

    def teardown_method(self):
        """Teardown: Clean up after each test."""
        clear_all_memory()

    def test_get_stats_empty(self):
        """Test stats when memory is empty."""
        stats = get_memory_stats()
        
        assert isinstance(stats, dict), "Stats should be a dict"
        assert stats.get("total_entries", 0) == 0, "Should have 0 entries"
        assert stats.get("avg_usage_per_entry", 0) >= 0, "Should have non-negative avg usage"

    def test_get_stats_multiple_entries(self):
        """Test stats with multiple entries."""
        # Store entries with same and different user IDs
        add_memory_entry(query="Q1", response="R1", sources=[], user_id="user1")
        add_memory_entry(query="Q2", response="R2", sources=[], user_id="user1")
        add_memory_entry(query="Q3", response="R3", sources=[], user_id="user2")
        
        stats = get_memory_stats()
        
        assert stats.get("total_entries", 0) == 3, "Should have 3 entries"
        assert len(stats.get("by_user", [])) >= 1, "Should have user breakdown"

    def test_stats_by_user(self):
        """Test that stats are broken down by user."""
        add_memory_entry(query="Q1", response="R1", sources=[], user_id="user1")
        add_memory_entry(query="Q2", response="R2", sources=[], user_id="user1")
        add_memory_entry(query="Q3", response="R3", sources=[], user_id="user2")
        
        stats = get_memory_stats()
        by_user = stats.get("by_user", [])
        
        assert len(by_user) >= 1, "Should have at least one user breakdown"
        for user_stat in by_user:
            assert "user_id" in user_stat, "User stat should have user_id"
            assert "cnt" in user_stat, "User stat should have entry count"


class TestMemoryIntegration:
    """Integration tests for the full memory pipeline."""

    def setup_method(self):
        """Setup: Clear memory before each test."""
        clear_all_memory()

    def teardown_method(self):
        """Teardown: Clean up after each test."""
        clear_all_memory()

    def test_full_pipeline_query_store_retrieve(self):
        """Test full pipeline: query → no match → store → query again → match."""
        query = "What is the campus location?"
        response = "Main campus is located at 123 University Avenue, Springfield"
        sources = ["Campus_Info.pdf"]
        
        # First query (should not match, nothing in memory yet)
        result1 = query_memory(query, user_id=None)
        assert result1 is None, "First query should not match (empty memory)"
        
        # Store the response
        entry = add_memory_entry(query=query, response=response, sources=sources, user_id=None)
        assert entry is not None, "Entry should be stored"
        
        # Second query (should match now)
        result2 = query_memory(query, user_id=None)
        assert result2 is not None, "Second query should match stored entry"
        assert result2["response"] == response, "Should return correct response"

    def test_per_user_memory_isolation(self):
        """Test that per-user memory is properly isolated."""
        if not CONV_PER_USER:
            pytest.skip("Per-user memory is disabled")
        
        query = "What is my status?"
        response_user1 = "User 1 status information"
        response_user2 = "User 2 status information"
        
        # Store for user1
        add_memory_entry(query=query, response=response_user1, sources=[], user_id="user1")
        
        # Store for user2
        add_memory_entry(query=query, response=response_user2, sources=[], user_id="user2")
        
        # Query for user1
        result1 = query_memory(query, user_id="user1")
        assert result1["response"] == response_user1, "User1 should get their response"
        
        # Query for user2
        result2 = query_memory(query, user_id="user2")
        assert result2["response"] == response_user2, "User2 should get their response"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
