"""
Query-related schemas.

Contains request and response schemas for LLM query endpoints.
"""

from pydantic import Field
from typing import Optional, List, Dict, Any
from app.schemas.base import AppBaseModel


class LocationInfo(AppBaseModel):
    """User location information."""
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    accuracy: Optional[float] = Field(None, description="Location accuracy in meters")
    city: Optional[str] = Field(None, description="City name")
    region: Optional[str] = Field(None, description="Region/state name")
    country: Optional[str] = Field(None, description="Country name")


class MessageHistory(AppBaseModel):
    """Message in conversation history."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class QueryRequest(AppBaseModel):
    """Request schema for querying LLM."""
    user_id: str = Field(..., description="Unique user identifier")
    session_id: str = Field(..., description="Unique session identifier")
    query: str = Field(..., description="User query text")
    model_provider: str = Field(..., description="LLM provider: 'openai', 'anthropic', 'google', or 'openrouter'")
    model_name: Optional[str] = Field(None, description="Specific model name (e.g., 'gpt-4o-mini')")
    web_search: Optional[bool] = Field(False, description="Enable web search")
    use_memory: Optional[bool] = Field(False, description="Use conversation memory/RAG")
    use_product_search: Optional[bool] = Field(False, description="Enable product search")
    history: Optional[List[MessageHistory]] = Field(default_factory=list, description="Conversation history")
    location: Optional[LocationInfo] = Field(None, description="User location data")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="File attachments (images, etc.)")
    mode: Optional[str] = Field("chat", description="Interaction mode: 'chat' or 'shopping'")


class QueryResponse(AppBaseModel):
    """Response schema for LLM query."""
    response: str = Field(..., description="Generated response text")
    citations: Optional[List[Dict[str, Any]]] = Field(None, description="Source citations")
    product_cards: Optional[List[Dict[str, Any]]] = Field(None, description="Product recommendation cards")
    product_json: Optional[List[Dict[str, Any]]] = Field(None, description="Structured product data")
    need_memory: Optional[bool] = Field(None, description="Whether memory was used")
    memory_reason: Optional[str] = Field(None, description="Reason for memory usage")
    user_location: Optional[LocationInfo] = Field(None, description="User location used")
    memory_context: Optional[Dict[str, Any]] = Field(None, description="Retrieved memory context")
    intent: Optional[str] = Field(None, description="Detected user intent")
    agents_used: Optional[List[str]] = Field(None, description="Agents that processed the request")
    options: Optional[List[Dict[str, Any]]] = Field(None, description="Shopping mode options")
    
    # For shopping mode
    shopping_status: Optional[str] = Field(None, description="Shopping flow status: 'question' or 'complete'")


class Citation(AppBaseModel):
    """Source citation."""
    title: str = Field(..., description="Citation title")
    url: str = Field(..., description="Citation URL")
    snippet: Optional[str] = Field(None, description="Text snippet")
    content: Optional[str] = Field(None, description="Full content preview")


class ProductCard(AppBaseModel):
    """Product recommendation card."""
    title: str
    description: str
    image_url: Optional[str] = None
    price: Optional[str] = None
    rating: Optional[float] = None
    url: str
