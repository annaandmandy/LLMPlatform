"""
Product Agent

Extracts product mentions from LLM responses and fetches real product data
from online retailers (Amazon, etc.) to generate product preview cards.

Flow:
1. LLM generates response
2. ProductAgent extracts product mentions from the response
3. Search for real products online using those keywords
4. Return product cards with real URLs users can click
"""

from typing import Dict, Any, List
import logging
import re
import os
import requests
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

# SerpAPI configuration
SERPAPI_KEY = os.getenv("SERPAPI_KEY")


class ProductAgent(BaseAgent):
    """
    Extracts product mentions and fetches real product data.

    The ProductAgent:
    1. Receives LLM response text
    2. Extracts product mentions (items, brands, product names)
    3. Searches for real products online
    4. Returns product cards with real purchasable links
    """

    def __init__(self, db=None):
        """
        Initialize the ProductAgent.

        Args:
            db: MongoDB database instance (optional, for caching)
        """
        super().__init__(name="ProductAgent", db=db)

        # Common product keywords that indicate a product mention
        self.product_indicators = [
            r'\b(buy|purchase|get|order)\s+(?:a|an|the|some)?\s*([A-Z][a-zA-Z\s&-]+)',
            r'\b(recommend|suggests?|try)\s+(?:the|a|an)?\s*([A-Z][a-zA-Z\s&-]+)',
            r'\b([A-Z][a-zA-Z]+)\s+(headphones|speaker|mat|lamp|filter|tracker|watch|chair|laptop|phone|tablet|camera|tv|earplugs|earbuds)',
            r'\b(Apple|Sony|Samsung|Fitbit|Bose|Nike|Adidas|Dell|HP|Canon|Nikon|LG|Brita|Ninja|Loop|Mack|Flents|Ohropax|Howard)\s+([A-Z][a-zA-Z0-9\s\'-]+)',
            r'\b([A-Z][a-zA-Z\'-]+\s+)+Earplugs?\b',  # Matches "Loop Quiet Earplugs", "Mack's Ultra Soft Foam Earplugs"
        ]

    async def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract product mentions from LLM response and fetch real product data.

        Args:
            request: Dictionary containing:
                - query: User's original query
                - llm_response: LLM's generated response text (optional)
                - max_results: Maximum products per mention (default: 3)

        Returns:
            Dictionary containing:
                - products: List of real product cards with purchase links
                - extracted_mentions: Product names extracted from response
        """
        query = request.get("query", "")
        llm_response = request.get("llm_response", "")
        max_results = request.get("max_results", 3)

        logger.info(f"Extracting product mentions from response")

        try:
            # Extract product mentions from LLM response or query
            text_to_analyze = llm_response if llm_response else query
            product_mentions = self._extract_product_mentions(text_to_analyze)

            if not product_mentions:
                logger.info("No product mentions found")
                return {
                    "products": [],
                    "extracted_mentions": []
                }

            logger.info(f"Extracted {len(product_mentions)} product mentions: {product_mentions}")

            # Search for real products for each mention
            all_products = []
            for mention in product_mentions[:3]:  # Limit to top 3 mentions
                products = await self._search_real_products(mention, max_results=max_results)
                all_products.extend(products)

            # Limit total products returned
            all_products = all_products[:10]

            logger.info(f"Found {len(all_products)} real products")

            return {
                "products": all_products,
                "extracted_mentions": product_mentions
            }

        except Exception as e:
            logger.error(f"Error in product extraction: {str(e)}")
            return {
                "products": [],
                "extracted_mentions": [],
                "error": str(e)
            }

    def _extract_product_mentions(self, text: str) -> List[str]:
        """
        Extract product mentions from text using pattern matching.

        Args:
            text: Text to analyze (LLM response or user query)

        Returns:
            List of extracted product names/terms
        """
        mentions = []

        # Extract using regex patterns
        for pattern in self.product_indicators:
            matches = re.findall(pattern, text)
            for match in matches:
                # match is a tuple, get the product name part
                if isinstance(match, tuple):
                    product_name = " ".join([m for m in match if m and len(m) > 2]).strip()
                else:
                    product_name = match.strip()

                if product_name and len(product_name) > 3:
                    mentions.append(product_name)

        # Remove duplicates while preserving order
        unique_mentions = []
        for mention in mentions:
            if mention not in unique_mentions:
                unique_mentions.append(mention)

        return unique_mentions[:5]  # Limit to top 5 mentions

    async def _search_real_products(self, product_name: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search for real products using Google Shopping via SerpAPI.

        Args:
            product_name: Product name to search for
            max_results: Maximum results (default: 3)

        Returns:
            List of product card dictionaries with real links
        """
        try:
            if not SERPAPI_KEY:
                logger.warning("SERPAPI_KEY not configured, skipping product search")
                return []

            url = "https://serpapi.com/search.json"
            params = {
                "engine": "google_shopping",
                "q": product_name,
                "hl": "en",
                "gl": "us",
                "api_key": SERPAPI_KEY,
            }

            logger.info(f"Searching Google Shopping for: {product_name}")

            res = requests.get(url, params=params, timeout=10)
            data = res.json()

            products = []
            for item in data.get("shopping_results", [])[:max_results]:
                product = {
                    "title": item.get("title", ""),
                    "description": item.get("snippet", ""),
                    "price": item.get("price", ""),
                    "rating": item.get("rating"),
                    "reviews_count": item.get("reviews"),
                    "image": item.get("thumbnail", ""),
                    "url": item.get("link") or item.get("product_link", ""),
                    "seller": item.get("source", ""),
                    "tag": item.get("tag", ""),
                    "delivery": item.get("delivery", ""),
                    "search_query": product_name
                }

                # Only add if we have at least a title and URL
                if product["title"] and product["url"]:
                    products.append(product)

            logger.info(f"Found {len(products)} products for '{product_name}'")

            return products

        except Exception as e:
            logger.error(f"Error searching for product '{product_name}': {str(e)}")
            return []
