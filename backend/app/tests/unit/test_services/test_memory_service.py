"""
Unit tests for MemoryService.

Tests memory retrieval and context building including:
- Vector similarity search
- Recent message retrieval
- Session summaries
- Memory formatting for prompts
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.memory_service import MemoryService, memory_service


@pytest.mark.asyncio
class TestMemoryService:
    """Test suite for MemoryService."""

    async def test_get_memory_context_with_all_sources(
        self,
        mock_db,
        sample_embedding
    ):
        """Test memory context retrieval with all sources available."""
        # Arrange
        user_id = "test_user_123"
        query = "What is the weather?"

        # Mock vector search
        similar_queries = [
            {
                "query": "Weather yesterday?",
                "response": "It was sunny",
                "timestamp": "2025-12-28T10:00:00Z",
                "similarity": 0.92
            },
            {
                "query": "Temperature today?",
                "response": "75 degrees",
                "timestamp": "2025-12-28T09:00:00Z",
                "similarity": 0.88
            }
        ]

        # Mock recent messages
        recent_docs = [
            {
                "query": "Hello",
                "response": "Hi there!",
                "timestamp": "2025-12-28T12:00:00Z",
                "intent": "greeting"
            }
        ]

        # Mock summaries
        summary_docs = [
            {
                "summary_text": "User asked about weather",
                "session_id": "session_123",
                "timestamp": "2025-12-28T11:00:00Z",
                "topics": ["weather", "forecast"]
            }
        ]

        with patch("app.services.memory_service.get_db") as mock_get_db, \
             patch.object(memory_service.vector_search, "search_similar") as mock_search:

            # Setup mocks
            mock_get_db.return_value = mock_db

            # Mock vector search
            mock_search.return_value = similar_queries

            # Mock queries collection for recent messages
            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.limit.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=recent_docs)
            mock_db.queries.find.return_value = mock_cursor

            # Mock summaries collection
            mock_summary_cursor = MagicMock()
            mock_summary_cursor.sort.return_value = mock_summary_cursor
            mock_summary_cursor.limit.return_value = mock_summary_cursor
            mock_summary_cursor.to_list = AsyncMock(return_value=summary_docs)
            mock_db.summaries.find.return_value = mock_summary_cursor

            # Act
            context = await memory_service.get_memory_context(
                user_id=user_id,
                query=query,
                query_embedding=sample_embedding,
                limit=5
            )

            # Assert
            assert "similar_queries" in context
            assert "recent_messages" in context
            assert "summaries" in context
            assert "total_items" in context

            assert len(context["similar_queries"]) == 2
            assert len(context["recent_messages"]) == 1
            assert len(context["summaries"]) == 1
            assert context["total_items"] == 4

            # Verify vector search was called correctly
            mock_search.assert_called_once_with(
                query_vector=sample_embedding,
                limit=5,
                filter_dict={"user_id": user_id}
            )

    async def test_get_memory_context_with_no_database(
        self,
        sample_embedding
    ):
        """Test memory context when database is not available."""
        # Arrange
        with patch("app.services.memory_service.get_db") as mock_get_db:
            mock_get_db.return_value = None

            # Act
            context = await memory_service.get_memory_context(
                user_id="test_user",
                query="test query",
                query_embedding=sample_embedding,
                limit=5
            )

            # Assert
            assert context["similar_queries"] == []
            assert context["recent_messages"] == []
            assert context["summaries"] == []
            assert context["total_items"] == 0

    async def test_get_memory_context_handles_vector_search_failure(
        self,
        mock_db,
        sample_embedding
    ):
        """Test graceful handling of vector search failures."""
        # Arrange
        with patch("app.services.memory_service.get_db") as mock_get_db, \
             patch.object(memory_service.vector_search, "search_similar") as mock_search:

            mock_get_db.return_value = mock_db
            mock_search.side_effect = Exception("Vector search failed")

            # Mock empty results for other sources
            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.limit.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=[])
            mock_db.queries.find.return_value = mock_cursor
            mock_db.summaries.find.return_value = mock_cursor

            # Act
            context = await memory_service.get_memory_context(
                user_id="test_user",
                query="test query",
                query_embedding=sample_embedding,
                limit=5
            )

            # Assert - should return empty similar_queries but not crash
            assert context["similar_queries"] == []
            assert "recent_messages" in context
            assert "summaries" in context

    async def test_format_memory_for_prompt_with_all_data(
        self,
        sample_memory_context
    ):
        """Test memory formatting for LLM prompts."""
        # Arrange
        memory_context = {
            "similar_queries": [
                {
                    "query": "What's the weather?",
                    "response": "It's sunny and 75 degrees with clear skies.",
                    "timestamp": "2025-12-28T10:00:00Z"
                },
                {
                    "query": "Temperature tomorrow?",
                    "response": "Expected high of 78 degrees tomorrow.",
                    "timestamp": "2025-12-28T09:00:00Z"
                }
            ],
            "recent_messages": [
                {"query": "Hello", "response": "Hi!", "timestamp": "2025-12-28T12:00:00Z"}
            ],
            "summaries": [
                {
                    "summary": "User discussed weather and forecasts",
                    "session_id": "session_123",
                    "timestamp": "2025-12-28T11:00:00Z"
                }
            ]
        }

        # Act
        formatted = memory_service.format_memory_for_prompt(memory_context, max_items=5)

        # Assert
        assert "Similar Past Conversations:" in formatted
        assert "What's the weather?" in formatted
        assert "Recent Conversation:" in formatted
        assert "Hello" in formatted
        assert "Previous Session Summaries:" in formatted
        assert "User discussed weather" in formatted

    async def test_format_memory_for_prompt_with_empty_context(self):
        """Test memory formatting with empty context."""
        # Arrange
        empty_context = {
            "similar_queries": [],
            "recent_messages": [],
            "summaries": []
        }

        # Act
        formatted = memory_service.format_memory_for_prompt(empty_context)

        # Assert
        assert formatted == ""

    async def test_format_memory_for_prompt_respects_max_items(self):
        """Test that formatting respects max_items limit."""
        # Arrange
        memory_context = {
            "similar_queries": [
                {"query": f"Query {i}", "response": f"Response {i}"}
                for i in range(10)
            ],
            "recent_messages": [],
            "summaries": []
        }

        # Act
        formatted = memory_service.format_memory_for_prompt(memory_context, max_items=3)

        # Assert
        # Should only include first 3 items
        assert "Query 0" in formatted
        assert "Query 1" in formatted
        assert "Query 2" in formatted
        assert "Query 3" not in formatted

    async def test_get_memory_context_filters_by_user_id(
        self,
        mock_db,
        sample_embedding
    ):
        """Test that memory queries are filtered by user_id."""
        # Arrange
        user_id = "specific_user_123"

        with patch("app.services.memory_service.get_db") as mock_get_db, \
             patch.object(memory_service.vector_search, "search_similar") as mock_search:

            mock_get_db.return_value = mock_db
            mock_search.return_value = []

            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.limit.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=[])
            mock_db.queries.find.return_value = mock_cursor
            mock_db.summaries.find.return_value = mock_cursor

            # Act
            await memory_service.get_memory_context(
                user_id=user_id,
                query="test",
                query_embedding=sample_embedding,
                limit=5
            )

            # Assert - verify filter was applied
            mock_search.assert_called_once_with(
                query_vector=sample_embedding,
                limit=5,
                filter_dict={"user_id": user_id}
            )

            # Check queries collection filter
            mock_db.queries.find.assert_called_once_with({"user_id": user_id})
