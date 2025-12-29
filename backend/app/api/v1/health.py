"""
Health and status check endpoints.
"""

from fastapi import APIRouter, Depends
from app.db.mongodb import get_db, check_connection, get_db_stats
from app.core.events import health_check
from app.core.config import get_available_providers

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "message": "LLM Platform API",
        "version": "2.0.0",
        "status": "running"
    }


@router.get("/status")
async def status():
    """
    Get API status and availability of services.
    
    Returns connection status for database and LLM providers.
    """
    db = get_db() if await check_connection() else None
    
    return {
        "status": "running",
        "mongodb_connected": db is not None,
        "providers_available": {
            provider: True for provider in get_available_providers()
        },
    }


@router.get("/health")
async def health():
    """
    Comprehensive health check.
    
    Returns detailed health information about all system components.
    """
    return await health_check()
