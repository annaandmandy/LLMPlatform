"""
Event logging schemas.

Contains schemas for logging user interaction events.
"""

from pydantic import Field
from typing import Optional, Dict, Any
from app.schemas.base import AppBaseModel


class LogEventRequest(AppBaseModel):
    """Request to log a user interaction event (legacy)."""
    user_id: str = Field(..., description="Unique user identifier")
    session_id: str = Field(..., description="Session identifier")
    event_type: str = Field(..., description="Event type (click, scroll, browse, etc.)")
    query: Optional[str] = Field(None, description="Associated query text")
    target_url: Optional[str] = Field(None, description="Target URL (for clicks)")
    page_url: Optional[str] = Field(None, description="Current page URL")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="Additional event data")


class EventResponse(AppBaseModel):
    """Response for event logging."""
    status: str = "success"
    message: str = "Event logged successfully"
