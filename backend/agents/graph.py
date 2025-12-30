import logging
import operator
from typing import TypedDict, Annotated, List, Dict, Any, Optional, Literal
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)

# -- Global Agent Registry --
_agents = {}

def set_agents(agents_dict: Dict[str, Any]):
    """Inject initialized agents into the graph module."""
    global _agents
    _agents = agents_dict
    logger.info("Agents injected into graph: %s", list(_agents.keys()))

# -- State Definition --
class AgentState(TypedDict):
    # Inputs
    query: str
    user_id: str
    session_id: str
    history: List[Dict[str, str]]
    mode: str
    attachments: Optional[List[Dict[str, Any]]]
    location: Optional[Dict[str, Any]]
    model: str
    
    # Internal & Outputs
    intent: str
    intent_confidence: Optional[float]
    memory_context: Optional[Dict[str, Any]]
    vision_notes: Optional[str]
    
    shopping_status: Optional[str]
    shopping_result: Optional[Dict[str, Any]]
    
    response: Optional[str]
    citations: Optional[List[Dict[str, Any]]]
    product_cards: Optional[List[Dict[str, Any]]]
    structured_products: Optional[List[Dict[str, Any]]]
    
    # Reducer for list accumulation
    agents_used: Annotated[List[str], operator.add]

# -- Nodes --

async def memory_node(state: AgentState):
    agent = _agents.get("memory_agent")
    if not agent:
        return {}
    
    try:
        mem_result = await agent.run({
            "action": "context_bundle",
            "query": state["query"],
            "session_id": state["session_id"],
            "user_id": state["user_id"],
        })
        return {
            "memory_context": mem_result["output"], 
            "agents_used": ["MemoryAgent"]
        }
    except Exception as e:
        logger.error(f"MemoryAgent failed: {e}")
        return {}

async def vision_node(state: AgentState):
    agent = _agents.get("vision_agent")
    if not agent or not state.get("attachments"):
        return {}
    
    try:
        vision_result = await agent.run({
            "query": state["query"],
            "attachments": state.get("attachments", []),
            "session_id": state["session_id"],
            "user_id": state["user_id"],
        })
        return {
            "vision_notes": vision_result.get("output", {}).get("vision_notes", ""), 
            "agents_used": ["VisionAgent"]
        }
    except Exception as e:
        logger.error(f"VisionAgent failed: {e}")
        return {}

async def intent_node(state: AgentState):
    # We import here to avoid potential circular initializations if any
    from utils.intent_classifier import detect_intent
    
    # Check if we forced intent (e.g. from shopping completion previously) 
    # Actually, in this graph, if shopping completes, we might loop back or handle it.
    # But for now, let's just detect fresh content.
    
    intent_res = await detect_intent(state["query"])
    return {
        "intent": intent_res["intent"],
        "intent_confidence": intent_res["confidence"],
        "agents_used": ["IntentClassifier"]
    }

async def shopping_node(state: AgentState):
    agent = _agents.get("shopping_agent")
    if not agent:
        return {"shopping_status": "complete"}

    try:
        req = {
            "query": state["query"],
            "history": state.get("history", []),
            "session_id": state["session_id"]
        }
        res = await agent.run(req)
        out = res["output"]
        
        updates = {
            "shopping_status": out["status"],
            "agents_used": ["ShoppingAgent"]
        }
        
        if out["status"] == "question":
            updates["response"] = out["response"]
            updates["shopping_result"] = {"options": out.get("options", [])}
        elif out["status"] == "complete":
            # Update query to synthesized search query
            updates["query"] = out["search_query"]
            # Force intent to product search
            updates["intent"] = "product_search"
            
        return updates
    except Exception as e:
        logger.error(f"ShoppingAgent failed: {e}")
        return {"shopping_status": "complete"}

async def writer_node(state: AgentState):
    agent = _agents.get("writer_agent")
    if not agent:
        return {"response": "System Error: WriterAgent unavailable."}
        
    req = {
        "query": state["query"],
        "intent": state.get("intent", "general"),
        "model": state.get("model", "gpt-4o-mini"),
        "memory_context": state.get("memory_context"),
        "product_cards": state.get("product_cards"),
        "history": state.get("history", []),
        "location": state.get("location"),
        "vision_notes": state.get("vision_notes"),
        "attachments": state.get("attachments"),
    }
    
    try:
        res = await agent.run(req)
        out = res["output"]
        return {
            "response": out["response"],
            "citations": out.get("citations"),
            "agents_used": ["WriterAgent"]
        }
    except Exception as e:
        logger.error(f"WriterAgent failed: {e}")
        return {"response": "I encountered an error generating the response."}

async def product_node(state: AgentState):
    agent = _agents.get("product_agent")
    if not agent:
        return {}
        
    req = {
        "query": state["query"],
        "llm_response": state.get("response", ""),
        "max_results": 1
    }
    
    try:
        res = await agent.run(req)
        out = res["output"]
        return {
            "product_cards": out.get("products"),
            "structured_products": out.get("structured_products"),
            "agents_used": ["ProductAgent"]
        }
    except Exception as e:
        logger.error(f"ProductAgent failed: {e}")
        return {}

# -- Graph Construction --
workflow = StateGraph(AgentState)

workflow.add_node("memory", memory_node)
workflow.add_node("vision", vision_node)
workflow.add_node("intent", intent_node)
workflow.add_node("shopping", shopping_node)
workflow.add_node("writer", writer_node)
workflow.add_node("product", product_node)

# Entry
workflow.set_entry_point("memory")

# Edges
workflow.add_edge("memory", "vision")
workflow.add_edge("vision", "intent")

def route_after_intent(state: AgentState):
    mode = state.get("mode", "chat")
    intent = state.get("intent", "general")
    
    if mode == "shopping":
        return "shopping"
    elif intent == "product_search":
        return "writer"
    else:
        return "writer"

workflow.add_conditional_edges(
    "intent",
    route_after_intent,
    {
        "shopping": "shopping",
        "writer": "writer"
    }
)

def route_after_shopping(state: AgentState):
    status = state.get("shopping_status")
    if status == "question":
        return END
    return "writer"

workflow.add_conditional_edges(
    "shopping",
    route_after_shopping,
    {
        END: END,
        "writer": "writer"
    }
)

def route_after_writer(state: AgentState):
    intent = state.get("intent")
    if intent == "product_search":
        return "product"
    return END

workflow.add_conditional_edges(
    "writer",
    route_after_writer,
    {
        "product": "product",
        END: END
    }
)

workflow.add_edge("product", END)

# Compile
graph_app = workflow.compile()
