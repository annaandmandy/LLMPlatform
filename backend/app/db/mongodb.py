"""
MongoDB database connection and management.

This module handles async MongoDB connections using Motor.
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.core.config import settings

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection manager."""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    # Collection references (initialized after connection)
    queries_collection = None
    sessions_collection = None
    summaries_collection = None
    products_collection = None
    files_collection = None


# Global instance
mongodb = MongoDB()


async def connect_db() -> AsyncIOMotorDatabase:
    """
    Connect to MongoDB and initialize collections.
    
    Returns:
        AsyncIOMotorDatabase: The connected database instance
        
    Raises:
        ConnectionFailure: If connection to MongoDB fails
    """
    try:
        logger.info("Connecting to MongoDB...")
        
        # Create async client with connection pooling
        mongodb.client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=20000,
        )
        
        # Get database
        mongodb.db = mongodb.client[settings.MONGO_DB]
        
        # Test connection
        await mongodb.client.admin.command('ping')
        logger.info(f"✅ Connected to MongoDB database: {settings.MONGO_DB}")
        
        # Initialize collection references
        _initialize_collections()
        
        # Create indexes
        await _create_indexes()
        
        return mongodb.db
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error connecting to MongoDB: {e}")
        raise


def _initialize_collections():
    """Initialize collection references."""
    if mongodb.db is None:
        logger.warning("Database not connected, skipping collection initialization")
        return
    
    mongodb.queries_collection = mongodb.db["queries"]
    mongodb.sessions_collection = mongodb.db["sessions"]
    mongodb.summaries_collection = mongodb.db["summaries"]
    mongodb.products_collection = mongodb.db["products"]
    mongodb.files_collection = mongodb.db["files"]
    
    logger.info("✅ Collections initialized")


async def _create_indexes():
    """Create database indexes for better query performance."""
    if mongodb.db is None:
        return
    
    try:
        # Queries collection indexes (with embedding for vector search)
        await mongodb.queries_collection.create_index("session_id")
        await mongodb.queries_collection.create_index("user_id")
        await mongodb.queries_collection.create_index([("timestamp", -1)])
        
        # Sessions collection indexes
        await mongodb.sessions_collection.create_index("session_id", unique=True)
        await mongodb.sessions_collection.create_index("user_id")
        await mongodb.sessions_collection.create_index([("start_time", -1)])
        
        # Summaries collection indexes
        await mongodb.summaries_collection.create_index("session_id")
        await mongodb.summaries_collection.create_index("user_id")
        await mongodb.summaries_collection.create_index([("timestamp", -1)])
        
        # Products collection indexes
        await mongodb.products_collection.create_index([("title", "text"), ("description", "text")])
        
        # Files collection indexes
        await mongodb.files_collection.create_index("user_id")
        await mongodb.files_collection.create_index([("upload_time", -1)])
        
        logger.info("✅ Database indexes created")
        
    except Exception as e:
        logger.warning(f"Failed to create some indexes: {e}")


async def close_db():
    """Close MongoDB connection."""
    if mongodb.client:
        mongodb.client.close()
        logger.info("✅ MongoDB connection closed")


def get_db() -> AsyncIOMotorDatabase:
    """
    Dependency function to get database instance.
    
    Returns:
        AsyncIOMotorDatabase: The database instance
        
    Raises:
        RuntimeError: If database is not connected
    """
    if mongodb.db is None:
        raise RuntimeError("Database not connected. Call connect_db() first.")
    return mongodb.db


async def check_connection() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        bool: True if connected, False otherwise
    """
    try:
        if mongodb.client is None:
            return False
        await mongodb.client.admin.command('ping')
        return True
    except Exception:
        return False


async def get_db_stats() -> dict:
    """
    Get database statistics.
    
    Returns:
        dict: Database statistics including collection counts
    """
    if mongodb.db is None:
        return {"connected": False}
    
    try:
        stats = {
            "connected": True,
            "database": settings.MONGO_DB,
            "collections": {}
        }
        
        # Get counts for each collection
        collections = [
            "queries", "events", "sessions", "summaries",
            "vectors", "products", "agent_logs", "memories", "files"
        ]
        
        for coll_name in collections:
            try:
                count = await mongodb.db[coll_name].count_documents({})
                stats["collections"][coll_name] = count
            except Exception:
                stats["collections"][coll_name] = "error"
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get DB stats: {e}")
        return {"connected": True, "error": str(e)}


# Convenience accessors for collections
def get_queries_collection():
    """Get queries collection."""
    return mongodb.queries_collection


def get_sessions_collection():
    """Get sessions collection."""
    return mongodb.sessions_collection


def get_summaries_collection():
    """Get summaries collection."""
    return mongodb.summaries_collection


def get_products_collection():
    """Get products collection."""
    return mongodb.products_collection


def get_files_collection():
    """Get files collection."""
    return mongodb.files_collection
