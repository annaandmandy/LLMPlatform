"""
Embedding Utilities

Handles text embeddings for semantic search and RAG retrieval.
Uses sentence-transformers for efficient local embeddings.
"""

import os
from pathlib import Path
from typing import List, Optional
import numpy as np
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Global model instance (lazy loaded)
_embedding_model = None
_MODEL_NAME = "all-MiniLM-L6-v2"


def _resolve_cache_dir() -> Optional[str]:
    """
    Determine a writable cache directory for SentenceTransformer models.
    Returns None to let sentence-transformers use its defaults.
    """
    env_cache = os.getenv("EMBEDDING_MODEL_CACHE")
    if env_cache:
        cache_path = Path(env_cache).expanduser()
    else:
        cache_path = Path(__file__).resolve().parent.parent / "cache" / "models"

    try:
        cache_path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.warning("Cache dir %s unavailable (%s); using default huggingface cache.", cache_path, exc)
        return None

    if os.access(cache_path, os.W_OK):
        return str(cache_path)

    logger.warning("Cache dir %s not writable; using default huggingface cache.", cache_path)
    return None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model...")
        cache_dir = _resolve_cache_dir()
        model_kwargs = {"cache_folder": cache_dir} if cache_dir else {}
        _embedding_model = SentenceTransformer(_MODEL_NAME, **model_kwargs)
        logger.info("Model loaded successfully.")
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
