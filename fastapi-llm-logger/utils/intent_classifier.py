"""
Intent Classification Utility

Detects user intent from query text using keyword-based rules with optional LLM fallback.
"""

import re
from typing import Dict, Any, Optional
import logging
import os
import requests
import json
import asyncio

logger = logging.getLogger(__name__)

# OpenRouter configuration
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")


class IntentClassifier:
    """
    Classifies user queries into intent categories.

    Intents:
    - product_search: Looking for products to buy
    - general: Everything else
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

    async def classify_with_llm(self, query: str) -> Dict[str, Any]:
        """
        Use LLM to classify intent (more accurate but slower).

        Args:
            query: User query text

        Returns:
            Dictionary with intent and confidence
        """
        if not OPENROUTER_KEY:
            logger.warning("OPENROUTER_API_KEY not configured, falling back to keyword-based classification")
            return self.classify(query, use_llm=False)

        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "microsoft/phi-3-mini-128k-instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an intent classification system. Classify user queries into one of these intents:\n\n"
                            "1. product_search: User wants to find, buy, compare, or get recommendations for products/items.\n"
                            "2. general: Everything else (chatting, explanations, non-product requests).\n\n"
                            "IMPORTANT: If the query mentions specific products, rankings (\"top 3\", \"best\"), or requests recommendations, classify as product_search.\n\n"
                            "Respond ONLY with valid JSON:\n"
                            '{"intent": "product_search", "confidence": 0.95, "reasoning": "brief explanation"}'
                        )
                    },
                    {"role": "user", "content": query}
                ],
                "response_format": {"type": "json_object"},
            }

            response = await asyncio.to_thread(
                requests.post,
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]

                # Parse JSON response
                result = json.loads(content)

                intent = result.get("intent", "general")
                confidence = result.get("confidence", 0.5)
                reasoning = result.get("reasoning", "")

                # Validate intent
                valid_intents = ["product_search", "general"]
                if intent not in valid_intents:
                    logger.warning(f"Invalid intent '{intent}' from LLM, defaulting to 'general'")
                    intent = "general"

                logger.info(f"LLM classified as '{intent}' (confidence: {confidence:.2f}) - {reasoning}")

                return {
                    "intent": intent,
                    "confidence": float(confidence),
                    "matched_patterns": 0,
                    "reasoning": reasoning,
                    "method": "llm"
                }
            else:
                logger.error(f"OpenRouter API error: {response.status_code}")
                # Fallback to keyword-based
                return self.classify(query, use_llm=False)

        except Exception as e:
            logger.error(f"Error in LLM classification: {str(e)}")
            # Fallback to keyword-based
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
        result = await _classifier.classify_with_llm(query)
    else:
        result = _classifier.classify(query, use_llm=False)

    logger.info(f"Intent detected: {result['intent']} (confidence: {result['confidence']:.2f})")
    return result
