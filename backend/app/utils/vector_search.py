"""
Vector Search Utilities

Provides helper functions for MongoDB Atlas Vector Search.
"""

from typing import List, Dict, Any, Optional
import logging
from app.db.mongodb import get_db

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Service for performing vector similarity searches using MongoDB Atlas."""
    
    def __init__(self, collection_name: str = "queries"):
        """
        Initialize vector search service.
        
        Args:
            collection_name: MongoDB collection with vector embeddings
        """
        self.collection_name = collection_name
    
    async def search_similar(
        self,
        query_vector: List[float],
        limit: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search using MongoDB Atlas Vector Search.
        
        Args:
            query_vector: The query embedding vector (1536 dims for OpenAI)
            limit: Maximum number of results to return
            filter_dict: Optional MongoDB filter to apply (e.g., {"user_id": "123"})
            
        Returns:
            List of similar documents with scores
            
        Example:
            >>> results = await service.search_similar(
            ...     query_vector=[0.1, 0.2, ...],  # 1536 dims
            ...     limit=5,
            ...     filter_dict={"user_id": "user123"}
            ... )
            >>> for result in results:
            ...     print(f"Score: {result['score']}, Query: {result['query']}")
        """
        db = get_db()
        if db is None:
            raise RuntimeError("Database not connected")
        
        collection = db[self.collection_name]
        
        # Build the aggregation pipeline
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",  # Name from Atlas UI setup
                    "path": "embedding",       # Field containing embeddings
                    "queryVector": query_vector,
                    "numCandidates": limit * 10,  # Performance tuning
                    "limit": limit
                }
            }
        ]
        
        # Add optional filter stage
        if filter_dict:
            pipeline.append({
                "$match": filter_dict
            })
        
        # Project relevant fields and add score
        pipeline.append({
            "$project": {
                "_id": 0,
                "query": 1,
                "response": 1,
                "user_id": 1,
                "session_id": 1,
                "timestamp": 1,
                "intent": 1,
                "model_provider": 1,
                "model_name": 1,
                "citations": 1,
                "score": {"$meta": "vectorSearchScore"}  # Similarity score
            }
        })
        
        try:
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=limit)
            
            logger.info(f"Vector search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            # Check if it's an index error
            if "index" in str(e).lower():
                logger.error(
                    "Vector index 'vector_index' not found. "
                    "Please create it in MongoDB Atlas UI. "
                    "See: app/scripts/migrate_collections.py for instructions"
                )
            raise
    
    async def search_by_text(
        self,
        query_text: str,
        embedding_function: callable,
        limit: int = 5,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search by text query (converts to vector first).
        
        Args:
            query_text: Text query to search for
            embedding_function: Function that converts text to vector
            limit: Maximum results
            **kwargs: Additional args passed to search_similar
            
        Returns:
            List of similar documents
            
        Example:
            >>> from app.utils.embeddings import get_embedding
            >>> results = await service.search_by_text(
            ...     "How do I reset my password?",
            ...     embedding_function=get_embedding,
            ...     limit=3
            ... )
        """
        # Convert text to vector
        query_vector = await embedding_function(query_text)
        
        # Perform vector search
        return await self.search_similar(
            query_vector=query_vector,
            limit=limit,
            **kwargs
        )


# Global instance for easy import
vector_search = VectorSearchService()


# Convenience function
async def search_similar_queries(
    query_vector: List[float],
    limit: int = 5,
    user_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function for searching similar queries.
    
    Args:
        query_vector: The query embedding
        limit: Max results
        user_id: Optional user filter
        
    Returns:
        List of similar query documents
    """
    filter_dict = {"user_id": user_id} if user_id else None
    return await vector_search.search_similar(
        query_vector=query_vector,
        limit=limit,
        filter_dict=filter_dict
    )
