"""
Google Gemini provider implementation.

Supports Gemini models with Google Search grounding.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from google import genai
from google.genai import types

from app.providers.base import BaseLLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleProvider(BaseLLMProvider):
    """Google Gemini provider with Google Search grounding."""
    
    @property
    def provider_name(self) -> str:
        return "google"
    
    def _create_client(self):
        """Create Google Gemini client."""
        api_key = self.api_key or settings.GOOGLE_API_KEY
        if not api_key:
            raise ValueError("Google API key not configured")
        return genai.Client(api_key=api_key)
    
    async def generate(
        self,
        model: str,
        query: str,
        system_prompt: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Tuple[str, List[Dict], Dict, Optional[Dict]]:
        """
        Generate response using Google Gemini API.
        
        Supports Google Search grounding for web search.
        """
        client = self._ensure_client()
        
        # Enable Google Search grounding
        grounding_tool = types.Tool(google_search=types.GoogleSearch())
        config = types.GenerateContentConfig(tools=[grounding_tool])
        
        # Generate content
        system_message = system_prompt or "You are a helpful AI assistant."
        
        response = client.models.generate_content(
            model=model,
            contents=[
                {"role": "user", "parts": [{"text": f"{system_message}\n\n{query}"}]}
            ],
            config=config,
        )
        
        # --- Extract text ---
        text = ""
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content") and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, "text"):
                        text += part.text + "\n"
        
        # --- Extract citations ---
        citations = []
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            metadata = getattr(candidate, "grounding_metadata", None)
            
            if metadata and getattr(metadata, "grounding_chunks", None):
                for chunk in metadata.grounding_chunks:
                    web_obj = getattr(chunk, "web", None)
                    if web_obj:
                        citations.append({
                            "title": getattr(web_obj, "title", ""),
                            "url": getattr(web_obj, "uri", "")
                        })
                    elif isinstance(chunk, dict) and "web" in chunk:
                        web = chunk["web"]
                        citations.append({
                            "title": web.get("title", ""),
                            "url": web.get("uri", "")
                        })
        
        # Remove duplicates
        seen, unique = set(), []
        for c in citations:
            url = c.get("url")
            if url and url not in seen:
                seen.add(url)
                unique.append(c)
        
        # Extract token usage
        tokens = None
        if hasattr(response, "usage_metadata"):
            usage = response.usage_metadata
            tokens = {
                "prompt": getattr(usage, "prompt_token_count", 0),
                "completion": getattr(usage, "candidates_token_count", 0),
                "total": getattr(usage, "total_token_count", 0)
            }
        
        # Convert response to dict safely
        try:
            raw = response.as_dict()  # works in google-genai >= 0.2.0
        except AttributeError:
            # Fallback: build manually if as_dict is missing
            raw = {
                "candidates": [{
                    "content": [
                        getattr(p, "text", "")
                        for p in getattr(response.candidates[0].content, "parts", [])
                        if hasattr(p, "text")
                    ],
                    "grounding_metadata": str(getattr(response.candidates[0], "grounding_metadata", "")),
                }] if hasattr(response, "candidates") and response.candidates else []
            }
        
        return text.strip(), unique, raw, tokens
    
    def supports_streaming(self) -> bool:
        """Google Gemini supports streaming."""
        return True
    
    def supports_vision(self, model: str) -> bool:
        """Gemini Pro Vision and 2.0+ support vision."""
        vision_models = ["vision", "gemini-2", "gemini-pro"]
        return any(vm in model.lower() for vm in vision_models)
    
    def supports_web_search(self, model: str) -> bool:
        """All Gemini models support Google Search grounding."""
        return True
