"""
test_helpers.py - Shared test utilities and helper functions
"""

import json
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


class TestDataFactory:
    """Factory for generating test data"""

    @staticmethod
    def create_user(
        user_id: int = 1,
        username: str = "testuser",
        role: str = "student",
        email: str = "test@example.com",
    ) -> Dict[str, Any]:
        """Create test user data"""
        return {
            "id": user_id,
            "username": username,
            "email": email,
            "role": role,
            "created_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def create_document(
        doc_id: int = 1,
        filename: str = "test.pdf",
        file_type: str = "pdf",
        chunks: int = 10,
    ) -> Dict[str, Any]:
        """Create test document data"""
        return {
            "id": doc_id,
            "filename": filename,
            "file_type": file_type,
            "chunk_count": chunks,
            "uploaded_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def create_message(
        message_id: int = 1,
        user_id: int = 1,
        content: str = "Test message",
        role: str = "user",
    ) -> Dict[str, Any]:
        """Create test chat message"""
        return {
            "id": message_id,
            "user_id": user_id,
            "content": content,
            "role": role,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def create_conversation(
        conversation_id: int = 1,
        user_id: int = 1,
        messages: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Create test conversation data"""
        if messages is None:
            messages = []
        return {
            "id": conversation_id,
            "user_id": user_id,
            "messages": messages,
            "created_at": datetime.utcnow().isoformat(),
        }


class APITestClient:
    """Helper for testing API endpoints"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.headers = {}
        self.token = None

    def set_token(self, token: str):
        """Set authorization token"""
        self.token = token
        self.headers["Authorization"] = f"Bearer {token}"

    def get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            "Content-Type": "application/json",
            **self.headers,
        }

    def simulate_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        expected_status: int = 200,
    ) -> Dict[str, Any]:
        """Simulate API request (for mock testing)"""
        return {
            "method": method,
            "endpoint": f"{self.base_url}{endpoint}",
            "data": data,
            "headers": self.get_headers(),
            "expected_status": expected_status,
        }


class PerformanceHelper:
    """Helper for performance testing"""

    def __init__(self):
        self.metrics = {}

    def start_timer(self, name: str):
        """Start timing a operation"""
        self.metrics[name] = {"start": time.time()}

    def end_timer(self, name: str) -> float:
        """End timing and get duration"""
        end = time.time()
        duration = end - self.metrics[name]["start"]
        self.metrics[name]["duration"] = duration
        return duration

    def assert_within_time(self, name: str, max_seconds: float, message: str = ""):
        """Assert operation completed within time limit"""
        duration = self.metrics[name]["duration"]
        assert duration < max_seconds, f"{message}: {duration}s > {max_seconds}s"

    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics"""
        return self.metrics


class MockResponseBuilder:
    """Builder for creating mock API responses"""

    def __init__(self, status: int = 200):
        self.response = {"status": status, "timestamp": datetime.utcnow().isoformat()}

    def add_data(self, key: str, value: Any) -> "MockResponseBuilder":
        """Add data to response"""
        self.response[key] = value
        return self

    def add_success(self, success: bool = True) -> "MockResponseBuilder":
        """Add success flag"""
        self.response["success"] = success
        return self

    def add_error(self, error: str) -> "MockResponseBuilder":
        """Add error message"""
        self.response["error"] = error
        return self

    def add_metadata(self, **kwargs) -> "MockResponseBuilder":
        """Add metadata"""
        self.response["metadata"] = kwargs
        return self

    def build(self) -> Dict[str, Any]:
        """Build the response"""
        return self.response.copy()


class AssertionHelper:
    """Helper methods for common assertions"""

    @staticmethod
    def assert_valid_json(data: str):
        """Assert string is valid JSON"""
        try:
            json.loads(data)
            assert True
        except json.JSONDecodeError:
            assert False, f"Invalid JSON: {data}"

    @staticmethod
    def assert_has_keys(obj: Dict, keys: List[str]):
        """Assert object has required keys"""
        for key in keys:
            assert key in obj, f"Missing required key: {key}"

    @staticmethod
    def assert_in_range(value: float, min_val: float, max_val: float):
        """Assert value is within range"""
        assert min_val <= value <= max_val, f"{value} not in range [{min_val}, {max_val}]"

    @staticmethod
    def assert_non_empty(data: Any):
        """Assert data is not empty"""
        assert data, "Data is empty"

    @staticmethod
    def assert_equals_approx(actual: float, expected: float, tolerance: float = 0.01):
        """Assert values are approximately equal"""
        diff = abs(actual - expected)
        assert diff <= tolerance, f"{actual} !≈ {expected} (diff: {diff})"


def create_test_context(
    user_id: int = 1,
    conversation_id: int = 1,
) -> Dict[str, Any]:
    """Create complete test context"""
    return {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "user": TestDataFactory.create_user(user_id),
        "conversation": TestDataFactory.create_conversation(conversation_id, user_id),
        "messages": [],
        "timestamp": datetime.utcnow().isoformat(),
    }


def create_mock_stream():
    """Create mock streaming response"""
    chunks = [
        {"index": 0, "content": "Part 1 "},
        {"index": 1, "content": "of the "},
        {"index": 2, "content": "response."},
    ]
    return iter(chunks)


def assert_response_structure(response: Dict[str, Any]):
    """Assert response has expected structure"""
    assert "status" in response or "success" in response
    assert "timestamp" in response


def measure_performance(func):
    """Decorator to measure function performance"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(f"{func.__name__} took {duration:.3f}s")
        return result, duration

    return wrapper
