"""
conftest.py - Shared pytest fixtures and configuration for all backend tests
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set test environment
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["LLM_MODE"] = "local_only"


@pytest.fixture(scope="session")
def test_config():
    """Session-level test configuration"""
    return {
        "testing": True,
        "database": "sqlite:///:memory:",
        "llm_mode": "local_only",
        "upload_dir": "/tmp/test_uploads",
        "chroma_dir": "/tmp/test_chroma",
    }


@pytest.fixture
def temp_upload_dir(tmp_path):
    """Create temporary upload directory for each test"""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    return upload_dir


@pytest.fixture
def temp_chroma_dir(tmp_path):
    """Create temporary ChromaDB directory for each test"""
    chroma_dir = tmp_path / "chroma_db"
    chroma_dir.mkdir()
    return chroma_dir


@pytest.fixture
def mock_database():
    """Create mock database connection"""
    mock_db = MagicMock()
    mock_db.cursor.return_value.fetchone.return_value = None
    mock_db.cursor.return_value.fetchall.return_value = []
    return mock_db


@pytest.fixture
def mock_chroma_client():
    """Create mock ChromaDB client"""
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    return mock_client


@pytest.fixture
def test_user_data():
    """Standard test user data"""
    return {
        "username": "testuser",
        "password": "testpass123",
        "email": "test@example.com",
        "role": "student",
    }


@pytest.fixture
def test_admin_data():
    """Standard test admin user data"""
    return {
        "username": "admin",
        "password": "admin123",
        "email": "admin@example.com",
        "role": "admin",
    }


@pytest.fixture
def test_document_data():
    """Standard test document data"""
    return {
        "filename": "test_document.pdf",
        "original_name": "Test Document.pdf",
        "file_type": "pdf",
        "file_size": 1024,
        "chunk_count": 10,
    }


@pytest.fixture
def test_chat_message():
    """Standard test chat message"""
    return {
        "user_id": 1,
        "conversation_id": 1,
        "message": "What is the attendance policy?",
        "role": "user",
    }


@pytest.fixture
def test_rag_context():
    """Standard test RAG context"""
    return {
        "query": "attendance policy",
        "documents": [
            {
                "id": "doc_1",
                "content": "Attendance must be 75% for eligibility",
                "metadata": {"source": "regulations.pdf"},
            }
        ],
        "metadata": {
            "retrieval_time": 0.234,
            "relevance_scores": [0.92],
        },
    }


@pytest.fixture
def mock_llm_response():
    """Mock LLM response"""
    return {
        "response": "The attendance policy requires 75% attendance for academic eligibility.",
        "sources": ["regulations.pdf"],
        "confidence": "High",
        "type": "Official institutional answer",
    }


@pytest.fixture
def mock_auth_token():
    """Generate mock JWT token"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImlkIjoxLCJyb2xlIjoic3R1ZGVudCJ9.mock_signature"


@pytest.fixture
def mock_embedding():
    """Mock embedding vector"""
    import numpy as np
    return np.random.rand(384).tolist()  # sentence-transformers default


@pytest.fixture
def mock_file_upload(tmp_path):
    """Create mock file upload"""
    test_file = tmp_path / "test_document.txt"
    test_file.write_text("This is test content for document processing.")
    return test_file


@pytest.fixture
def mock_audio_file(tmp_path):
    """Create mock audio file for voice testing"""
    audio_file = tmp_path / "test_audio.wav"
    # Create minimal WAV file header
    import wave
    with wave.open(str(audio_file), 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b'\x00\x00' * 16000)  # 1 second of silence
    return audio_file


@pytest.fixture
def mock_ollama_response():
    """Mock Ollama LLM response"""
    return {
        "model": "qwen2.5:0.5b",
        "response": "Test response from Ollama",
        "done": True,
        "context": [1, 2, 3],
        "total_duration": 1000000,
        "load_duration": 100000,
        "prompt_eval_count": 10,
        "prompt_eval_duration": 200000,
        "eval_count": 50,
        "eval_duration": 700000,
    }


@pytest.fixture
def mock_groq_response():
    """Mock Groq API response"""
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "llama-3.3-70b-versatile",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Test response from Groq",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 25,
        },
    }


@pytest.fixture
def mock_gemini_response():
    """Mock Google Gemini API response"""
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "Test response from Gemini",
                        }
                    ],
                    "role": "model",
                },
                "finishReason": "STOP",
                "index": 0,
                "safetyRatings": [
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "probability": "NEGLIGIBLE",
                    }
                ],
            }
        ],
    }


@pytest.fixture
def rate_limit_config():
    """Standard rate limiting configuration"""
    return {
        "global_limit": "100/minute",
        "per_user_limit": "30/minute",
        "chat_limit": "5/minute",
        "upload_limit": "10/minute",
        "auth_limit": "5/minute",
    }


# Markers for test categories
def pytest_configure(config):
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "auth: mark test as authentication related")
    config.addinivalue_line("markers", "chat: mark test as chat related")
    config.addinivalue_line("markers", "document: mark test as document related")
    config.addinivalue_line("markers", "rag: mark test as RAG pipeline related")
    config.addinivalue_line("markers", "provider: mark test as LLM provider related")
