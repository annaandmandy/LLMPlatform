"""
Session Service - Business logic for session management.

Handles session lifecycle: start, events, end, and retrieval.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.db.mongodb import get_db
from app.db.repositories.session_repo import SessionRepository
from app.schemas.session import (
    SessionStartRequest,
    SessionEventRequest,
    SessionEndRequest
)

logger = logging.getLogger(__name__)


class SessionService:
    """
    Service for managing user sessions.

    Handles the full session lifecycle:
    1. Start session (creates session document)
    2. Log events (adds events to session)
    3. End session (marks session complete, calculates metrics)
    4. Retrieve session data
    """

    def __init__(self):
        """Initialize with repository."""
        self._repo = None

    @property
    def repo(self) -> SessionRepository:
        """Get repository instance (lazy initialization)."""
        if self._repo is None:
            db = get_db()
            if db is None:
                raise RuntimeError("Database not initialized")
            self._repo = SessionRepository(db)
        return self._repo

    async def start_session(self, request: SessionStartRequest) -> Dict[str, Any]:
        """
        Start a new user session.

        Args:
            request: SessionStartRequest with session details

        Returns:
            Dict with session_id and confirmation
        """
        try:
            start_time = datetime.utcnow().isoformat()

            # Use repository to create session
            await self.repo.create_session(
                session_id=request.session_id,
                user_id=request.user_id,
                experiment_id=request.experiment_id,
                environment=request.environment.model_dump(exclude_none=True) if request.environment else None
            )

            logger.info(f"Session started: {request.session_id} for {request.user_id}")

            return {
                "success": True,
                "session_id": request.session_id,
                "message": "Session started successfully",
                "start_time": start_time
            }

        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            raise
    
    async def add_event(self, request: SessionEventRequest) -> Dict[str, Any]:
        """
        Add an event to an existing session.

        Args:
            request: SessionEventRequest with event details

        Returns:
            Dict with confirmation
        """
        # Build event object (use the schema's model_dump to properly format)
        event = request.event.model_dump(exclude_none=True)

        try:
            # Use repository to add event
            modified_count = await self.repo.add_event(
                session_id=request.session_id,
                event=event
            )

            if modified_count == 0:
                logger.warning(f"Session not found: {request.session_id}")
                return {
                    "success": False,
                    "message": "Session not found"
                }

            logger.info(f"Event added to session: {request.session_id}")

            return {
                "success": True,
                "message": "Event added successfully",
                "session_id": request.session_id
            }

        except Exception as e:
            logger.error(f"Failed to add event: {e}")
            raise
    
    async def end_session(self, request: SessionEndRequest) -> Dict[str, Any]:
        """
        End a session and calculate final metrics.

        Args:
            request: SessionEndRequest with session_id

        Returns:
            Dict with session summary
        """
        try:
            # Get current session to calculate metrics
            session = await self.repo.get_session(
                session_id=request.session_id,
                include_events=True
            )

            if not session:
                logger.warning(f"Session not found: {request.session_id}")
                return {
                    "success": False,
                    "message": "Session not found"
                }

            # Calculate session duration
            end_time = datetime.utcnow()
            start_time = datetime.fromisoformat(session["start_time"]) if isinstance(session["start_time"], str) else session["start_time"]
            duration_seconds = (end_time - start_time).total_seconds()

            # Calculate metrics
            total_events = len(session.get("events", []))

            # Use repository to end session
            await self.repo.end_session(request.session_id)

            logger.info(f"Session ended: {request.session_id} (duration: {duration_seconds:.1f}s, events: {total_events})")

            return {
                "success": True,
                "message": "Session ended successfully",
                "session_id": request.session_id,
                "duration_seconds": duration_seconds,
                "total_events": total_events,
                "start_time": session["start_time"] if isinstance(session["start_time"], str) else session["start_time"].isoformat(),
                "end_time": end_time.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to end session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session document or None if not found
        """
        try:
            session = await self.repo.get_session(
                session_id=session_id,
                include_events=True
            )

            if session:
                session["_id"] = str(session["_id"])
                return session

            return None

        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None

    async def get_user_sessions(
        self,
        user_id: str,
        active_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all sessions for a user.

        Args:
            user_id: User ID to filter by
            active_only: If True, only return active sessions
            limit: Maximum number of sessions to return

        Returns:
            List of session documents
        """
        # Use repository based on active_only flag
        if active_only:
            sessions = await self.repo.get_active_sessions(user_id=user_id)
            # Apply limit
            sessions = sessions[:limit]
        else:
            sessions = await self.repo.get_user_sessions(
                user_id=user_id,
                limit=limit,
                include_events=False
            )

        # Convert ObjectId to string
        for session in sessions:
            session["_id"] = str(session["_id"])

        return sessions


# Global instance
session_service = SessionService()
