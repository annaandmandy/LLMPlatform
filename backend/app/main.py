"""
FastAPI Application - Main Entry Point (Refactored)

This is the new, simplified main application file.
The old monolithic main.py has been refactored into modular components.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.events import startup_event, shutdown_event
from app.api.v1.router import api_router

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="LLM Platform API - Refactored Architecture"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lifecycle events
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

# Include API routes
app.include_router(api_router)

# Root endpoint (for backward compatibility)
@app.get("/")
async def root():
    """Root endpoint - redirects to API v1."""
    return {
        "message": "LLM Platform API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api": "/api/v1"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
