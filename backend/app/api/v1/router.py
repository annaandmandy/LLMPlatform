"""
Main API router aggregator.

Collects all v1 API routes and provides a single router for inclusion in the main app.
"""

from fastapi import APIRouter
from app.api.v1 import health, events, sessions, products, files

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all sub-routers
api_router.include_router(health.router)
api_router.include_router(events.router)
api_router.include_router(sessions.router)
api_router.include_router(products.router)
api_router.include_router(files.router)

# Note: Query router will be added after service layer (Phase 5)

__all__ = ["api_router"]
