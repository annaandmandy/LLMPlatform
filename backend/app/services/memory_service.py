"""
Memory Service - Dynamic memory retrieval using vector search and summaries.

Memory is computed on-demand, not stored.
"""

from typing import List, Dict, Any, Optional
import logging

from app.db.mongodb import get_db
from app.utils.vector_search import VectorSearchService

logger = logging.getLogger(__name__)


class MemoryService:
    """
    Service for building memory context dynamically.
    
    Memory = Vector Search + Recent Messages + Summaries
    (No memories collection - it's all computed!)
    """
    
    def __init__(self):
        """Initialize memory service."""
        self.vector_search = VectorSearchService(collection_name="queries")
    
    async def get_memory_context(
        self,
        user_id: str,
        query: str,
        query_embedding: List[float],
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Build memory context from multiple sources.
        
        Args:
            user_id: User identifier
            query: Current query text
            query_embedding: Vector embedding of the query
            limit: Max items to retrieve from each source
            
        Returns:
            Dict with similar_queries, recent_messages, summaries
        """
        db = get_db()
        if db is None:
            logger.warning("Database not connected, returning empty memory")
            return {
                "similar_queries": [],
                "recent_messages": [],
                "summaries": [],
                "total_items": 0
            }
        
        memory_context = {}
        
        # 1. Vector search for similar past queries (semantic similarity)
        try:
            similar_queries = await self.vector_search.search_similar(
                query_vector=query_embedding,
                limit=limit,
                filter_dict={"user_id": user_id}
            )
            memory_context["similar_queries"] = similar_queries
            logger.info(f"Found {len(similar_queries)} similar past queries")
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            memory_context["similar_queries"] = []
        
        # 2. Recent messages from this user (conversation continuity)
        try:
            queries_collection = db["queries"]
            recent_cursor = queries_collection.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(limit)
            
            recent_docs = await recent_cursor.to_list(length=limit)
            recent_messages = [
                {
                    "query": doc.get("query"),
                    "response": doc.get("response"),
                    "timestamp": doc.get("timestamp"),
                    "intent": doc.get("intent")
                }
                for doc in recent_docs
            ]
            memory_context["recent_messages"] = recent_messages
            logger.info(f"Found {len(recent_messages)} recent messages")
        except Exception as e:
            logger.warning(f"Failed to get recent messages: {e}")
            memory_context["recent_messages"] = []
        
        # 3. Session summaries (high-level context)
        try:
            summaries_collection = db["summaries"]
            summaries_cursor = summaries_collection.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(3)  # Last 3 summaries
            
            summary_docs = await summaries_cursor.to_list(length=3)
            summaries = [
                {
                    "summary": doc.get("summary_text"),
                    "session_id": doc.get("session_id"),
                    "timestamp": doc.get("timestamp"),
                    "topics": doc.get("topics", [])
                }
                for doc in summary_docs
            ]
            memory_context["summaries"] = summaries
            logger.info(f"Found {len(summaries)} summaries")
        except Exception as e:
            logger.warning(f"Failed to get summaries: {e}")
            memory_context["summaries"] = []
        
        # Calculate total items
        total_items = (
            len(memory_context.get("similar_queries", [])) +
            len(memory_context.get("recent_messages", [])) +
            len(memory_context.get("summaries", []))
        )
        memory_context["total_items"] = total_items
        
        logger.info(f"Memory context built: {total_items} total items")
        return memory_context
    
    def format_memory_for_prompt(
        self,
        memory_context: Dict[str, Any],
        max_items: int = 5
    ) -> str:
        """
        Format memory context into a prompt-friendly string.
        
        Args:
            memory_context: Memory context dict
            max_items: Max items to include in prompt
            
        Returns:
            Formatted memory string
        """
        parts = []
        
        # Add similar queries
        similar = memory_context.get("similar_queries", [])[:max_items]
        if similar:
            parts.append("### Similar Past Conversations:")
            for i, item in enumerate(similar, 1):
                parts.append(f"{i}. Q: {item.get('query', 'N/A')}")
                parts.append(f"   A: {item.get('response', 'N/A')[:100]}...")
        
        # Add recent messages
        recent = memory_context.get("recent_messages", [])[:max_items]
        if recent:
            parts.append("\n### Recent Conversation:")
            for i, msg in enumerate(recent, 1):
                parts.append(f"{i}. {msg.get('query', 'N/A')}")
        
        # Add summaries
        summaries = memory_context.get("summaries", [])
        if summaries:
            parts.append("\n### Previous Session Summaries:")
            for i, summary in enumerate(summaries, 1):
                parts.append(f"{i}. {summary.get('summary', 'N/A')}")
        
        if not parts:
            return ""
        
        return "\n".join(parts)


# Global instance
memory_service = MemoryService()
