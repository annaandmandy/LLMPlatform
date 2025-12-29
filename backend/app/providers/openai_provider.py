"""
OpenAI provider implementation.

Supports GPT models with web search capabilities.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from openai import OpenAI

from app.providers.base import BaseLLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider with web search support."""
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    def _create_client(self):
        """Create OpenAI client."""
        api_key = self.api_key or settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OpenAI API key not configured")
        return OpenAI(api_key=api_key)
    
    async def generate(
        self,
        model: str,
        query: str,
        system_prompt: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Tuple[str, List[Dict], Dict, Optional[Dict]]:
        """
        Generate response using OpenAI API.
        
        Supports both Chat Completions API (for search models) and Responses API.
        """
        client = self._ensure_client()
        
        system_message = system_prompt or "You are a helpful AI assistant."
        
        def _build_messages(include_images: bool):
            """Build message array for API call."""
            user_content: Any
            if include_images and attachments:
                parts = [{"type": "text", "text": query}]
                for att in attachments:
                    if att.get("type") == "image" and att.get("base64"):
                        parts.append({
                            "type": "image_url",
                            "image_url": {"url": att["base64"]}
                        })
                user_content = parts
            else:
                user_content = query
            
            return [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_content},
            ]
        
        # Detect built-in search models
        use_chat_api = any(tag in model for tag in ["search-preview", "search-api"])
        
        if use_chat_api:
            # Chat Completions API for web-search-enabled models
            include_images = bool(attachments)
            messages = _build_messages(include_images)
            
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages
                )
            except Exception as err:
                # Retry without images if quota/rate limit hit
                if include_images and "input-images" in str(err).lower():
                    logger.warning("Image quota/rate limit hit for OpenAI; retrying without images")
                    messages = _build_messages(False)
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages
                    )
                else:
                    raise
            
            msg = response.choices[0].message
            text = msg.content or ""
            sources = []
            
            # Extract annotations (citations)
            if hasattr(msg, "annotations"):
                for ann in msg.annotations:
                    ann_type = getattr(ann, "type", None)
                    if ann_type == "url_citation":
                        uc = getattr(ann, "url_citation", {})
                        sources.append({
                            "title": getattr(uc, "title", "") or uc.get("title", ""),
                            "url": getattr(uc, "url", "") or uc.get("url", "")
                        })
        
        else:
            # Responses API for standard models
            messages = _build_messages(bool(attachments))
            response = client.responses.create(
                model=model,
                input=messages,
                tools=[{"type": "web_search"}]
            )
            
            text, sources = "", []
            for item in getattr(response, "output", []):
                for content in getattr(item, "content", []) or []:
                    if getattr(content, "type", None) == "output_text":
                        text += getattr(content, "text", "")
                    
                    # Extract citations from annotations
                    for ann in getattr(content, "annotations", []) or []:
                        if getattr(ann, "type", None) == "url_citation":
                            sources.append({
                                "title": getattr(ann, "title", ""),
                                "url": getattr(ann, "url", "")
                            })
        
        # Extract token usage
        tokens = None
        if hasattr(response, "usage"):
            usage = response.usage
            tokens = {
                "prompt": getattr(usage, "prompt_tokens", 0),
                "completion": getattr(usage, "completion_tokens", 0),
                "total": getattr(usage, "total_tokens", 0)
            }
        
        # Get raw response
        raw = getattr(response, "model_dump", lambda: {})()
        
        return text.strip(), sources, raw, tokens
    
    def supports_streaming(self) -> bool:
        """OpenAI supports streaming."""
        return True
    
    def supports_vision(self, model: str) -> bool:
        """Check if model supports vision."""
        vision_models = ["gpt-4", "gpt-4o", "vision"]
        return any(vm in model.lower() for vm in vision_models)
    
    def supports_web_search(self, model: str) -> bool:
        """Check if model supports web search."""
        return "search" in model.lower()
