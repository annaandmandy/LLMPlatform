"""
Multi-Agent System for LLM Platform

This package contains specialized agents for handling different types of queries:
- CoordinatorAgent: Routes requests to appropriate agents
- MemoryAgent: Handles summarization and RAG retrieval
- ProductAgent: Searches products and generates preview cards
- WriterAgent: Synthesizes final responses
"""

from .base_agent import BaseAgent
from .coordinator import CoordinatorAgent
from .memory_agent import MemoryAgent
from .product_agent import ProductAgent
from .writer_agent import WriterAgent

__all__ = [
    'BaseAgent',
    'CoordinatorAgent',
    'MemoryAgent',
    'ProductAgent',
    'WriterAgent'
]
