"""
Anthropic (Claude) provider implementation.

Supports Claude models with web search capabilities.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
import anthropic

from app.providers.base import BaseLLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider with web search support."""
    
    @property
    def provider_name(self) -> str:
        return"anthropic"
    
    def _create_client(self):
        """Create Anthropic client."""
        api_key = self.api_key or settings.ANTHROPIC_API_KEY
        if not api_key:
            raise ValueError("Anthropic API key not configured")
        return anthropic.Anthropic(api_key=api_key)
    
    async def generate(
        self,
        model: str,
        query: str,
        system_prompt: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Tuple[str, List[Dict], Dict, Optional[Dict]]:
        """
        Generate response using Anthropic Claude API.
        
        Supports web_search_20250305 tool for citations.
        """
        client = self._ensure_client()
        
        system_message = system_prompt or "You are a helpful AI assistant."
        
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 5
            }],
            system=system_message,
            messages=[{"role": "user", "content": query}]
        )
        
        text_parts = []
        citations = []
        
        # Safely iterate content blocks (these are typed SDK objects)
        for block in getattr(response, "content", []):
            # Get block type
            block_type = getattr(block, "type", None) or (
                block.get("type") if isinstance(block, dict) else None
            )
            
            # ---- TEXT BLOCKS ----
            if block_type == "text":
                text_value = getattr(block, "text", "") or (
                    block.get("text") if isinstance(block, dict) else ""
                )
                text_parts.append(text_value)
                
                # Extract inline citations
                block_citations = getattr(block, "citations", []) or (
                    block.get("citations") if isinstance(block, dict) else []
                )
                for cite in block_citations or []:
                    citations.append({
                        "title": getattr(cite, "title", "") or (
                            cite.get("title") if isinstance(cite, dict) else ""
                        ),
                        "url": getattr(cite, "url", "") or (
                            cite.get("url") if isinstance(cite, dict) else ""
                        ),
                        "snippet": getattr(cite, "cited_text", "") or (
                            cite.get("cited_text") if isinstance(cite, dict) else ""
                        )
                    })
            
            # ---- WEB SEARCH RESULTS ----
            elif block_type == "web_search_tool_result":
                block_content = getattr(block, "content", []) or (
                    block.get("content") if isinstance(block, dict) else []
                )
                for result in block_content or []:
                    result_type = getattr(result, "type", None) or (
                        result.get("type") if isinstance(result, dict) else None
                    )
                    if result_type == "web_search_result":
                        citations.append({
                            "title": getattr(result, "title", "") or (
                                result.get("title") if isinstance(result, dict) else ""
                            ),
                            "url": getattr(result, "url", "") or (
                                result.get("url") if isinstance(result, dict) else ""
                            ),
                            "snippet": getattr(result, "page_age", "") or (
                                result.get("page_age") if isinstance(result, dict) else ""
                            )
                        })
        
        # Remove duplicates by URL
        seen, unique = set(), []
        for c in citations:
            url = c.get("url")
            if url and url not in seen:
                seen.add(url)
                unique.append(c)
        
        # Extract token usage
        tokens = None
        if hasattr(response, "usage"):
            usage = response.usage
            tokens = {
                "prompt": getattr(usage, "input_tokens", 0),
                "completion": getattr(usage, "output_tokens", 0),
                "total": getattr(usage, "input_tokens", 0) + getattr(usage, "output_tokens", 0)
            }
        
        text = "\n".join(text_parts).strip()
        raw = response.model_dump()
        
        return text, unique, raw, tokens
    
    def supports_streaming(self) -> bool:
        """Anthropic supports streaming."""
        return True
    
    def supports_vision(self, model: str) -> bool:
        """Claude 3+ models support vision."""
        vision_models = ["claude-3", "claude-3.5", "claude-3.7"]
        return any(vm in model.lower() for vm in vision_models)
    
    def supports_web_search(self, model: str) -> bool:
        """All Claude models support web search via tools."""
        return True
