"""
OpenRouter provider implementation.

Supports routing to various models (Grok, Perplexity, etc.) through OpenRouter API.
"""

import logging
import json
import requests
from typing import Dict, Any, List, Tuple, Optional

from app.providers.base import BaseLLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter provider for accessing Grok, Perplexity, and other models."""
    
    @property
    def provider_name(self) -> str:
        return "openrouter"
    
    def _create_client(self):
        """OpenRouter uses REST API, no client needed."""
        api_key = self.api_key or settings.OPENROUTER_API_KEY
        if not api_key:
            raise ValueError("OpenRouter API key not configured")
        return None  # We'll use requests directly
    
    async def generate(
        self,
        model: str,
        query: str,
        system_prompt: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Tuple[str, List[Dict], Dict, Optional[Dict]]:
        """
        Generate response using OpenRouter API.
        
        Supports Grok, Perplexity, and other models with citation extraction.
        """
        api_key = self.api_key or settings.OPENROUTER_API_KEY
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "LLM Platform",
            "Content-Type": "application/json"
        }
        
        # Strip "openrouter/" prefix if sent by frontend
        if model.startswith("openrouter/"):
            model = model.split("openrouter/")[-1]
        
        system_message = system_prompt or "You are a helpful AI assistant."
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": query}
            ]
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=600
        )
        
        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ OpenRouter request failed: {e}")
            logger.error(f"Response text: {response.text}")
            raise
        
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        
        # --- Extract citations ---
        citations = []
        
        # Case 1: Perplexity models return `references` directly
        if "references" in data:
            for ref in data["references"]:
                citations.append({
                    "title": ref.get("title", ""),
                    "url": ref.get("url", ""),
                    "content": ref.get("content", "")
                })
        
        # Case 2: xAI / Grok or GPT-4o-mini:online style
        message = data["choices"][0]["message"]
        
        # A. annotations field (common for Grok and GPT-4o-mini:online)
        if "annotations" in message:
            for ann in message["annotations"]:
                if ann.get("type") == "url_citation":
                    citations.append({
                        "title": ann.get("title") or ann.get("url_citation", {}).get("title", ""),
                        "url": ann.get("url") or ann.get("url_citation", {}).get("url", ""),
                        "content": ann.get("content") or ann.get("url_citation", {}).get("content", "")
                    })
        
        # B. metadata.citations (used by OpenAI-style models on OpenRouter)
        elif "metadata" in message and "citations" in message["metadata"]:
            for c in message["metadata"]["citations"]:
                citations.append({
                    "title": c.get("title", ""),
                    "url": c.get("url", ""),
                    "content": c.get("snippet", "")
                })
        
        # Extract token usage
        tokens = None
        if "usage" in data:
            usage = data["usage"]
            tokens = {
                "prompt": usage.get("prompt_tokens", 0),
                "completion": usage.get("completion_tokens", 0),
                "total": usage.get("total_tokens", 0)
            }
        
        return text.strip(), citations, data, tokens
    
    def supports_streaming(self) -> bool:
        """OpenRouter supports streaming."""
        return True
    
    def supports_vision(self, model: str) -> bool:
        """Check if model supports vision (depends on underlying model)."""
        vision_keywords = ["vision", "gpt-4", "claude-3", "gemini-2"]
        return any(kw in model.lower() for kw in vision_keywords)
    
    def supports_web_search(self, model: str) -> bool:
        """
        Check if model supports web search.
        
        Perplexity and some Grok models have built-in search.
        """
        search_models = ["perplexity", "grok", "online"]
        return any(sm in model.lower() for sm in search_models)
