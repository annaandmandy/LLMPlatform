"""
Integration tests for Session API routes.

Tests the session management endpoints including:
- POST /api/v1/session/start - Start session
- POST /api/v1/session/event - Add event
- POST /api/v1/session/end - End session
- GET /api/v1/session/{id} - Get session
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


class TestSessionRoutes:
    """Integration tests for session routes."""

    def test_start_session_success(
        self,
        test_client: TestClient,
        sample_session_start_request
    ):
        """Test successful session creation."""
        # Act
        response = test_client.post("/api/v1/session/start", json=sample_session_start_request)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert data["session_id"] == sample_session_start_request["session_id"]
        assert data["message"] == "Session started successfully"

    def test_start_session_with_invalid_request(
        self,
        test_client: TestClient
    ):
        """Test session start with missing required fields."""
        # Arrange
        invalid_request = {
            "session_id": "test_session_123"
            # Missing user_id and environment
        }

        # Act
        response = test_client.post("/api/v1/session/start", json=invalid_request)

        # Assert
        assert response.status_code == 422  # Validation error

    def test_add_event_to_session(
        self,
        test_client: TestClient,
        sample_event,
        sample_session_start_request
    ):
        """Test adding an event to a session."""
        # Arrange - First create a session
        test_client.post("/api/v1/session/start", json=sample_session_start_request)

        request_data = {
            "session_id": sample_session_start_request["session_id"],
            "event": sample_event
        }

        # Act
        response = test_client.post("/api/v1/session/event", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert data["message"] == "Event added successfully"

    def test_add_event_with_invalid_event_data(
        self,
        test_client: TestClient
    ):
        """Test adding event with invalid structure."""
        # Arrange
        invalid_request = {
            "session_id": "test_session_789",
            "event": {
                # Missing required fields like 't' and 'type'
                "data": {}
            }
        }

        # Act
        response = test_client.post("/api/v1/session/event", json=invalid_request)

        # Assert
        assert response.status_code == 422

    def test_end_session_success(
        self,
        test_client: TestClient,
        sample_session_start_request
    ):
        """Test successfully ending a session."""
        # Arrange - First create a session
        test_client.post("/api/v1/session/start", json=sample_session_start_request)

        request_data = {
            "session_id": sample_session_start_request["session_id"]
        }

        # Act
        response = test_client.post("/api/v1/session/end", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ended"
        assert data["message"] == "Session ended successfully"
        assert data["session_id"] == sample_session_start_request["session_id"]

    def test_end_nonexistent_session(
        self,
        test_client: TestClient
    ):
        """Test ending a session that doesn't exist."""
        # Arrange
        request_data = {
            "session_id": "nonexistent_session"
        }

        # Act
        response = test_client.post("/api/v1/session/end", json=request_data)

        # Assert
        assert response.status_code == 404  # Session not found

    def test_get_session_by_id(
        self,
        test_client: TestClient,
        sample_session_start_request
    ):
        """Test retrieving session by ID."""
        # Arrange - First create a session
        test_client.post("/api/v1/session/start", json=sample_session_start_request)
        session_id = sample_session_start_request["session_id"]

        # Act
        response = test_client.get(f"/api/v1/session/{session_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["status"] == "active"

    def test_get_nonexistent_session(
        self,
        test_client: TestClient
    ):
        """Test retrieving a session that doesn't exist."""
        # Act
        response = test_client.get("/api/v1/session/nonexistent_session")

        # Assert
        assert response.status_code == 404

    def test_session_lifecycle_flow(
        self,
        test_client: TestClient,
        sample_session_start_request,
        sample_event
    ):
        """Test complete session lifecycle: start -> add events -> end."""
        # Arrange
        session_id = sample_session_start_request["session_id"]

        # Act - Start session
        start_response = test_client.post("/api/v1/session/start", json=sample_session_start_request)
        assert start_response.status_code == 200
        assert start_response.json()["status"] == "created"

        # Act - Add event
        event_request = {
            "session_id": session_id,
            "event": sample_event
        }
        event_response = test_client.post("/api/v1/session/event", json=event_request)
        assert event_response.status_code == 200
        assert event_response.json()["status"] == "updated"

        # Act - End session
        end_request = {"session_id": session_id}
        end_response = test_client.post("/api/v1/session/end", json=end_request)

        # Assert
        assert end_response.status_code == 200
        data = end_response.json()
        assert data["status"] == "ended"
        assert data["session_id"] == session_id

    def test_add_multiple_events_to_session(
        self,
        test_client: TestClient,
        sample_event,
        sample_session_start_request
    ):
        """Test adding multiple events to the same session."""
        # Arrange - First create a session
        test_client.post("/api/v1/session/start", json=sample_session_start_request)
        session_id = sample_session_start_request["session_id"]

        # Act - Add multiple events
        for i in range(3):
            event_data = sample_event.copy()
            event_data["t"] = 1000 + (i * 100)
            event_data["type"] = f"event_type_{i}"

            request = {
                "session_id": session_id,
                "event": event_data
            }

            response = test_client.post("/api/v1/session/event", json=request)

            # Assert each succeeds
            assert response.status_code == 200
            assert response.json()["status"] == "updated"
