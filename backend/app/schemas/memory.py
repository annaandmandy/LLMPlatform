"""
Memory-related schemas.

Contains schemas for memory CRUD operations.
"""

from pydantic import Field
from app.schemas.base import AppBaseModel


class MemoryPayload(AppBaseModel):
    """Schema for creating/updating memories."""
    user_id: str = Field(..., description="User identifier")
    key: str = Field(..., description="Memory key")
    value: str = Field(..., description="Memory value")


class MemoryResponse(AppBaseModel):
    """Response for memory operations."""
    user_id: str
    key: str
    value: str
    status: str = "success"


class ExperimentPayload(AppBaseModel):
    """Schema for experiment-related requests."""
    experiment_id: str = Field(..., description="Experiment identifier")
