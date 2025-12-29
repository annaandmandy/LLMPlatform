"""
Core module - Configuration, events, and application lifecycle management.
"""

from app.core.config import settings, get_llm_api_key, is_provider_available, get_available_providers
from app.core.events import startup_event, shutdown_event, health_check

__all__ = [
    "settings",
    "get_llm_api_key",
    "is_provider_available",
    "get_available_providers",
    "startup_event",
    "shutdown_event",
    "health_check",
]
