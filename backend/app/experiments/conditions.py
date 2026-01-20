"""
Condition Functions for Graph Routing.

These functions determine which path the graph takes at conditional edges.
"""

from typing import Literal, Dict, Any

# We need the AgentState definition. 
# It is currently in graph.py, but circular imports might be tricky.
# For now, we'll assume 'state' is a Dict or TypedDict compatible object.

def route_intent(state: Dict[str, Any]) -> str:
    """Route based on detected intent."""
    mode = state.get("mode", "chat")
    intent = state.get("intent", "general")
    
    if mode == "shopping":
        return "shopping"
    elif intent == "product_search":
        return "product_search"
    else:
        return "general"

def route_shopping(state: Dict[str, Any]) -> str:
    """Route after shopping node."""
    status = state.get("shopping_status")
    if status == "question":
        return "end" # In original graph this was END
    return "continue"

def route_product(state: Dict[str, Any]) -> str:
    """Route after product node."""
    # In the original graph, product always went to END.
    # But for flexibility, let's allow it to potentially loop or go elsewhere.
    # Route based on intent (mirroring original graph logic)
    intent = state.get("intent")
    if intent == "product_search":
        return "product"
    return "end"

def route_vision(state: Dict[str, Any]) -> str:
    """Route to vision agent only if images are present."""
    attachments = state.get("attachments", []) or []
    has_images = any(att.get("type") == "image" for att in attachments)
    return "vision" if has_images else "no_vision"

