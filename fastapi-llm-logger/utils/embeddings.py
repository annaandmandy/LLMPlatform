"""
Embedding Utilities

Handles text embeddings for semantic search and RAG retrieval.
Uses sentence-transformers for efficient local embeddings.
"""

from typing import List, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Global model instance (lazy loaded)
_embedding_model = None


def get_embedding_model():
    """
    Get or initialize the embedding model.

    Uses all-MiniLM-L6-v2 (384 dimensions, fast, good quality)

    Returns:
        SentenceTransformer model instance
    """
    global _embedding_model

    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model: all-MiniLM-L6-v2")
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model loaded successfully")
        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise

    return _embedding_model


def get_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for a text string.

    Args:
        text: Input text to embed

    Returns:
        List of floats representing the embedding vector (384 dimensions)

    Example:
        >>> embedding = get_embedding("Hello world")
        >>> len(embedding)
        384
    """
    try:
        model = get_embedding_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Failed to generate embedding: {str(e)}")
        raise


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts efficiently.

    Args:
        texts: List of text strings to embed

    Returns:
        List of embedding vectors

    Example:
        >>> embeddings = get_embeddings_batch(["Hello", "World"])
        >>> len(embeddings)
        2
    """
    try:
        model = get_embedding_model()
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Failed to generate batch embeddings: {str(e)}")
        raise


def compute_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Compute cosine similarity between two embeddings.

    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector

    Returns:
        Similarity score between -1 and 1 (higher is more similar)

    Example:
        >>> emb1 = get_embedding("cat")
        >>> emb2 = get_embedding("kitten")
        >>> similarity = compute_similarity(emb1, emb2)
        >>> similarity > 0.7
        True
    """
    try:
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        return float(similarity)

    except Exception as e:
        logger.error(f"Failed to compute similarity: {str(e)}")
        raise


def find_most_similar(
    query_embedding: List[float],
    candidate_embeddings: List[List[float]],
    top_k: int = 3
) -> List[tuple]:
    """
    Find the most similar embeddings to a query embedding.

    Args:
        query_embedding: Query embedding vector
        candidate_embeddings: List of candidate embedding vectors
        top_k: Number of top results to return

    Returns:
        List of tuples (index, similarity_score) sorted by similarity (descending)

    Example:
        >>> query_emb = get_embedding("machine learning")
        >>> candidates = [get_embedding("AI"), get_embedding("cooking")]
        >>> results = find_most_similar(query_emb, candidates, top_k=1)
        >>> results[0][0]  # Index of most similar
        0
    """
    try:
        similarities = []
        for idx, candidate_emb in enumerate(candidate_embeddings):
            similarity = compute_similarity(query_embedding, candidate_emb)
            similarities.append((idx, similarity))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    except Exception as e:
        logger.error(f"Failed to find most similar: {str(e)}")
        raise


def preload_model():
    """
    Preload the embedding model to avoid cold start.

    Call this during application startup.
    """
    try:
        get_embedding_model()
        logger.info("Embedding model preloaded")
    except Exception as e:
        logger.warning(f"Failed to preload embedding model: {str(e)}")
