"""
Unit tests for QueryService.

Tests the main query processing service including:
- Query processing with agents
- Query processing with providers
- Memory integration
- Database logging
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.query_service import QueryService, query_service
from app.schemas.query import QueryRequest, QueryResponse


@pytest.mark.asyncio
class TestQueryService:
    """Test suite for QueryService."""

    async def test_process_query_with_agents(
        self,
        sample_query_request,
        sample_embedding,
        sample_memory_context,
        mock_db
    ):
        """Test query processing using multi-agent system."""
        # Arrange
        request = QueryRequest(**sample_query_request)

        with patch("app.services.query_service.embedding_service") as mock_embed, \
             patch("app.services.query_service.memory_service") as mock_mem, \
             patch("app.services.query_service.get_coordinator") as mock_coord, \
             patch("app.services.query_service.get_db") as mock_get_db:

            # Setup mocks
            mock_embed.generate_embedding = AsyncMock(return_value=sample_embedding)
            mock_mem.get_memory_context = AsyncMock(return_value=sample_memory_context)

            mock_coordinator = AsyncMock()
            mock_coordinator.process = AsyncMock(return_value={
                "response": "Agent processed response",
                "intent": "weather_query",
                "agents_used": ["coordinator", "writer"],
                "citations": None,
                "product_cards": None,
                "product_json": None,
                "options": None,
                "shopping_status": None,
                "tokens": {"total": 100}
            })
            mock_coord.return_value = mock_coordinator

            mock_get_db.return_value = mock_db

            # Act
            service = QueryService()
            response = await service.process_query(request)

            # Assert
            assert isinstance(response, QueryResponse)
            assert response.response == "Agent processed response"
            assert response.intent == "weather_query"
            assert "coordinator" in response.agents_used
            assert response.memory_context == sample_memory_context

            # Verify service calls
            mock_embed.generate_embedding.assert_called_once_with(request.query)
            mock_mem.get_memory_context.assert_called_once()
            mock_coordinator.process.assert_called_once()

    async def test_process_query_with_provider_fallback(
        self,
        sample_query_request,
        sample_embedding,
        sample_memory_context,
        mock_db
    ):
        """Test query processing with direct provider (no agents)."""
        # Arrange
        request = QueryRequest(**sample_query_request)

        with patch("app.services.query_service.embedding_service") as mock_embed, \
             patch("app.services.query_service.memory_service") as mock_mem, \
             patch("app.services.query_service.get_coordinator") as mock_coord, \
             patch("app.services.query_service.ProviderFactory") as mock_factory, \
             patch("app.services.query_service.get_db") as mock_get_db:

            # Setup mocks
            mock_embed.generate_embedding = AsyncMock(return_value=sample_embedding)
            mock_mem.get_memory_context = AsyncMock(return_value=sample_memory_context)
            mock_mem.format_memory_for_prompt = MagicMock(return_value="Memory context")
            mock_coord.return_value = None  # No coordinator available

            mock_provider = AsyncMock()
            mock_provider.generate = AsyncMock(return_value=(
                "Provider response",
                None,  # citations
                {},    # raw_response
                {"total": 50}  # tokens
            ))
            mock_factory.get_provider.return_value = mock_provider

            mock_get_db.return_value = mock_db

            # Act
            service = QueryService()
            response = await service.process_query(request)

            # Assert
            assert isinstance(response, QueryResponse)
            assert response.response == "Provider response"
            assert response.agents_used == []

            # Verify provider was called
            mock_factory.get_provider.assert_called_once_with(request.model_provider)
            mock_provider.generate.assert_called_once()

    async def test_process_query_logs_to_database(
        self,
        sample_query_request,
        sample_embedding,
        sample_memory_context,
        mock_db
    ):
        """Test that queries are logged to database."""
        # Arrange
        request = QueryRequest(**sample_query_request)

        with patch("app.services.query_service.embedding_service") as mock_embed, \
             patch("app.services.query_service.memory_service") as mock_mem, \
             patch("app.services.query_service.get_coordinator") as mock_coord, \
             patch("app.services.query_service.get_db") as mock_get_db:

            # Setup mocks
            mock_embed.generate_embedding = AsyncMock(return_value=sample_embedding)
            mock_mem.get_memory_context = AsyncMock(return_value=sample_memory_context)

            mock_coordinator = AsyncMock()
            mock_coordinator.process = AsyncMock(return_value={
                "response": "Test response",
                "intent": "test",
                "agents_used": ["coordinator"],
                "tokens": {"total": 75}
            })
            mock_coord.return_value = mock_coordinator

            mock_get_db.return_value = mock_db

            # Act
            service = QueryService()
            await service.process_query(request)

            # Assert - verify database insert was called
            mock_db.queries.insert_one.assert_called_once()
            call_args = mock_db.queries.insert_one.call_args[0][0]

            assert call_args["user_id"] == request.user_id
            assert call_args["session_id"] == request.session_id
            assert call_args["query"] == request.query
            assert call_args["response"] == "Test response"
            assert call_args["embedding"] == sample_embedding
            assert "latency_ms" in call_args
            assert call_args["success"] is True

    async def test_process_query_with_memory_integration(
        self,
        sample_query_request,
        sample_embedding,
        mock_db
    ):
        """Test that memory context is properly integrated."""
        # Arrange
        request = QueryRequest(**sample_query_request)
        expected_memory = {
            "similar_queries": [{"query": "Previous query", "response": "Previous response"}],
            "recent_messages": [],
            "summaries": [],
            "total_items": 1
        }

        with patch("app.services.query_service.embedding_service") as mock_embed, \
             patch("app.services.query_service.memory_service") as mock_mem, \
             patch("app.services.query_service.get_coordinator") as mock_coord, \
             patch("app.services.query_service.get_db") as mock_get_db:

            # Setup mocks
            mock_embed.generate_embedding = AsyncMock(return_value=sample_embedding)
            mock_mem.get_memory_context = AsyncMock(return_value=expected_memory)

            mock_coordinator = AsyncMock()
            mock_coordinator.process = AsyncMock(return_value={
                "response": "Response with memory",
                "intent": "test",
                "agents_used": []
            })
            mock_coord.return_value = mock_coordinator

            mock_get_db.return_value = mock_db

            # Act
            service = QueryService()
            response = await service.process_query(request)

            # Assert
            assert response.memory_context == expected_memory

            # Verify memory service was called with correct params
            mock_mem.get_memory_context.assert_called_once_with(
                user_id=request.user_id,
                query=request.query,
                query_embedding=sample_embedding,
                limit=5
            )

    async def test_process_query_handles_errors_gracefully(
        self,
        sample_query_request
    ):
        """Test error handling in query processing."""
        # Arrange
        request = QueryRequest(**sample_query_request)

        with patch("app.services.query_service.embedding_service") as mock_embed:
            # Setup mock to raise an error
            mock_embed.generate_embedding = AsyncMock(side_effect=Exception("Embedding failed"))

            # Act & Assert
            service = QueryService()
            with pytest.raises(Exception) as exc_info:
                await service.process_query(request)

            assert "Embedding failed" in str(exc_info.value)

    async def test_process_with_agents_builds_correct_request(
        self,
        sample_query_request,
        sample_memory_context
    ):
        """Test that agent request is built correctly."""
        # Arrange
        request = QueryRequest(**sample_query_request)

        with patch("app.services.query_service.get_coordinator") as mock_coord:
            mock_coordinator = AsyncMock()
            mock_coordinator.process = AsyncMock(return_value={
                "response": "Test",
                "intent": "test",
                "agents_used": []
            })
            mock_coord.return_value = mock_coordinator

            # Act
            service = QueryService()
            await service._process_with_agents(request, sample_memory_context)

            # Assert - check the agent request structure
            call_args = mock_coordinator.process.call_args[0][0]
            assert call_args["query"] == request.query
            assert call_args["user_id"] == request.user_id
            assert call_args["session_id"] == request.session_id
            assert call_args["model_provider"] == request.model_provider
            assert call_args["memory_context"] == sample_memory_context
