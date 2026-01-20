"""
Registry for Agents and Tools.

Maps string identifiers to actual Python classes/functions for dynamic graph building.
"""

from typing import Type, Any, Dict, Callable

# Import your existing agents here
from app.agents.memory_agent import MemoryAgent
from app.agents.vision_agent import VisionAgent
from app.agents.shopping_agent import ShoppingAgent
from app.agents.writer_agent import WriterAgent
from app.agents.product_agent import ProductAgent
from app.agents.coordinator import CoordinatorAgent
from app.agents.intent_agent import IntentAgent

from app.experiments.conditions import route_intent, route_shopping, route_product, route_vision
from app.tools.web_scraper import scrape_web
from app.tools.file_search import search_files

# Define a type for Agent Classes (approximate)
AgentClass = Type[Any] 

_AGENT_REGISTRY: Dict[str, AgentClass] = {
    "MemoryAgent": MemoryAgent,
    "VisionAgent": VisionAgent,
    "ShoppingAgent": ShoppingAgent,
    "WriterAgent": WriterAgent,
    "ProductAgent": ProductAgent,
    "ProductAgent": ProductAgent,
    "CoordinatorAgent": CoordinatorAgent,
    "IntentAgent": IntentAgent,
}

_TOOL_REGISTRY: Dict[str, Any] = {
    # Placeholders for future tools (e.g. Firecrawl, FileSearch)
    "web_search": scrape_web,
    "scrape_web": scrape_web,
    "file_search": search_files,
}

_CONDITION_REGISTRY: Dict[str, Callable] = {
    "route_intent": route_intent,
    "route_shopping": route_shopping,
    "route_product": route_product,
    "route_vision": route_vision,
}

def get_agent_class(name: str) -> AgentClass:
    """Retrieve an Agent class by name."""
    if name not in _AGENT_REGISTRY:
        raise ValueError(f"Agent type '{name}' not found in registry. Available: {list(_AGENT_REGISTRY.keys())}")
    return _AGENT_REGISTRY[name]

def get_tool(name: str) -> Any:
    """Retrieve a Tool by name."""
    if name not in _TOOL_REGISTRY:
        raise ValueError(f"Tool '{name}' not found in registry.")
    return _TOOL_REGISTRY[name]

def register_agent(name: str, cls: AgentClass):
    """Register a new agent type dynamically."""
    _AGENT_REGISTRY[name] = cls

def register_condition(name: str, func: Callable):
    """Register a condition function."""
    _CONDITION_REGISTRY[name] = func

def get_condition(name: str) -> Callable:
    if name not in _CONDITION_REGISTRY:
         raise ValueError(f"Condition '{name}' not found in registry.")
    return _CONDITION_REGISTRY[name]
