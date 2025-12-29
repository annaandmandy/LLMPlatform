"""
Repository for memory-related database operations.

Handles storage and retrieval of conversation memories, including:
- Vector similarity search for relevant context
- Memory storage with embeddings
- Memory cleanup and management
"""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from app.db.repositories.base import BaseRepository


class MemoryRepository(BaseRepository):
    """Repository for managing memory documents in MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize with queries collection (memories stored as queries)."""
        super().__init__(db, "queries")

    async def store_memory(
        self,
        user_id: str,
        query: str,
        response: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a conversation turn as memory.

        Args:
            user_id: User identifier
            query: User's query text
            response: Assistant's response text
            embedding: Query embedding vector
            metadata: Optional additional metadata

        Returns:
            ID of created memory document
        """
        document = {
            "user_id": user_id,
            "query": query,
            "response": response,
            "embedding": embedding,
            "timestamp": datetime.utcnow(),
            "created_at": datetime.utcnow().isoformat(),
        }

        if metadata:
            document.update(metadata)

        return await self.create(document)

    async def get_recent_memories(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversation memories for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of memories to return

        Returns:
            List of memory documents
        """
        return await self.find_many(
            query={"user_id": user_id},
            sort=[("timestamp", -1)],
            limit=limit,
            projection={"embedding": 0}  # Exclude embeddings for performance
        )

    async def delete_old_memories(
        self,
        user_id: str,
        days: int = 30
    ) -> int:
        """
        Delete memories older than specified days.

        Args:
            user_id: User identifier
            days: Number of days to keep

        Returns:
            Number of memories deleted
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        return await self.delete_many({
            "user_id": user_id,
            "timestamp": {"$lt": cutoff_date}
        })

    async def count_user_memories(self, user_id: str) -> int:
        """
        Count total memories for a user.

        Args:
            user_id: User identifier

        Returns:
            Number of memories
        """
        return await self.count({"user_id": user_id})
