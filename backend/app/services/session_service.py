"""
Session Service - Business logic for session management.

Handles session lifecycle: start, events, end, and retrieval.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.db.mongodb import get_db
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
    
    async def start_session(self, request: SessionStartRequest) -> Dict[str, Any]:
        """
        Start a new user session.
        
        Args:
            request: SessionStartRequest with session details
            
        Returns:
            Dict with session_id and confirmation
        """
        db = get_db()
        if db is None:
            raise RuntimeError("Database not initialized")
        
        sessions_collection = db["sessions"]
        
        # Build session document
        session_doc = {
            "session_id": request.session_id,
            "user_id": request.user_id,
            "experiment_id": request.experiment_id,
            "start_time": datetime.utcnow().isoformat(),
            "environment": request.environment.model_dump(exclude_none=True) if request.environment else None,
            "is_active": True,
            "events": [],  # Empty events list
            "created_at": datetime.utcnow().isoformat(),
        }
        
        try:
            # Insert into database
            await sessions_collection.insert_one(session_doc)
            
            logger.info(f"Session started: {request.session_id} for {request.user_id}")
            
            return {
                "success": True,
                "session_id": request.session_id,
                "message": "Session started successfully",
                "start_time": session_doc["start_time"]
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
        db = get_db()
        if db is None:
            raise RuntimeError("Database not initialized")
        
        sessions_collection = db["sessions"]
        
        # Build event object (use the schema's model_dump to properly format)
        event = request.event.model_dump(exclude_none=True)
        
        try:
            # Add event to session's events array
            result = await sessions_collection.update_one(
                {"session_id": request.session_id},
                {
                    "$push": {"events": event},
                    "$set": {"updated_at": datetime.utcnow().isoformat()}
                }
            )
            
            if result.modified_count == 0:
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
        db = get_db()
        if db is None:
            raise RuntimeError("Database not initialized")
        
        sessions_collection = db["sessions"]
        
        try:
            # Get current session
            session = await sessions_collection.find_one({"session_id": request.session_id})
            
            if not session:
                logger.warning(f"Session not found: {request.session_id}")
                return {
                    "success": False,
                    "message": "Session not found"
                }
            
            # Calculate session duration
            end_time = datetime.utcnow()
            start_time = datetime.fromisoformat(session["start_time"])
            duration_seconds = (end_time - start_time).total_seconds()
            
            # Calculate metrics
            total_events = len(session.get("events", []))
            
            # Update session with end details
            update_data = {
                "end_time": end_time.isoformat(),
                "is_active": False,
                "duration_seconds": duration_seconds,
                "total_events": total_events,
                "updated_at": end_time.isoformat(),
            }
            
            await sessions_collection.update_one(
                {"session_id": request.session_id},
                {"$set": update_data}
            )
            
            logger.info(f"Session ended: {request.session_id} (duration: {duration_seconds:.1f}s, events: {total_events})")
            
            return {
                "success": True,
                "message": "Session ended successfully",
                "session_id": request.session_id,
                "duration_seconds": duration_seconds,
                "total_events": total_events,
                "start_time": session["start_time"],
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
        db = get_db()
        if db is None:
            raise RuntimeError("Database not initialized")
        
        sessions_collection = db["sessions"]
        
        try:
            session = await sessions_collection.find_one({"session_id": session_id})
            
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
        db = get_db()
        if db is None:
            raise RuntimeError("Database not initialized")
        
        sessions_collection = db["sessions"]
        
        # Build query
        query = {"user_id": user_id}
        if active_only:
            query["is_active"] = True
        
        # Fetch sessions
        cursor = sessions_collection.find(query).sort("start_time", -1).limit(limit)
        sessions = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for session in sessions:
            session["_id"] = str(session["_id"])
        
        return sessions


# Global instance
session_service = SessionService()
