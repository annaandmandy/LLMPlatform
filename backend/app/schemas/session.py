"""
Session-related schemas.

Contains schemas for session management and event tracking.
"""

from pydantic import Field
from typing import Optional, Dict, List, Any
from app.schemas.base import AppBaseModel
from app.schemas.query import LocationInfo


class Environment(AppBaseModel):
    """User environment information."""
    device: str = Field(..., description="Device type")
    browser: str = Field(..., description="Browser name and version")
    os: str = Field(..., description="Operating system")
    viewport: Dict[str, int] = Field(..., description="Viewport dimensions {'width': 1920, 'height': 1080}")
    language: Optional[str] = Field("en", description="User language")
    connection: Optional[str] = Field(None, description="Connection type")
    location: Optional[LocationInfo] = Field(None, description="User location")


class EventData(AppBaseModel):
    """
    Event-specific data fields.
    
    Note: This is for UX analytics, not full Q&A storage.
    Full query/response data lives in the queries collection.
    """
    
    # Generic fields
    text: Optional[str] = None  # Short preview text only
    target: Optional[str] = None
    target_url: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    
    # Scroll-specific
    scrollY: Optional[float] = None
    speed: Optional[float] = None
    direction: Optional[str] = None  # "up" or "down"
    
    # Query/Response tracking (lightweight - reference only!)
    query_id: Optional[str] = None  # Reference to queries collection
    model: Optional[str] = None
    provider: Optional[str] = None
    latency_ms: Optional[float] = None
    success: Optional[bool] = None  # Did the query succeed?
    
    # Tokens (summary only, full data in queries)
    tokens: Optional[Dict[str, int]] = None  # {"total": 60}
    
    # Feedback/error fields
    feedback: Optional[str] = None  # "up", "down", "neutral"
    error_code: Optional[str] = None
    retry_model: Optional[str] = None
    
    # Activity tracking
    activity_state: Optional[str] = None  # "active" or "idle"
    duration_ms: Optional[int] = None
    visible_time_ms: Optional[float] = None
    selected_text: Optional[str] = None
    
    # Navigation/topic tracking
    topic: Optional[str] = None
    sentiment: Optional[str] = None
    page_url: Optional[str] = None


class Event(AppBaseModel):
    """Individual event within a session."""
    t: int = Field(..., description="Timestamp in milliseconds since epoch")
    type: str = Field(..., description="Event type: prompt, model_response, scroll, click, hover, etc.")
    data: EventData = Field(..., description="Event-specific data")
    
    class Config:
        use_enum_values = True
    
    def model_dump(self, **kwargs):
        """Override to exclude None values."""
        kwargs['exclude_none'] = True
        d = super().model_dump(**kwargs)
        # Clean nested data dict
        if 'data' in d and d['data']:
            d['data'] = {k: v for k, v in d['data'].items() if v is not None}
        return d


class SessionStartRequest(AppBaseModel):
    """Request to start a new session."""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="Unique user identifier")
    experiment_id: Optional[str] = Field("default", description="Experiment identifier")
    environment: Environment = Field(..., description="User environment information")


class SessionEventRequest(AppBaseModel):
    """Request to add an event to a session."""
    session_id: str = Field(..., description="Session identifier")
    event: Event = Field(..., description="Event to add")


class SessionEndRequest(AppBaseModel):
    """Request to end a session."""
    session_id: str = Field(..., description="Session identifier")


class SessionResponse(AppBaseModel):
    """Response for session operations."""
    session_id: str
    status: str  # "created", "updated", "ended"
    message: str
