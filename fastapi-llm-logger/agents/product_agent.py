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

from typing import Dict, Any, List, Optional
import logging
import re
import os
import json
import asyncio
import requests
from openai import OpenAI
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

# SerpAPI configuration
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PRODUCT_EXTRACTION_MODEL = os.getenv("PRODUCT_EXTRACTION_MODEL", "gpt-4o-mini")
EXTRACTION_SYSTEM_PROMPT = (
    "You read a passage and identify up to 5 concrete consumer products or brand models mentioned. "
    "For each product, also infer the general product category (e.g., water bottle, running shoes, travel pillow). "
    "Return JSON: {\"products\": [{\"name\": \"Hydro Flask Standard Mouth\", \"category\": \"water bottle\"}, ...]}. "
    "If the category is unclear, use a short descriptive noun phrase such as 'fitness tracker'. "
    "Ignore URLs, publishers, or abstract ideas."
)
EXTRACTION_USER_TEMPLATE = "Passage:\n\"\"\"{text}\"\"\"\nReturn only JSON."


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
        self._openai_client: Optional[OpenAI] = None

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
        logger.info("Extracting product mentions from response")

        try:
            text_to_analyze = llm_response if llm_response else query
            structured_mentions = await self._extract_products_with_llm(text_to_analyze)

            if not structured_mentions:
                fallback_mentions = self._extract_product_mentions(text_to_analyze)
                structured_mentions = [
                    {"name": mention, "category": None}
                    for mention in fallback_mentions
                ]

            if not structured_mentions:
                logger.info("No product mentions found")
                return {
                    "products": [],
                    "extracted_mentions": [],
                    "structured_products": []
                }

            logger.info(
                f"Extracted {len(structured_mentions)} product mentions: {structured_mentions}"
            )

            # Search for real products for each mention
            all_products = []
            extracted_names = [mention["name"] for mention in structured_mentions]
            for mention in structured_mentions[:3]:  # Limit to top 3 mentions
                search_term = mention["name"]
                if mention.get("category"):
                    search_term = f"{search_term} {mention['category']}".strip()

                products = await self._search_real_products(search_term, max_results=max_results)
                all_products.extend(products)

            # Limit total products returned
            all_products = all_products[:10]

            logger.info(f"Found {len(all_products)} real products")

            return {
                "products": all_products,
                "extracted_mentions": extracted_names,
                "structured_products": structured_mentions,
            }

        except Exception as e:
            logger.error(f"Error in product extraction: {str(e)}")
            return {
                "products": [],
                "extracted_mentions": [],
                "structured_products": [],
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

                if self._is_probable_product_name(product_name):
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

    async def _extract_products_with_llm(self, text: str) -> List[Dict[str, Optional[str]]]:
        if not text or not OPENAI_API_KEY:
            return []

        try:
            client = self._get_openai_client()
            safe_text = text.replace("{", "{{").replace("}", "}}")
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=PRODUCT_EXTRACTION_MODEL,
                messages=[
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": EXTRACTION_USER_TEMPLATE.format(text=safe_text.strip())},
                ],
                response_format={"type": "json_object"},
                max_tokens=300,
            )

            content = ""
            if response.choices:
                content = response.choices[0].message.content or ""
            if not content:
                return []

            data = json.loads(content)
            raw_products = data.get("products", [])
            structured: List[Dict[str, Optional[str]]] = []

            for item in raw_products:
                name = None
                category = None
                if isinstance(item, dict):
                    name = item.get("name") or item.get("product") or item.get("title")
                    category = item.get("category") or item.get("type")
                elif isinstance(item, str):
                    name = item

                if not name or not self._is_probable_product_name(name):
                    continue

                structured.append({
                    "name": name.strip(),
                    "category": category.strip() if isinstance(category, str) else None
                })

            deduped: List[Dict[str, Optional[str]]] = []
            seen = set()
            for entry in structured:
                key = (entry["name"].lower(), (entry.get("category") or "").lower())
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(entry)

            return deduped[:5]
        except Exception as e:
            logger.warning(f"LLM-based product extraction failed: {e}")
            return []

    def _get_openai_client(self) -> OpenAI:
        if self._openai_client is None:
            self._openai_client = OpenAI(api_key=OPENAI_API_KEY)
        return self._openai_client

    def _is_probable_product_name(self, name: str) -> bool:
        if not name:
            return False
        candidate = name.strip()
        if len(candidate) < 3:
            return False
        lowered = candidate.lower()
        if lowered.startswith("http") or "://" in lowered:
            return False
        if re.search(r"\b(blog|news|review|magazine|daily)\b", lowered):
            return False
        if "." in candidate and " " not in candidate:
            return False
        return True

    def _normalize_url(self, url: Optional[str]) -> str:
        if not url:
            return ""
        if url.startswith("http://") or url.startswith("https://"):
            return url
        if "." in url:
            return f"https://{url.strip()}"
        return url.strip()
