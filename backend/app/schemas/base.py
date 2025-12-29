"""
Base schemas for the application.

Contains common base classes and mixins used across all schemas.
"""

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional


class AppBaseModel(BaseModel):
    """
    Base model for all application schemas.
    
    Disables protected_namespaces to allow 'model_' prefixed fields
    (e.g., model_provider, model_name) which are common in LLM applications.
    """
    model_config = ConfigDict(protected_namespaces=())


class TimestampMixin(AppBaseModel):
    """Mixin for models that need timestamp fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserIdentifiableMixin(AppBaseModel):
    """Mixin for models that need user and session identification."""
    user_id: str = Field(..., description="Unique identifier for the user")
    session_id: str = Field(..., description="Unique identifier for the session")
