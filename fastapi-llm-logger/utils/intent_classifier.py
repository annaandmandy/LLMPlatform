"""
Intent Classification Utility

Detects user intent from query text using keyword-based rules with optional LLM fallback.
"""

import re
from typing import Dict, Any, Optional, List
import logging
import os
import json
import numpy as np
from openai import OpenAI

logger = logging.getLogger(__name__)

# API configuration
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Central place to view/update supported intents
INTENT_DEFINITIONS: Dict[str, str] = {
    "general": "User is asking a general question, chatting, or making a non-product request.",
    "product_search": "User wants to search or find a product, brand, or item to buy or compare."
}
INTENT_LIST = list(INTENT_DEFINITIONS.keys())


class IntentClassifier:
    """
    Classifies user queries into intent categories.

    Intents:
        - Entries in INTENT_LIST (e.g., ["general", "product_search"])
    """

    def __init__(self, keyword_file: str = "intent_keywords.json"):
        """Initialize the intent classifier and compile patterns."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.keyword_file = os.path.join(base_dir, keyword_file)

        if not os.path.exists(self.keyword_file):
            raise FileNotFoundError(f"Keyword file not found: {self.keyword_file}")

        with open(self.keyword_file, "r", encoding="utf-8") as f:
            keyword_data = json.load(f)

        self.product_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in keyword_data["product_search"]["patterns"]
        ]

        logger.info(f"✅ IntentClassifier initialized from {self.keyword_file}")

        # Embedding-based intent descriptions pulled from shared map (lazy embedding computation)
        self.intent_descriptions = INTENT_DEFINITIONS.copy()
        self.intent_embeddings: Optional[Dict[str, List[float]]] = None
        self.embedding_model = os.getenv("INTENT_EMBEDDING_MODEL", "text-embedding-3-small")
        self._openai_client: Optional[OpenAI] = None

    def classify(self, query: str, use_llm: bool = False) -> Dict[str, Any]:
        """
        Classify the query into an intent category.

        Args:
            query: User query text
            use_llm: Whether to use LLM for classification (not implemented yet)

        Returns:
            Dictionary containing:
                - intent: The detected intent
                - confidence: Confidence score (0-1)
                - matched_patterns: Number of matched patterns (for debugging)
        """
        query_lower = query.lower().strip()

        # Check for product search intent
        product_matches = self._count_matches(query, self.product_patterns)
        if product_matches > 0:
            return {
                "intent": "product_search",
                "confidence": min(0.5 + (product_matches * 0.15), 1.0),
                "matched_patterns": product_matches
            }

        # Default to general intent
        return {
            "intent": "general",
            "confidence": 0.5,
            "matched_patterns": 0
        }

    def _count_matches(self, text: str, patterns: list) -> int:
        """
        Count how many patterns match the text.

        Args:
            text: Text to search
            patterns: List of compiled regex patterns

        Returns:
            Number of matching patterns
        """
        matches = 0
        for pattern in patterns:
            if pattern.search(text):
                matches += 1
        return matches

    def _ensure_openai_client(self):
        if self._openai_client is None:
            if not OPENAI_API_KEY:
                raise RuntimeError("OPENAI_API_KEY not configured")
            self._openai_client = OpenAI(api_key=OPENAI_API_KEY)

    def _get_embedding(self, text: str) -> List[float]:
        self._ensure_openai_client()
        response = self._openai_client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding

    def _ensure_intent_embeddings(self):
        if self.intent_embeddings is None:
            logger.info("Precomputing intent embeddings for classifier")
            self.intent_embeddings = {
                intent: self._get_embedding(description)
                for intent, description in self.intent_descriptions.items()
            }

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        a = np.array(vec_a)
        b = np.array(vec_b)
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    async def classify_with_llm(self, query: str) -> Dict[str, Any]:
        """
        Use OpenAI embeddings to classify intent via semantic similarity.

        Args:
            query: User query text

        Returns:
            Dictionary with intent, confidence, and per-intent scores
        """
        if not OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not configured, falling back to keyword-based classification")
            return self.classify(query, use_llm=False)

        query = (query or "").strip()
        if not query:
            return {"intent": "general", "confidence": 0.5, "matched_patterns": 0}

        try:
            self._ensure_intent_embeddings()
            query_embedding = self._get_embedding(query)

            scores = {
                intent: self._cosine_similarity(query_embedding, emb)
                for intent, emb in (self.intent_embeddings or {}).items()
            }

            best_intent = max(scores, key=scores.get)
            best_score = scores[best_intent]
            confidence = max(0.0, min(1.0, (best_score + 1) / 2))

            return {
                "intent": best_intent,
                "confidence": round(confidence, 3),
                "matched_patterns": 0,
                "all_scores": {k: round(v, 3) for k, v in scores.items()},
                "method": "embedding"
            }
        except Exception as e:
            logger.error(f"Error in embedding-based intent classification: {str(e)}")
            return self.classify(query, use_llm=False)


# Global classifier instance
_classifier = IntentClassifier()


USE_LLM_INTENT = os.getenv("USE_LLM_INTENT", "false").lower() in {"true", "1", "yes"}


async def detect_intent(query: str, use_llm: Optional[bool] = None) -> Dict[str, Any]:
    """
    Detect the intent of a user query.

    Args:
        query: User query text
        use_llm: Whether to use LLM for classification (default: env USE_LLM_INTENT)

    Returns:
        Dictionary containing intent, confidence, and matched_patterns

    Example:
        >>> await detect_intent("I want to buy a laptop")
        {'intent': 'product_search', 'confidence': 0.95, 'reasoning': 'User wants product recommendations'}
    """
    should_use_llm = USE_LLM_INTENT if use_llm is None else use_llm

    if should_use_llm:
        logger.info(f"used llm")
        result = await _classifier.classify_with_llm(query)
    else:
        result = _classifier.classify(query, use_llm=False)

    logger.info(f"Intent detected: {result['intent']} (confidence: {result['confidence']:.2f})")
    return result
