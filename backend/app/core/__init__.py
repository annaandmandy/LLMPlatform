"""
Core module - Configuration, events, and application lifecycle management.
"""

from app.core.config import settings, get_llm_api_key, is_provider_available, get_available_providers

# Note: startup_event, shutdown_event, health_check should be imported directly from app.core.events
# to avoid circular imports with db.mongodb

__all__ = [
    "settings",
    "get_llm_api_key",
    "is_provider_available",
    "get_available_providers",
]
