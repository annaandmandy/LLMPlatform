"""
Intent Classification Utility

Detects user intent from query text using a hybrid approach:
1. Keyword-based rules (fast, deterministic)
2. Optional LLM-based classification (more accurate, slower)
"""

import re
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Classifies user queries into intent categories.

    Intents:
    - product_search: Looking for products to buy
    - summarize: Request for conversation summary
    - retrieve_memory: Request for past conversation context
    - general: General conversation
    """

    # Keyword patterns for each intent
    PRODUCT_KEYWORDS = [
        r'\b(buy|purchase|shop|price|cost|cheap|expensive|sale|discount)\b',
        r'\b(product|item|goods|merchandise)\b',
        r'\b(store|seller|vendor|market|amazon|ebay)\b',
        r'\b(find|search|looking for|need|want).*(product|item)\b',
        r'\b(show|display|list).*(product|item|price)\b'
    ]

    SUMMARIZE_KEYWORDS = [
        r'\b(summarize|summary|recap)\b',
        r'\b(what (did|have) (we|i)).*discuss\b',
        r'\b(overview|digest|brief)\b',
        r'\btell me (what|about).*(said|discussed|talked)\b'
    ]

    MEMORY_KEYWORDS = [
        r'\b(remember|recall|mentioned|said)\b',
        r'\b(earlier|before|previously|past)\b',
        r'\b(history|conversation|chat).*(show|display|retrieve)\b',
        r'\b(what (did|have)).*(say|tell|mention)\b',
        r'\bdo you (remember|recall)\b'
    ]

    def __init__(self):
        """Initialize the intent classifier."""
        self.product_patterns = [re.compile(p, re.IGNORECASE) for p in self.PRODUCT_KEYWORDS]
        self.summarize_patterns = [re.compile(p, re.IGNORECASE) for p in self.SUMMARIZE_KEYWORDS]
        self.memory_patterns = [re.compile(p, re.IGNORECASE) for p in self.MEMORY_KEYWORDS]

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
                - matched_patterns: List of matched patterns (for debugging)
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

        # Check for summarize intent
        summarize_matches = self._count_matches(query, self.summarize_patterns)
        if summarize_matches > 0:
            return {
                "intent": "summarize",
                "confidence": min(0.6 + (summarize_matches * 0.2), 1.0),
                "matched_patterns": summarize_matches
            }

        # Check for memory retrieval intent
        memory_matches = self._count_matches(query, self.memory_patterns)
        if memory_matches > 0:
            return {
                "intent": "retrieve_memory",
                "confidence": min(0.6 + (memory_matches * 0.2), 1.0),
                "matched_patterns": memory_matches
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

    async def classify_with_llm(self, query: str, llm_client) -> Dict[str, Any]:
        """
        Use LLM to classify intent (more accurate but slower).

        Args:
            query: User query text
            llm_client: LLM client instance

        Returns:
            Dictionary with intent and confidence

        Note: This is a placeholder for future LLM-based classification
        """
        # TODO: Implement LLM-based classification for better accuracy
        # This would call a small, fast model like gpt-4o-mini with a classification prompt
        pass


# Global classifier instance
_classifier = IntentClassifier()


def detect_intent(query: str, use_llm: bool = False) -> Dict[str, Any]:
    """
    Detect the intent of a user query.

    Args:
        query: User query text
        use_llm: Whether to use LLM for classification

    Returns:
        Dictionary containing intent, confidence, and matched_patterns

    Example:
        >>> detect_intent("I want to buy a laptop")
        {'intent': 'product_search', 'confidence': 0.65, 'matched_patterns': 1}
    """
    result = _classifier.classify(query, use_llm=use_llm)
    logger.info(f"Intent detected: {result['intent']} (confidence: {result['confidence']:.2f})")
    return result
