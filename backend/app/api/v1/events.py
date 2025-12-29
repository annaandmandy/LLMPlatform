"""
Event logging endpoints.

⚠️ DEPRECATED: This endpoint is kept for backward compatibility only.
Use session-based event tracking instead (/api/v1/session/event).
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

from app.schemas.event import LogEventRequest, EventResponse
from app.db.mongodb import get_db

router = APIRouter(prefix="/log_event", tags=["events"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=EventResponse)
async def log_event(request: LogEventRequest):
    """
    Log a user interaction event (DEPRECATED - legacy endpoint).
    
    ⚠️ WARNING: This endpoint is deprecated. Use session-based events instead:
       POST /api/v1/session/event
    
    This endpoint creates standalone event documents which are NOT integrated
    with session lifecycles. For proper event tracking, use the session API.
    """
    logger.warning(f"Legacy event endpoint used by user {request.user_id}. Migrate to session-based events.")
    
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Use events_legacy collection to avoid confusion with session events
    events_collection = db["events_legacy"]
    
    event_doc = {
        "user_id": request.user_id,
        "session_id": request.session_id,
        "event_type": request.event_type,
        "query": request.query,
        "target_url": request.target_url,
        "page_url": request.page_url,
        "extra_data": request.extra_data,
        "timestamp": datetime.utcnow()
    }
    
    await events_collection.insert_one(event_doc)
    
    return EventResponse(
        status="success",
        message="Event logged successfully (legacy mode - please migrate to session events)"
    )
