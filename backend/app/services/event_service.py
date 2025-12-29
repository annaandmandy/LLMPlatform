"""
Event Service - DEPRECATED

⚠️ NOTE: This service is DEPRECATED and kept only for backward compatibility.

Events are now stored within session documents (in the sessions collection),
not as standalone documents. 

Use SessionService.add_event() instead for new code.

The standalone 'events' collection was removed to avoid data duplication.
All event data is now part of the session lifecycle tracking.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.db.mongodb import get_db
from app.schemas.event import LogEventRequest

logger = logging.getLogger(__name__)


class EventService:
    """
    DEPRECATED: Use SessionService instead.
    
    This service provides backward compatibility for the legacy /log_event endpoint.
    It creates standalone event documents, but this is not the recommended approach.
    """
    
    async def log_event(self, event: LogEventRequest) -> Dict[str, Any]:
        """
        Log a user event to the database (DEPRECATED).
        
        ⚠️ WARNING: This creates standalone event documents which are NOT 
        integrated with the session lifecycle. Use SessionService.add_event() instead.
        
        Args:
            event: LogEventRequest with event details
            
        Returns:
            Dict with success status and event_id
        """
        logger.warning("EventService.log_event() is deprecated. Use SessionService.add_event() instead.")
        
        db = get_db()
        if db is None:
            raise RuntimeError("Database not initialized")
        
        # Note: Using 'events_legacy' collection to avoid confusion
        # This can be dropped once all clients migrate to session- based events
        events_collection = db["events_legacy"]
        
        # Build event document
        event_doc = {
            "user_id": event.user_id,
            "session_id": event.session_id,
            "event_type": event.event_type,
            "event_data": event.event_data or {},
            "timestamp": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
        }
        
        try:
            # Insert into database
            result = await events_collection.insert_one(event_doc)
            event_id = str(result.inserted_id)
            
            logger.info(f"[DEPRECATED] Event logged: {event.event_type} for {event.user_id}")
            
            return {
                "success": True,
                "event_id": event_id,
                "message": "Event logged successfully (legacy mode)"
            }
            
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
            raise


# Global instance
event_service = EventService()
