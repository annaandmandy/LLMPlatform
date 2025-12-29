"""
Embedding Service - Generate vector embeddings for text.

Supports OpenAI embeddings (text-embedding-3-small).
"""

from typing import List
import logging
from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self):
        """Initialize embedding service with OpenAI client."""
        self.client = None
        self.model = "text-embedding-3-small"  # 1536 dimensions
        self.dimensions = 1536
    
    def _ensure_client(self):
        """Lazy load OpenAI client."""
        if self.client is None:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key not configured")
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return self.client
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of 1536 floats (embedding vector)
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * self.dimensions
        
        try:
            client = self._ensure_client()
            
            # Call OpenAI embeddings API
            response = client.embeddings.create(
                model=self.model,
                input=text[:8000],  # Limit to 8k chars
                encoding_format="float"
            )
            
            # Extract embedding
            embedding = response.data[0].embedding
            
            logger.info(f"Generated embedding: {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return zero vector on error
            return [0.0] * self.dimensions
    
    async def generate_batch_embeddings(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Max texts per API call
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        embeddings = []
        
        try:
            client = self._ensure_client()
            
            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch = [t[:8000] for t in batch]  # Limit each text
                
                response = client.embeddings.create(
                    model=self.model,
                    input=batch,
                    encoding_format="float"
                )
                
                # Extract embeddings in order
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
            
            logger.info(f"Generated {len(embeddings)} embeddings in batch")
            return embeddings
            
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            # Return zero vectors for all texts
            return [[0.0] * self.dimensions for _ in texts]
    
    async def embed_query_and_response(
        self,
        query: str,
        response: str
    ) -> List[float]:
        """
        Generate embedding for query + response pair.
        
        Combines query and response for better semantic search.
        
        Args:
            query: User query
            response: AI response
            
        Returns:
            Embedding vector
        """
        # Combine query and response with clear separation
        combined_text = f"Query: {query}\nResponse: {response}"
        return await self.generate_embedding(combined_text)


# Global instance
embedding_service = EmbeddingService()
