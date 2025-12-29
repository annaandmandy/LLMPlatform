"""
Schemas package - Pydantic models for API requests and responses.
"""

from app.schemas.base import AppBaseModel, TimestampMixin, UserIdentifiableMixin
from app.schemas.query import (
    LocationInfo,
    MessageHistory,
    QueryRequest,
    QueryResponse,
    Citation,
    ProductCard,
    QueryDocument,  # NEW: For MongoDB storage with embeddings
)
from app.schemas.session import (
    Environment,
    EventData,
    Event,
    SessionStartRequest,
    SessionEventRequest,
    SessionEndRequest,
    SessionResponse,
)
from app.schemas.event import LogEventRequest, EventResponse
from app.schemas.memory import MemoryPayload, MemoryResponse, ExperimentPayload
from app.schemas.product import ProductSearchRequest, Product, ProductSearchResponse

__all__ = [
    # Base
    "AppBaseModel",
    "TimestampMixin",
    "UserIdentifiableMixin",
    
    # Query
    "LocationInfo",
    "MessageHistory",
    "QueryRequest",
    "QueryResponse",
    "Citation",
    "ProductCard",
    "QueryDocument",
    
    # Session
    "Environment",
    "EventData",
    "Event",
    "SessionStartRequest",
    "SessionEventRequest",
    "SessionEndRequest",
    "SessionResponse",
    
    # Event
    "LogEventRequest",
    "EventResponse",
    
    # Memory
    "MemoryPayload",
    "MemoryResponse",
    "ExperimentPayload",
    
    # Product
    "ProductSearchRequest",
    "Product",
    "ProductSearchResponse",
]
