"""
Session management endpoints.

Handles session lifecycle: start, events, end, and retrieval.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Optional

from app.schemas.session import (
    SessionStartRequest,
    SessionEventRequest,
    SessionEndRequest,
    SessionResponse
)
from app.db.mongodb import get_db

router = APIRouter(prefix="/session", tags=["sessions"])


@router.post("/start", response_model=SessionResponse)
async def start_session(request: SessionStartRequest):
    """
    Start a new user session.
    
    Creates a session record with user environment information.
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    sessions_collection = db["sessions"]
    
    # Check if session already exists
    existing = await sessions_collection.find_one({"session_id": request.session_id})
    if existing:
        return SessionResponse(
            session_id=request.session_id,
            status="exists",
            message="Session already exists"
        )
    
    # Create new session
    session_doc = {
        "session_id": request.session_id,
        "user_id": request.user_id,
        "experiment_id": request.experiment_id,
        "environment": request.environment.model_dump(exclude_none=True),
        "start_time": datetime.utcnow(),
        "events": [],
        "status": "active"
    }
    
    await sessions_collection.insert_one(session_doc)
    
    return SessionResponse(
        session_id=request.session_id,
        status="created",
        message="Session started successfully"
    )


@router.post("/event", response_model=SessionResponse)
async def add_session_event(request: SessionEventRequest):
    """
    Add an event to an existing session.
    
    Appends event to the session's event array.
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    sessions_collection = db["sessions"]
    
    # Check if session exists
    session = await sessions_collection.find_one({"session_id": request.session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Add event to session
    event_doc = request.event.model_dump(exclude_none=True)
    
    await sessions_collection.update_one(
        {"session_id": request.session_id},
        {
            "$push": {"events": event_doc},
            "$set": {"last_activity": datetime.utcnow()}
        }
    )
    
    return SessionResponse(
        session_id=request.session_id,
        status="updated",
        message="Event added successfully"
    )


@router.post("/end", response_model=SessionResponse)
async def end_session(request: SessionEndRequest):
    """
    End a session.
    
    Marks the session as ended and records end time.
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    sessions_collection = db["sessions"]
    
    # Check if session exists
    session = await sessions_collection.find_one({"session_id": request.session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update session status
    await sessions_collection.update_one(
        {"session_id": request.session_id},
        {
            "$set": {
                "status": "ended",
                "end_time": datetime.utcnow()
            }
        }
    )
    
    return SessionResponse(
        session_id=request.session_id,
        status="ended",
        message="Session ended successfully"
    )


@router.get("/{session_id}")
async def get_session(session_id: str, include_events: Optional[bool] = False):
    """
    Retrieve session data.
    
    Args:
        session_id: Session identifier
        include_events: Whether to include event array (can be large)
        
    Returns:
        Session data with optional events
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    sessions_collection = db["sessions"]
    
    # Build projection based on include_events
    projection = {"_id": 0}
    if not include_events:
        projection["events"] = 0
    
    session = await sessions_collection.find_one(
        {"session_id": session_id},
        projection
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@router.get("/{session_id}/experiment")
async def get_session_experiment(session_id: str):
    """
    Get experiment configuration for a session.
    
    Returns experiment_id and any experiment-related metadata.
    Used by frontend to restore experiment state.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Experiment configuration data
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    sessions_collection = db["sessions"]
    
    session = await sessions_collection.find_one(
        {"session_id": session_id},
        {"_id": 0, "experiment_id": 1, "model_group": 1, "environment": 1}
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "experiment_id": session.get("experiment_id"),
        "model_group": session.get("environment", {}).get("model_group"),
        "environment": session.get("environment", {})
    }


@router.post("/{session_id}/experiment")
async def update_session_experiment(session_id: str, experiment_data: dict):
    """
    Update experiment configuration for a session.
    
    Allows updating experiment_id and related metadata after session creation.
    Useful for A/B testing and experiment tracking.
    
    Args:
        session_id: Session identifier
        experiment_data: Experiment configuration updates
        
    Returns:
        Success status
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    sessions_collection = db["sessions"]
    
    # Build update document
    update_doc = {}
    if "experiment_id" in experiment_data:
        update_doc["experiment_id"] = experiment_data["experiment_id"]
    if "model_group" in experiment_data:
        update_doc["environment.model_group"] = experiment_data["model_group"]
    
    if not update_doc:
        raise HTTPException(status_code=400, detail="No valid experiment data provided")
    
    result = await sessions_collection.update_one(
        {"session_id": session_id},
        {"$set": update_doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "success": True,
        "session_id": session_id,
        "updated": True
    }
