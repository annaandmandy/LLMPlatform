"""
Pytest configuration and shared fixtures.

This file provides reusable test fixtures for:
- Mock database connections
- Test clients
- Sample data factories
- Service mocks
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
from datetime import datetime

from app.main import app
from app.core.config import settings


# ==================== Test Client ====================

@pytest.fixture
def test_client(mock_db_stateful):
    """FastAPI test client for integration tests with stateful mocked database."""
    from app.db.mongodb import get_db

    # Patch get_db to return mock_db for both dependency injection and direct calls
    with patch("app.db.mongodb.get_db", return_value=mock_db_stateful), \
         patch("app.api.v1.sessions.get_db", return_value=mock_db_stateful), \
         patch("app.api.v1.query.get_db", return_value=mock_db_stateful):

        # Also override FastAPI dependency
        app.dependency_overrides[get_db] = lambda: mock_db_stateful

        client = TestClient(app)
        yield client

        # Clean up
        app.dependency_overrides.clear()


# ==================== Mock Database ====================

@pytest_asyncio.fixture
async def mock_db():
    """
    Simple mock MongoDB database for unit testing.
    Returns basic mocks without state management - unit tests control behavior explicitly.
    """
    mock_database = MagicMock()

    # Mock collections
    for collection_name in ["queries", "sessions", "products", "files", "summaries"]:
        collection = MagicMock()
        collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id="mock_id"))
        collection.find_one = AsyncMock(return_value=None)

        # Create async cursor mock for find()
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[])
        collection.find = MagicMock(return_value=mock_cursor)

        collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        collection.count_documents = AsyncMock(return_value=0)

        # Set as both attribute and dict item
        setattr(mock_database, collection_name, collection)

    # Support dict-style access db["collection_name"]
    type(mock_database).__getitem__ = lambda self, key: getattr(self, key, MagicMock())

    return mock_database


@pytest_asyncio.fixture
async def mock_db_stateful():
    """
    Stateful mock MongoDB database for integration testing.
    Returns a MagicMock that simulates MongoDB collections with actual data persistence.
    Use this for integration tests where data needs to persist across multiple API calls.
    """
    mock_database = MagicMock()

    # In-memory storage for each collection
    collection_storage = {
        "queries": {},
        "sessions": {},
        "products": {},
        "files": {},
        "summaries": {}
    }

    # Mock collections
    for collection_name in ["queries", "sessions", "products", "files", "summaries"]:
        collection = MagicMock()
        storage = collection_storage[collection_name]

        # insert_one - store document
        async def _insert_one(doc, _storage=storage):
            doc_id = doc.get("_id", f"mock_id_{len(_storage)}")
            doc["_id"] = doc_id
            # Use session_id or user_id as key if available
            key = doc.get("session_id") or doc.get("user_id") or doc_id
            _storage[key] = doc.copy()
            return MagicMock(inserted_id=doc_id)
        collection.insert_one = AsyncMock(side_effect=_insert_one)

        # find_one - retrieve document
        async def _find_one(query, projection=None, _storage=storage):
            # Look for match in storage
            for key, doc in _storage.items():
                match = True
                for field, value in query.items():
                    if doc.get(field) != value:
                        match = False
                        break
                if match:
                    # Apply projection if provided
                    if projection:
                        result = {}
                        for k, v in doc.items():
                            # Include field if not explicitly excluded (projection value == 0)
                            if k not in projection or projection.get(k) != 0:
                                result[k] = v
                        # Remove fields that are explicitly excluded
                        for k, v in projection.items():
                            if v == 0 and k in result:
                                del result[k]
                        return result
                    return doc.copy()
            return None
        collection.find_one = AsyncMock(side_effect=_find_one)

        # find - return cursor
        def _find(query, _storage=storage):
            mock_cursor = MagicMock()
            mock_cursor.sort = MagicMock(return_value=mock_cursor)
            mock_cursor.limit = MagicMock(return_value=mock_cursor)

            async def _to_list(length=None):
                results = []
                for doc in _storage.values():
                    match = True
                    for field, value in query.items():
                        if doc.get(field) != value:
                            match = False
                            break
                    if match:
                        results.append(doc.copy())
                return results[:length] if length else results

            mock_cursor.to_list = AsyncMock(side_effect=_to_list)
            return mock_cursor
        collection.find = MagicMock(side_effect=_find)

        # update_one - update document
        async def _update_one(query, update_doc, _storage=storage):
            for key, doc in _storage.items():
                match = True
                for field, value in query.items():
                    if doc.get(field) != value:
                        match = False
                        break
                if match:
                    # Apply $set operations
                    if "$set" in update_doc:
                        doc.update(update_doc["$set"])
                    # Apply $push operations
                    if "$push" in update_doc:
                        for field, value in update_doc["$push"].items():
                            if field not in doc:
                                doc[field] = []
                            doc[field].append(value)
                    return MagicMock(modified_count=1)
            return MagicMock(modified_count=0)
        collection.update_one = AsyncMock(side_effect=_update_one)

        # delete_one - delete document
        async def _delete_one(query, _storage=storage):
            for key, doc in list(_storage.items()):
                match = True
                for field, value in query.items():
                    if doc.get(field) != value:
                        match = False
                        break
                if match:
                    del _storage[key]
                    return MagicMock(deleted_count=1)
            return MagicMock(deleted_count=0)
        collection.delete_one = AsyncMock(side_effect=_delete_one)

        # count_documents
        async def _count_documents(query, _storage=storage):
            count = 0
            for doc in _storage.values():
                match = True
                for field, value in query.items():
                    if doc.get(field) != value:
                        match = False
                        break
                if match:
                    count += 1
            return count
        collection.count_documents = AsyncMock(side_effect=_count_documents)

        # Set as both attribute and dict item
        setattr(mock_database, collection_name, collection)

    # Support dict-style access db["collection_name"]
    type(mock_database).__getitem__ = lambda self, key: getattr(self, key, MagicMock())

    return mock_database


@pytest.fixture
def override_get_db(mock_db):
    """Override the get_db dependency with mock database."""
    async def _get_mock_db():
        yield mock_db
    return _get_mock_db


# ==================== Sample Data Factories ====================

@pytest.fixture
def sample_query_request() -> Dict[str, Any]:
    """Factory for creating sample QueryRequest data."""
    return {
        "user_id": "test_user_123",
        "session_id": "test_session_456",
        "query": "What is the weather today?",
        "model_provider": "openai",
        "model_name": "gpt-4o-mini",
        "web_search": False,
        "use_memory": True,
        "use_product_search": False,
        "history": [],
        "location": None,
        "attachments": None,
        "mode": "chat"
    }


@pytest.fixture
def sample_query_response() -> Dict[str, Any]:
    """Factory for creating sample QueryResponse data."""
    return {
        "response": "The weather is sunny today with a high of 75°F.",
        "citations": None,
        "product_cards": None,
        "product_json": None,
        "user_location": None,
        "memory_context": None,
        "intent": "weather_query",
        "agents_used": ["coordinator"],
        "options": None,
        "shopping_status": None
    }


@pytest.fixture
def sample_session_start_request() -> Dict[str, Any]:
    """Factory for creating sample SessionStartRequest data."""
    return {
        "session_id": "test_session_789",
        "user_id": "test_user_123",
        "experiment_id": "default",
        "environment": {
            "device": "desktop",
            "browser": "Chrome 120",
            "os": "macOS",
            "viewport": {"width": 1920, "height": 1080},
            "language": "en",
            "connection": "4g",
            "location": None
        }
    }


@pytest.fixture
def sample_event() -> Dict[str, Any]:
    """Factory for creating sample Event data."""
    return {
        "t": int(datetime.utcnow().timestamp() * 1000),
        "type": "prompt",
        "data": {
            "text": "Hello, world!",
            "model": "gpt-4o-mini",
            "provider": "openai"
        }
    }


@pytest.fixture
def sample_embedding() -> List[float]:
    """Factory for creating sample embedding vector."""
    # Return a 1536-dimension vector (OpenAI embedding size)
    return [0.1] * 1536


@pytest.fixture
def sample_memory_context() -> Dict[str, Any]:
    """Factory for creating sample memory context."""
    return {
        "relevant_memories": [
            {
                "query": "Previous question about weather",
                "response": "Yesterday was rainy.",
                "timestamp": "2025-12-28T12:00:00Z",
                "similarity": 0.85
            }
        ],
        "context_summary": "User has previously asked about weather."
    }


# ==================== Service Mocks ====================

@pytest.fixture
def mock_embedding_service():
    """Mock EmbeddingService for testing."""
    with patch("app.services.embedding_service.embedding_service") as mock:
        mock.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
        yield mock


@pytest.fixture
def mock_memory_service():
    """Mock MemoryService for testing."""
    with patch("app.services.memory_service.memory_service") as mock:
        mock.get_relevant_context = AsyncMock(return_value={
            "relevant_memories": [],
            "context_summary": None
        })
        yield mock


@pytest.fixture
def mock_query_service():
    """Mock QueryService for testing."""
    with patch("app.services.query_service.query_service") as mock, \
         patch("app.api.v1.query.query_service", mock):
        mock.process_query = AsyncMock(return_value={
            "response": "Test response",
            "citations": None,
            "product_cards": None,
            "product_json": None,
            "user_location": None,
            "memory_context": None,
            "intent": "test",
            "agents_used": ["coordinator"],
            "options": None,
            "shopping_status": None
        })
        yield mock


@pytest.fixture
def mock_session_service():
    """Mock SessionService for testing."""
    with patch("app.services.session_service.session_service") as mock:
        mock.start_session = AsyncMock(return_value={
            "session_id": "test_session_789",
            "status": "created",
            "message": "Session started successfully"
        })
        mock.add_event = AsyncMock(return_value={
            "session_id": "test_session_789",
            "status": "updated",
            "message": "Event added successfully"
        })
        mock.end_session = AsyncMock(return_value={
            "session_id": "test_session_789",
            "status": "ended",
            "message": "Session ended successfully"
        })
        yield mock


@pytest.fixture
def mock_file_service():
    """Mock FileService for testing."""
    with patch("app.services.file_service.file_service") as mock:
        mock.upload_file = AsyncMock(return_value={
            "file_id": "test_file_123",
            "filename": "test.txt",
            "size": 1024,
            "uploaded_at": datetime.utcnow().isoformat()
        })
        mock.get_files = AsyncMock(return_value=[])
        mock.delete_file = AsyncMock(return_value=True)
        yield mock


# ==================== Provider Mocks ====================

@pytest.fixture
def mock_provider():
    """Mock LLM provider for testing."""
    mock = AsyncMock()
    mock.generate = AsyncMock(return_value="Mocked LLM response")
    mock.generate_stream = AsyncMock()
    return mock


@pytest.fixture
def mock_provider_factory():
    """Mock ProviderFactory for testing."""
    with patch("app.providers.factory.ProviderFactory") as mock_factory:
        mock_provider = AsyncMock()
        mock_provider.generate = AsyncMock(return_value="Mocked response")
        mock_factory.get_provider.return_value = mock_provider
        yield mock_factory


# ==================== Agent Mocks ====================

@pytest.fixture
def mock_coordinator():
    """Mock coordinator agent for testing."""
    with patch("app.agents.get_coordinator") as mock:
        mock_agent = AsyncMock()
        mock_agent.process = AsyncMock(return_value={
            "response": "Agent response",
            "intent": "test_intent",
            "agents_used": ["coordinator"]
        })
        mock.return_value = mock_agent
        yield mock


# ==================== Test Utilities ====================

@pytest.fixture
def assert_datetime_recent():
    """Helper to assert a datetime string is recent (within last 5 seconds)."""
    def _assert(dt_string: str):
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        now = datetime.utcnow()
        delta = (now - dt.replace(tzinfo=None)).total_seconds()
        assert delta < 5, f"Timestamp {dt_string} is not recent (delta: {delta}s)"
    return _assert


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return {
        "MONGODB_URI": "mongodb://localhost:27017",
        "MONGO_DB": "test_db",
        "OPENAI_API_KEY": "test_openai_key",
        "ANTHROPIC_API_KEY": "test_anthropic_key",
        "UPLOAD_DIR": "/tmp/test_uploads"
    }
