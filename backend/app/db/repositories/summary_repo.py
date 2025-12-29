"""
Repository for summary-related database operations.

Handles storage and retrieval of session summaries, including:
- Creating and updating summaries
- Retrieving summaries by session/user
- Managing summary history
"""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from app.db.repositories.base import BaseRepository


class SummaryRepository(BaseRepository):
    """Repository for managing summary documents in MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize with summaries collection."""
        super().__init__(db, "summaries")

    async def create_or_update_summary(
        self,
        session_id: str,
        summary_text: str,
        message_count: int,
        model_used: str = "rule_based",
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Create a new summary or append to existing summary document.

        Args:
            session_id: Session identifier
            summary_text: Generated summary text
            message_count: Number of messages summarized
            model_used: Model or strategy used (e.g., "gpt-4o-mini", "rule_based")
            user_id: Optional user identifier

        Returns:
            True if successful
        """
        summary_entry = {
            "t": datetime.now(),
            "text": summary_text,
            "message_count": message_count,
            "model": model_used,
        }

        # Check if summary document exists
        summary_doc = await self.find_one({"session_id": session_id})

        if summary_doc:
            # Append to existing summaries
            await self.update_one(
                {"session_id": session_id},
                {"$push": {"summaries": summary_entry}}
            )
        else:
            # Create new summary document
            await self.create(
                {
                    "session_id": session_id,
                    "user_id": user_id,
                    "summaries": [summary_entry],
                    "created_at": datetime.now()
                }
            )

        return True

    async def get_summaries_by_session(
        self,
        session_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get summaries for a specific session.

        Args:
            session_id: Session identifier
            limit: Maximum number of summary entries to return

        Returns:
            List of summary entries
        """
        doc = await self.find_one({"session_id": session_id})

        if not doc:
            return []

        # Get the most recent summaries
        summaries = doc.get("summaries", [])
        recent_summaries = summaries[-limit:] if len(summaries) > limit else summaries

        return [
            {
                "session_id": doc.get("session_id"),
                "summary": entry.get("text"),
                "message_count": entry.get("message_count"),
                "model": entry.get("model"),
                "timestamp": entry.get("t"),
            }
            for entry in recent_summaries
        ]

    async def get_summaries_by_user(
        self,
        user_id: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get recent summaries across all sessions for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of summary documents to return

        Returns:
            List of summary entries
        """
        cursor = self.collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(limit)

        docs = await cursor.to_list(length=limit)

        summaries = []
        for doc in docs:
            # Only take the newest summary entry per doc
            latest_entry = doc.get("summaries", [])[-1:] or []
            for entry in latest_entry:
                summaries.append(
                    {
                        "session_id": doc.get("session_id"),
                        "summary": entry.get("text"),
                        "message_count": entry.get("message_count"),
                        "model": entry.get("model"),
                        "timestamp": entry.get("t"),
                    }
                )

        return summaries

    async def get_summaries_for_context(
        self,
        user_id: Optional[str],
        session_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Get summaries for building context (used by memory agent).

        Args:
            user_id: Optional user identifier
            session_id: Optional session identifier

        Returns:
            List of unique summary entries
        """
        filters: List[Dict[str, Any]] = []
        if session_id:
            filters.append({"session_id": session_id})
        if user_id:
            filters.append({"user_id": user_id})

        summaries: List[Dict[str, Any]] = []
        for f in filters:
            cursor = self.collection.find(f).sort("created_at", -1).limit(2)
            docs = await cursor.to_list(length=2)
            for doc in docs:
                # Only take the newest summary entry per doc to save tokens
                latest_entry = doc.get("summaries", [])[-1:] or []
                for entry in latest_entry:
                    summaries.append(
                        {
                            "session_id": doc.get("session_id"),
                            "summary": entry.get("text"),
                            "message_count": entry.get("message_count"),
                            "model": entry.get("model"),
                            "timestamp": entry.get("t"),
                        }
                    )

        # Deduplicate by summary text + session_id
        seen = set()
        unique = []
        for s in summaries:
            key = (s.get("session_id"), s.get("summary"))
            if key in seen:
                continue
            seen.add(key)
            unique.append(s)

        # Keep only the newest few summaries for prompt usage
        return unique[:3]

    async def get_summaries_by_user_for_memory(
        self,
        user_id: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get summaries formatted for memory service.

        Args:
            user_id: User identifier
            limit: Maximum number of summaries to return

        Returns:
            List of summary dictionaries with summary_text field
        """
        cursor = self.collection.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit)

        summary_docs = await cursor.to_list(length=limit)

        return [
            {
                "summary": doc.get("summary_text"),
                "session_id": doc.get("session_id"),
                "timestamp": doc.get("timestamp"),
                "topics": doc.get("topics", [])
            }
            for doc in summary_docs
        ]

    async def count_user_summaries(self, user_id: str) -> int:
        """
        Count total summary documents for a user.

        Args:
            user_id: User identifier

        Returns:
            Number of summary documents
        """
        return await self.count({"user_id": user_id})
