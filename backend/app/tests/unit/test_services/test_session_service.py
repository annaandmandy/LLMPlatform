"""
Unit tests for SessionService.

Tests session lifecycle management including:
- Starting sessions
- Adding events
- Ending sessions
- Retrieving session data
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.session_service import SessionService, session_service
from app.schemas.session import SessionStartRequest, SessionEventRequest, SessionEndRequest, Event, EventData


@pytest.mark.asyncio
class TestSessionService:
    """Test suite for SessionService."""

    @pytest.fixture(autouse=True)
    def reset_service_cache(self):
        """Reset the global service's repository cache before each test."""
        session_service._repo = None
        yield
        session_service._repo = None

    async def test_start_session_success(
        self,
        sample_session_start_request,
        mock_db
    ):
        """Test successful session creation."""
        # Arrange
        request = SessionStartRequest(**sample_session_start_request)

        with patch("app.services.session_service.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db

            # Act
            result = await session_service.start_session(request)

            # Assert
            assert result["success"] is True
            assert result["session_id"] == request.session_id
            assert "start_time" in result

            # Verify database insert (via repository)
            mock_db.sessions.insert_one.assert_called_once()
            call_args = mock_db.sessions.insert_one.call_args[0][0]
            assert call_args["session_id"] == request.session_id
            assert call_args["user_id"] == request.user_id
            assert call_args["status"] == "active"  # Repository uses status field
            assert call_args["events"] == []

    async def test_start_session_without_database(
        self,
        sample_session_start_request
    ):
        """Test session start fails without database."""
        # Arrange
        request = SessionStartRequest(**sample_session_start_request)

        with patch("app.services.session_service.get_db") as mock_get_db:
            mock_get_db.return_value = None

            # Create a fresh service instance to avoid cached repo
            from app.services.session_service import SessionService
            fresh_service = SessionService()

            # Act & Assert
            with pytest.raises(RuntimeError, match="Database not initialized"):
                await fresh_service.start_session(request)

    async def test_add_event_success(
        self,
        sample_event,
        mock_db
    ):
        """Test successfully adding event to session."""
        # Arrange
        event = Event(**sample_event)
        request = SessionEventRequest(session_id="test_session_789", event=event)

        with patch("app.services.session_service.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db
            mock_db.sessions.update_one.return_value = MagicMock(modified_count=1)

            # Act
            result = await session_service.add_event(request)

            # Assert
            assert result["success"] is True
            assert result["session_id"] == "test_session_789"

            # Verify database update
            mock_db.sessions.update_one.assert_called_once()
            call_args = mock_db.sessions.update_one.call_args

            # Check filter
            assert call_args[0][0] == {"session_id": "test_session_789"}

            # Check update operation
            update_op = call_args[0][1]
            assert "$push" in update_op
            assert "events" in update_op["$push"]
            assert "$set" in update_op
            assert "updated_at" in update_op["$set"]

    async def test_add_event_to_nonexistent_session(
        self,
        sample_event,
        mock_db
    ):
        """Test adding event to non-existent session."""
        # Arrange
        event = Event(**sample_event)
        request = SessionEventRequest(session_id="nonexistent_session", event=event)

        with patch("app.services.session_service.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db
            mock_db.sessions.update_one.return_value = MagicMock(modified_count=0)

            # Act
            result = await session_service.add_event(request)

            # Assert
            assert result["success"] is False
            assert "not found" in result["message"].lower()

    async def test_end_session_success(
        self,
        mock_db
    ):
        """Test successfully ending a session."""
        # Arrange
        session_id = "test_session_789"
        request = SessionEndRequest(session_id=session_id)

        # Mock existing session
        existing_session = {
            "session_id": session_id,
            "user_id": "test_user_123",
            "start_time": "2025-12-29T10:00:00",
            "is_active": True,
            "events": [
                {"t": 1000, "type": "prompt", "data": {}},
                {"t": 2000, "type": "model_response", "data": {}}
            ]
        }

        with patch("app.services.session_service.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db
            mock_db.sessions.find_one.return_value = existing_session
            mock_db.sessions.update_one.return_value = MagicMock(modified_count=1)

            # Act
            result = await session_service.end_session(request)

            # Assert
            assert result["success"] is True
            assert result["session_id"] == session_id
            assert "duration_seconds" in result
            assert result["total_events"] == 2
            assert "start_time" in result
            assert "end_time" in result

            # Verify database update (via repository)
            mock_db.sessions.update_one.assert_called_once()
            call_args = mock_db.sessions.update_one.call_args[0][1]["$set"]
            assert call_args["status"] == "ended"  # Repository uses status field
            assert "end_time" in call_args
            assert "updated_at" in call_args

    async def test_end_session_not_found(
        self,
        mock_db
    ):
        """Test ending non-existent session."""
        # Arrange
        request = SessionEndRequest(session_id="nonexistent_session")

        with patch("app.services.session_service.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db
            mock_db.sessions.find_one.return_value = None

            # Act
            result = await session_service.end_session(request)

            # Assert
            assert result["success"] is False
            assert "not found" in result["message"].lower()

    async def test_get_session_success(
        self,
        mock_db
    ):
        """Test retrieving session by ID."""
        # Arrange
        session_id = "test_session_789"
        session_data = {
            "_id": "mock_object_id",
            "session_id": session_id,
            "user_id": "test_user_123",
            "start_time": "2025-12-29T10:00:00",
            "is_active": True
        }

        with patch("app.services.session_service.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db
            mock_db.sessions.find_one.return_value = session_data

            # Act
            result = await session_service.get_session(session_id)

            # Assert
            assert result is not None
            assert result["session_id"] == session_id
            assert result["_id"] == "mock_object_id"  # Should be converted to string

            # Verify database query (repository may add projection parameter)
            mock_db.sessions.find_one.assert_called_once()
            call_args = mock_db.sessions.find_one.call_args[0]
            assert call_args[0] == {"session_id": session_id}

    async def test_get_session_not_found(
        self,
        mock_db
    ):
        """Test retrieving non-existent session."""
        # Arrange
        with patch("app.services.session_service.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db
            mock_db.sessions.find_one.return_value = None

            # Act
            result = await session_service.get_session("nonexistent_session")

            # Assert
            assert result is None

    async def test_get_user_sessions(
        self,
        mock_db
    ):
        """Test retrieving all sessions for a user."""
        # Arrange
        user_id = "test_user_123"
        sessions_data = [
            {"_id": "id1", "session_id": "session1", "user_id": user_id, "is_active": True},
            {"_id": "id2", "session_id": "session2", "user_id": user_id, "is_active": False}
        ]

        with patch("app.services.session_service.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db

            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.limit.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=sessions_data)
            mock_db.sessions.find.return_value = mock_cursor

            # Act
            result = await session_service.get_user_sessions(user_id)

            # Assert
            assert len(result) == 2
            assert all(s["_id"] in ["id1", "id2"] for s in result)

            # Verify query (repository may add projection parameter)
            mock_db.sessions.find.assert_called_once()
            call_args = mock_db.sessions.find.call_args[0]
            assert call_args[0]["user_id"] == user_id

    async def test_get_user_sessions_active_only(
        self,
        mock_db
    ):
        """Test retrieving only active sessions for a user."""
        # Arrange
        user_id = "test_user_123"
        sessions_data = [
            {"_id": "id1", "session_id": "session1", "user_id": user_id, "is_active": True}
        ]

        with patch("app.services.session_service.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db

            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.limit.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=sessions_data)
            mock_db.sessions.find.return_value = mock_cursor

            # Act
            await session_service.get_user_sessions(user_id, active_only=True)

            # Assert - verify query includes status filter (repository uses status field)
            call_args = mock_db.sessions.find.call_args[0][0]
            assert call_args["user_id"] == user_id
            assert call_args["status"] == "active"

    async def test_get_user_sessions_with_limit(
        self,
        mock_db
    ):
        """Test that session retrieval respects limit."""
        # Arrange
        user_id = "test_user_123"

        with patch("app.services.session_service.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db

            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.limit.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=[])
            mock_db.sessions.find.return_value = mock_cursor

            # Act
            await session_service.get_user_sessions(user_id, limit=10)

            # Assert
            mock_cursor.limit.assert_called_with(10)
