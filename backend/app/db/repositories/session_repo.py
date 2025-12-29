"""
Repository for session-related database operations.

Handles storage and retrieval of user sessions, including:
- Session lifecycle management
- Event tracking within sessions
- Session history retrieval
"""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from app.db.repositories.base import BaseRepository


class SessionRepository(BaseRepository):
    """Repository for managing session documents in MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize with sessions collection."""
        super().__init__(db, "sessions")

    async def create_session(
        self,
        session_id: str,
        user_id: str,
        experiment_id: str = "default",
        environment: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new session.

        Args:
            session_id: Unique session identifier
            user_id: User identifier
            experiment_id: Experiment/variant identifier
            environment: Optional environment data (device, browser, etc.)

        Returns:
            ID of created session document
        """
        document = {
            "session_id": session_id,
            "user_id": user_id,
            "experiment_id": experiment_id,
            "environment": environment or {},
            "start_time": datetime.utcnow(),
            "status": "active",
            "events": [],
            "created_at": datetime.utcnow().isoformat(),
        }

        return await self.create(document)

    async def add_event(
        self,
        session_id: str,
        event: Dict[str, Any]
    ) -> int:
        """
        Add an event to a session.

        Args:
            session_id: Session identifier
            event: Event data to append

        Returns:
            Number of documents modified (1 if successful)
        """
        return await self.update_one(
            query={"session_id": session_id},
            update={
                "$push": {"events": event},
                "$set": {"updated_at": datetime.utcnow().isoformat()}
            }
        )

    async def end_session(self, session_id: str) -> int:
        """
        Mark a session as ended.

        Args:
            session_id: Session identifier

        Returns:
            Number of documents modified
        """
        return await self.update_one(
            query={"session_id": session_id},
            update={
                "$set": {
                    "status": "ended",
                    "end_time": datetime.utcnow(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )

    async def get_session(
        self,
        session_id: str,
        include_events: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get session by ID.

        Args:
            session_id: Session identifier
            include_events: Whether to include events array

        Returns:
            Session document or None if not found
        """
        projection = None if include_events else {"events": 0}

        return await self.find_one(
            query={"session_id": session_id},
            projection=projection
        )

    async def get_user_sessions(
        self,
        user_id: str,
        limit: int = 50,
        skip: int = 0,
        include_events: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all sessions for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of sessions to return
            skip: Number of sessions to skip
            include_events: Whether to include events arrays

        Returns:
            List of session documents
        """
        projection = None if include_events else {"events": 0}

        return await self.find_many(
            query={"user_id": user_id},
            sort=[("start_time", -1)],  # Most recent first
            limit=limit,
            skip=skip,
            projection=projection
        )

    async def get_active_sessions(
        self,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all active sessions, optionally filtered by user.

        Args:
            user_id: Optional user filter

        Returns:
            List of active session documents
        """
        query = {"status": "active"}
        if user_id:
            query["user_id"] = user_id

        return await self.find_many(
            query=query,
            sort=[("start_time", -1)],
            projection={"events": 0}  # Exclude events for performance
        )

    async def delete_user_sessions(self, user_id: str) -> int:
        """
        Delete all sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            Number of sessions deleted
        """
        return await self.delete_many({"user_id": user_id})
