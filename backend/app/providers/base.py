"""
Base provider interface for LLM integrations.

All LLM providers must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional, AsyncGenerator
import logging

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.
    
    This defines the interface that all providers (OpenAI, Anthropic, Google, etc.)
    must implement for consistent behavior across the application.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the provider.
        
        Args:
            api_key: API key for the provider (optional, can load from config)
        """
        self.api_key = api_key
        self._client = None
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'openai', 'anthropic')."""
        pass
    
    @abstractmethod
    async def generate(
        self,
        model: str,
        query: str,
        system_prompt: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Tuple[str, List[Dict], Dict, Optional[Dict]]:
        """
        Generate a response from the LLM.
        
        Args:
            model: Model name/identifier
            query: User query/prompt
            system_prompt: Optional system prompt
            attachments: Optional file attachments (images, etc.)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Tuple of (response_text, citations, raw_response, tokens)
            - response_text: Generated text response
            - citations: List of source citations
            - raw_response: Raw API response (dict)
            - tokens: Token usage dict with 'prompt', 'completion', 'total' keys
        """
        pass
    
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Check if this provider supports streaming responses."""
        pass
    
    @abstractmethod
    def supports_vision(self, model: str) -> bool:
        """
        Check if the given model supports vision/image inputs.
        
        Args:
            model: Model name to check
            
        Returns:
            True if model supports image inputs
        """
        pass
    
    def supports_web_search(self, model: str) -> bool:
        """
        Check if the given model supports web search.
        
        Args:
            model: Model name to check
            
        Returns:
            True if model supports web search
        """
        return False  # Default: no web search support
    
    async def stream_generate(
        self,
        model: str,
        query: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream responses from the LLM (token by token).
        
        Args:
            model: Model name/identifier
            query: User query/prompt
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Dicts with streaming events:
            - {"type": "token", "content": "hello"}
            - {"type": "citation", "data": {...}}
            - {"type": "done", "metadata": {...}}
        """
        if not self.supports_streaming():
            raise NotImplementedError(f"{self.provider_name} does not support streaming")
        
        # Default implementation - providers should override
        raise NotImplementedError("Streaming not implemented for this provider")
    
    def _ensure_client(self):
        """Ensure the API client is initialized (lazy loading)."""
        if self._client is None:
            self._client = self._create_client()
        return self._client
    
    @abstractmethod
    def _create_client(self):
        """Create and return the API client instance."""
        pass
    
    def _extract_tokens(self, response: Any) -> Optional[Dict[str, int]]:
        """
        Extract token usage from response.
        
        Common helper method for extracting token counts.
        Providers can override if needed.
        
        Returns:
            Dict with 'prompt', 'completion', 'total' keys or None
        """
        return None
    
    def _format_citations(self, raw_citations: List[Any]) -> List[Dict[str, str]]:
        """
        Format raw citations into standard format.
        
        Args:
            raw_citations: Provider-specific citation data
            
        Returns:
            List of dicts with 'title', 'url', 'snippet' keys
        """
        return []
