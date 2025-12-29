"""
Main API router aggregator.

Collects all v1 API routes and provides a single router for inclusion in the main app.
"""

from fastapi import APIRouter
from app.api.v1 import health, events, sessions

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all sub-routers
api_router.include_router(health.router)
api_router.include_router(events.router)
api_router.include_router(sessions.router)

# Note: Other routers will be added as we migrate them:
# - query.router (complex, needs service layer)
# - products.router  
# - memories.router
# - files.router

__all__ = ["api_router"]
