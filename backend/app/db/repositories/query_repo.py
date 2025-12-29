"""
Repository for query-related database operations.

Handles storage and retrieval of user queries, including:
- Query logging with embeddings
- Query history retrieval
- Vector similarity search (for memory)
"""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from app.db.repositories.base import BaseRepository


class QueryRepository(BaseRepository):
    """Repository for managing query documents in MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize with queries collection."""
        super().__init__(db, "queries")

    async def create_query_log(
        self,
        user_id: str,
        session_id: str,
        query: str,
        response: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a query with its response and optional embedding.

        Args:
            user_id: User identifier
            session_id: Session identifier
            query: User's query text
            response: LLM response text
            embedding: Optional query embedding vector
            metadata: Optional additional metadata (model, tokens, etc.)

        Returns:
            ID of created query log
        """
        document = {
            "user_id": user_id,
            "session_id": session_id,
            "query": query,
            "response": response,
            "timestamp": datetime.utcnow(),
            "created_at": datetime.utcnow().isoformat(),
        }

        if embedding:
            document["embedding"] = embedding

        if metadata:
            document.update(metadata)

        return await self.create(document)

    async def get_user_query_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get query history for a user.

        Args:
            user_id: User identifier
            session_id: Optional session filter
            limit: Maximum number of queries to return
            skip: Number of queries to skip (for pagination)

        Returns:
            List of query documents (without embeddings for performance)
        """
        query = {"user_id": user_id}
        if session_id:
            query["session_id"] = session_id

        # Exclude large embedding arrays for performance
        projection = {"embedding": 0}

        queries = await self.find_many(
            query=query,
            sort=[("timestamp", -1)],  # Most recent first
            limit=limit,
            skip=skip,
            projection=projection
        )

        return queries

    async def get_session_queries(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all queries for a specific session.

        Args:
            session_id: Session identifier
            limit: Optional maximum number of queries

        Returns:
            List of query documents
        """
        return await self.find_many(
            query={"session_id": session_id},
            sort=[("timestamp", 1)],  # Chronological order
            limit=limit,
            projection={"embedding": 0}  # Exclude embeddings
        )

    async def delete_user_queries(self, user_id: str) -> int:
        """
        Delete all queries for a user.

        Args:
            user_id: User identifier

        Returns:
            Number of queries deleted
        """
        return await self.delete_many({"user_id": user_id})

    async def delete_session_queries(self, session_id: str) -> int:
        """
        Delete all queries for a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of queries deleted
        """
        return await self.delete_many({"session_id": session_id})
