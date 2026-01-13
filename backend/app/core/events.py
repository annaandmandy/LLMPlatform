"""
Application startup and shutdown event handlers.

This module manages the lifecycle of the FastAPI application.
"""

import logging
from pathlib import Path

from app.core.config import settings
from app.db.mongodb import connect_db, close_db, mongodb

logger = logging.getLogger(__name__)


async def startup_event():
    """
    Execute on application startup.
    
    Responsibilities:
    - Connect to MongoDB
    - Initialize agents
    - Create necessary directories
    - Perform health checks
    """
    logger.info("🚀 Starting application...")
    
    # Create necessary directories
    try:
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        if settings.LOG_FILE:
            settings.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        logger.info("✅ Directories created")
    except Exception as e:
        logger.warning(f"Unable to create directories: {e}")
    
    # Connect to MongoDB
    try:
        db = await connect_db()
        logger.info("✅ Database connected")
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        logger.warning("⚠️ Application will run without database")
        return
    
    # Initialize multi-agent system
    try:
        await initialize_agents(db)
        logger.info("✅ Multi-agent system initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize agents: {e}")
        logger.warning("⚠️ Multi-agent features may not work")
    
    # Initialize Experiment Service (Graph Factory)
    from app.services.experiment_service import experiment_service
    await experiment_service.initialize()
    
    logger.info("✅ Application startup complete")


async def shutdown_event():
    """
    Execute on application shutdown.
    
    Responsibilities:
    - Close database connections
    - Cleanup resources
    - Log shutdown
    """
    logger.info("👋 Shutting down application...")
    
    # Close database connection
    await close_db()
    
    # Cleanup other resources if needed
    # (e.g., close Redis connections, HTTP clients, etc.)
    
    logger.info("✅ Application shutdown complete")


async def initialize_agents(db):
    """
    Initialize the multi-agent system.
    
    This is a wrapper that delegates to the agents module.
    
    Args:
        db: MongoDB database instance
    """
    from app.agents import initialize_agents as init_agents
    return await init_agents(db)


# Health check helper
async def health_check() -> dict:
    """
    Perform application health check.
    
    Returns:
        dict: Health status of various components
    """
    from app.db.mongodb import check_connection, get_db_stats
    from app.core.config import get_available_providers
    
    # Check database
    db_connected = await check_connection()
    db_stats = await get_db_stats() if db_connected else {}
    
    # Check providers
    available_providers = get_available_providers()
    
    # Check agents
    from app.agents import are_agents_initialized
    agents_initialized = are_agents_initialized()
    
    health_status = {
        "status": "healthy" if db_connected else "degraded",
        "database": {
            "connected": db_connected,
            "stats": db_stats
        },
        "providers": {
            "available": available_providers,
            "count": len(available_providers)
        },
        "agents": {
            "initialized": agents_initialized
        },
        "config": {
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "version": settings.APP_VERSION
        }
    }
    
    return health_status
