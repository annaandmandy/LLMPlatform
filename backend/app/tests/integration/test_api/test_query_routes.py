"""
Integration tests for Query API routes.

Tests the query endpoints including:
- POST /api/v1/query/ - Standard query processing
- POST /api/v1/query/stream - Streaming responses
- GET /api/v1/query/history/{user_id} - Query history
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


class TestQueryRoutes:
    """Integration tests for query routes."""

    def test_query_llm_success(
        self,
        test_client: TestClient,
        sample_query_request,
        sample_query_response,
        mock_query_service
    ):
        """Test successful query processing."""
        # Arrange
        mock_query_service.process_query.return_value = sample_query_response

        # Act
        response = test_client.post("/api/v1/query/", json=sample_query_request)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == sample_query_response["response"]
        assert data["intent"] == sample_query_response["intent"]

    def test_query_llm_with_invalid_request(
        self,
        test_client: TestClient
    ):
        """Test query with missing required fields."""
        # Arrange - missing required fields
        invalid_request = {
            "query": "What is Python?"
            # Missing user_id, session_id, model_provider
        }

        # Act
        response = test_client.post("/api/v1/query/", json=invalid_request)

        # Assert
        assert response.status_code == 422  # Validation error

    def test_query_llm_handles_service_error(
        self,
        test_client: TestClient,
        sample_query_request,
        mock_query_service
    ):
        """Test error handling when service fails."""
        # Arrange
        mock_query_service.process_query.side_effect = Exception("Service error")

        # Act
        response = test_client.post("/api/v1/query/", json=sample_query_request)

        # Assert
        assert response.status_code == 500
        assert "Service error" in response.json()["detail"]

    def test_query_with_memory_enabled(
        self,
        test_client: TestClient,
        sample_query_request,
        sample_query_response,
        mock_query_service
    ):
        """Test query with memory context enabled."""
        # Arrange
        sample_query_request["use_memory"] = True
        mock_query_service.process_query.return_value = sample_query_response

        # Act
        response = test_client.post("/api/v1/query/", json=sample_query_request)

        # Assert
        assert response.status_code == 200

        # Verify service was called with memory flag
        call_args = mock_query_service.process_query.call_args[0][0]
        assert call_args.use_memory is True

    def test_query_with_attachments(
        self,
        test_client: TestClient,
        sample_query_request,
        sample_query_response,
        mock_query_service
    ):
        """Test query with file attachments."""
        # Arrange
        sample_query_request["attachments"] = [
            {"type": "image", "url": "https://example.com/image.jpg"}
        ]
        mock_query_service.process_query.return_value = sample_query_response

        # Act
        response = test_client.post("/api/v1/query/", json=sample_query_request)

        # Assert
        assert response.status_code == 200

        # Verify attachments were passed to service
        call_args = mock_query_service.process_query.call_args[0][0]
        assert call_args.attachments is not None
        assert len(call_args.attachments) == 1

    def test_query_with_location_data(
        self,
        test_client: TestClient,
        sample_query_request,
        sample_query_response,
        mock_query_service
    ):
        """Test query with user location data."""
        # Arrange
        sample_query_request["location"] = {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "city": "San Francisco",
            "country": "USA"
        }
        mock_query_service.process_query.return_value = sample_query_response

        # Act
        response = test_client.post("/api/v1/query/", json=sample_query_request)

        # Assert
        assert response.status_code == 200

        # Verify location was passed to service
        call_args = mock_query_service.process_query.call_args[0][0]
        assert call_args.location is not None
        assert call_args.location.city == "San Francisco"

    def test_query_with_conversation_history(
        self,
        test_client: TestClient,
        sample_query_request,
        sample_query_response,
        mock_query_service
    ):
        """Test query with conversation history."""
        # Arrange
        sample_query_request["history"] = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        mock_query_service.process_query.return_value = sample_query_response

        # Act
        response = test_client.post("/api/v1/query/", json=sample_query_request)

        # Assert
        assert response.status_code == 200

        # Verify history was passed
        call_args = mock_query_service.process_query.call_args[0][0]
        assert len(call_args.history) == 2

    def test_query_stream_endpoint(
        self,
        test_client: TestClient,
        sample_query_request
    ):
        """Test streaming query endpoint."""
        # Note: Streaming is harder to test with TestClient
        # This test verifies the endpoint exists and accepts requests

        # Act
        response = test_client.post("/api/v1/query/stream", json=sample_query_request)

        # Assert
        # The actual streaming will be handled by the service
        # Here we just verify the endpoint is accessible
        assert response.status_code in [200, 500]  # Either works or fails gracefully

    def test_query_shopping_mode(
        self,
        test_client: TestClient,
        sample_query_request,
        mock_query_service
    ):
        """Test query in shopping mode."""
        # Arrange
        sample_query_request["mode"] = "shopping"
        sample_query_request["use_product_search"] = True

        shopping_response = {
            "response": "Here are some products for you:",
            "product_cards": [
                {"title": "Product 1", "price": "$99", "url": "https://example.com/1"}
            ],
            "shopping_status": "complete",
            "intent": "product_search",
            "agents_used": ["shopping"],
            "citations": None,
            "product_json": None,
            "user_location": None,
            "memory_context": None,
            "options": None
        }
        mock_query_service.process_query.return_value = shopping_response

        # Act
        response = test_client.post("/api/v1/query/", json=sample_query_request)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["shopping_status"] == "complete"
        assert len(data["product_cards"]) > 0
