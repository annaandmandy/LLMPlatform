"""
Multi-Agent System for LLM Platform

This package contains specialized agents for handling different types of queries:
- CoordinatorAgent: Routes requests to appropriate agents
- MemoryAgent: Handles summarization and RAG retrieval
- ProductAgent: Searches products and generates preview cards
- WriterAgent: Synthesizes final responses
"""

import logging
from typing import Optional

from .base_agent import BaseAgent
from .coordinator import CoordinatorAgent
from .memory_agent import MemoryAgent
from .product_agent import ProductAgent
from .writer_agent import WriterAgent
from .vision_agent import VisionAgent
from .shopping_agent import ShoppingAgent

logger = logging.getLogger(__name__)

__all__ = [
    'BaseAgent',
    'CoordinatorAgent',
    'MemoryAgent',
    'ProductAgent',
    'WriterAgent',
    'VisionAgent',
    'ShoppingAgent',
    'initialize_agents',
]


# Global agent instances
coordinator_agent: Optional[CoordinatorAgent] = None
memory_agent: Optional[MemoryAgent] = None
product_agent: Optional[ProductAgent] = None
writer_agent: Optional[WriterAgent] = None
vision_agent: Optional[VisionAgent] = None
shopping_agent: Optional[ShoppingAgent] = None


async def initialize_agents(db):
    """
    Initialize the multi-agent system.
    
    This function creates and configures all agents, links them together,
    and injects them into the LangGraph workflow.
    
    Args:
        db: MongoDB database instance
        
    Returns:
        dict: Dictionary of initialized agents
        
    Raises:
        Exception: If agent initialization fails
    """
    global coordinator_agent, memory_agent, product_agent, writer_agent, vision_agent, shopping_agent
    
    try:
        logger.info("🤖 Initializing multi-agent system...")
        
        # Initialize individual agents
        memory_agent = MemoryAgent(db=db)
        product_agent = ProductAgent(db=db)
        writer_agent = WriterAgent(db=db)
        vision_agent = VisionAgent(db=db)
        shopping_agent = ShoppingAgent(db=db)
        coordinator_agent = CoordinatorAgent(db=db)
        
        # Configure WriterAgent with LLM functions
        llm_functions = _get_llm_functions()
        if llm_functions:
            writer_agent.set_llm_functions(llm_functions)
        else:
            logger.warning("⚠️ LLM functions not configured - WriterAgent may not work correctly")
        
        # Link agents to coordinator (for backward compatibility)
        coordinator_agent.set_agents(
            memory_agent,
            product_agent,
            writer_agent,
            vision_agent,
            shopping_agent
        )
        
        # Inject agents into LangGraph
        from .graph import set_agents
        set_agents({
            "memory_agent": memory_agent,
            "product_agent": product_agent,
            "writer_agent": writer_agent,
            "vision_agent": vision_agent,
            "shopping_agent": shopping_agent,
            "coordinator_agent": coordinator_agent
        })
        
        logger.info("✅ Multi-agent system initialized successfully")
        
        return {
            "coordinator_agent": coordinator_agent,
            "memory_agent": memory_agent,
            "product_agent": product_agent,
            "writer_agent": writer_agent,
            "vision_agent": vision_agent,
            "shopping_agent": shopping_agent,
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize multi-agent system: {e}")
        raise


def _get_llm_functions():
    """
    Get LLM provider functions for WriterAgent.
    
    This will be updated after provider migration to import from app.providers.
    For now, it attempts to import from the old main.py if available.
    
    Returns:
        dict: Dictionary of LLM provider functions
    """
    try:
        # TODO: Update this after provider migration (Phase 3)
        # Will become:
        # from app.providers.factory import ProviderFactory
        # return ProviderFactory.get_all_providers()
        
        # For now, try to import from old main.py
        import sys
        from pathlib import Path
        
        old_main_path = Path(__file__).parent.parent / "main.py"
        if old_main_path.exists():
            logger.info("Attempting to import LLM functions from existing main.py")
            
            # Import the functions
            import importlib.util
            spec = importlib.util.spec_from_file_location("main", old_main_path)
            if spec and spec.loader:
                main_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(main_module)
                
                # Get the call_* functions
                return {
                    "openai": getattr(main_module, "call_openai", None),
                    "anthropic": getattr(main_module, "call_anthropic", None),
                    "google": getattr(main_module, "call_gemini", None),
                    "openrouter": getattr(main_module, "call_openrouter", None),
                    "openrouter_perplexity": getattr(main_module, "call_openrouter", None),
                    "openrouter_grok": getattr(main_module, "call_openrouter", None),
                }
        
        logger.warning("⚠️ LLM functions not available. Provider migration needed.")
        return {}
        
    except Exception as e:
        logger.warning(f"Could not load LLM functions: {e}")
        return {}


def get_coordinator() -> Optional[CoordinatorAgent]:
    """Get the coordinator agent instance."""
    return coordinator_agent


def get_memory_agent() -> Optional[MemoryAgent]:
    """Get the memory agent instance."""
    return memory_agent


def get_product_agent() -> Optional[ProductAgent]:
    """Get the product agent instance."""
    return product_agent


def get_writer_agent() -> Optional[WriterAgent]:
    """Get the writer agent instance."""
    return writer_agent


def get_shopping_agent() -> Optional[ShoppingAgent]:
    """Get the shopping agent instance."""
    return shopping_agent


def get_vision_agent() -> Optional[VisionAgent]:
    """Get the vision agent instance."""
    return vision_agent


def are_agents_initialized() -> bool:
    """Check if agents have been initialized."""
    return coordinator_agent is not None
