"""
Event logging endpoints.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.schemas.event import LogEventRequest, EventResponse
from app.db.mongodb import get_db

router = APIRouter(prefix="/log_event", tags=["events"])


@router.post("/", response_model=EventResponse)
async def log_event(request: LogEventRequest):
    """
    Log a user interaction event (legacy endpoint).
    
    This is a simplified event logging endpoint for backward compatibility.
    For richer event tracking, use the session-based events API.
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    events_collection = db["events"]
    
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
        message="Event logged successfully"
    )
