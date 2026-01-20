"""
Graph Loader (Factory).

Builds a compiled StateGraph from an ExperimentConfig.
"""

import json
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from app.experiments.schema import ExperimentConfig, AgentConfig
from app.experiments.registry import get_agent_class, get_condition

# Import AgentState from original graph to ensure compatibility
# In a full refactor, AgentState should probably move to a shared schema file.
from app.agents.graph import AgentState

logger = logging.getLogger(__name__)

class ExperimentLoader:
    """Factory class to build graphs from config."""

    @staticmethod
    def load_config(file_path: str) -> ExperimentConfig:
        """Load JSON config file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        return ExperimentConfig(**data)

    @staticmethod
    def build_graph(config: ExperimentConfig) -> Any:
        """
        Construct a StateGraph based on the configuration.
        """
        workflow = StateGraph(AgentState)
        
        # 1. Initialize and Add Nodes
        # We need to hold references to initialized agents to pass to 'set_agents' later if needed,
        # or we just rely on the node function wrapper structure.
        
        # For LangGraph integration, we usually define a node function like:
        # async def memory_node(state): ...
        
        # To make this dynamic, we'll create a closure/wrapper for each agent.
        
        for agent_conf in config.agents:
            node_func = ExperimentLoader._create_node_func(agent_conf)
            workflow.add_node(agent_conf.id, node_func)
            
        # 2. Add Edges
        for edge in config.edges:
            if edge.condition:
                # Conditional Edge
                condition_func = get_condition(edge.condition)
                
                # The path map in config keys are strings, values are node IDs.
                # key "end" or value "__end__" maps to END constant
                path_map = {}
                if edge.path_map:
                    for k, v in edge.path_map.items():
                        target = END if v == "__end__" else v
                        path_map[k] = target
                        
                workflow.add_conditional_edges(
                    edge.source,
                    condition_func,
                    path_map
                )
            else:
                # Normal Edge
                target = END if edge.target == "__end__" else edge.target
                workflow.add_edge(edge.source, target)
                
        # 3. Set Entry Point
        workflow.set_entry_point(config.entry_point)
        
        # 4. Compile
        return workflow.compile()

    @staticmethod
    def _create_node_func(agent_conf: AgentConfig):
        """
        Creates a wrapper function compatible with LangGraph node signature.
        This wrapper instantiates or retrieves the agent and runs it.
        """
        AgentClass = get_agent_class(agent_conf.type)
        
        # Initialize the agent instance. 
        # NOTE: Ideally agents are stateless or refreshed per request. 
        # If they rely on `self.db` passed during init, we need to handle that.
        # For the prototype, we assume we can init them here or use a global provider.
        # Reviewing `memory_agent.py`, it takes `db`. 
        # We might need to rely on the `get_db()` dependency injection within the `run` method 
        # OR initialize them with a DB connection here.
        
        # For this implementation, we will perform a lightweight init (no DB) 
        # and assume the agent's `run` or `execute` method handles grabbing dependencies 
        # via the `get_db` helper or similar pattern, OR we update agents to accept deps at runtime.
        
        # Checking `memory_agent.py`: __init__ takes (db, summary_interval).
        # We can't easily pass the async motor DB here in a sync factory if we cache this graph.
        # BUT `graph.py` uses `_agents` global.
        
        # STRATEGY: We will create a node function that instantiates the agent on the fly 
        # OR retrieves it from a context.
        # Best practice for LangGraph is usually passing dependencies in `state` or closure.
        
        # Let's try to instantiate a "Runner" that can look up the DB at runtime.
        
        async def node_wrapper(state: AgentState):
            from app.db.mongodb import get_db
            db = get_db() # Get the thread-local/context-local DB
            
            # Instantiate Agent with DB
            # We assume all agents accept `db` as first arg or kwarg.
            agent_instance = AgentClass(db=db, **agent_conf.config)
            
            # Configure WriterAgent with LLM functions
            if agent_conf.type == "WriterAgent":
                from app.providers.factory import ProviderFactory
                llm_functions = ProviderFactory.get_all_providers()
                agent_instance.set_llm_functions(llm_functions)
            
            # Prepare input for agent
            # Most agents expect a dict with keys like "query", "session_id", etc.
            # We map state to that dict.
            req = {
                "query": state["query"],
                "session_id": state["session_id"],
                "user_id": state["user_id"],
                "history": state.get("history", []),
                "chunk_id": state.get("chunk_id"), # if needed
                # Add other state fields as needed by specific agents
                "action": "retrieve", # Default for memory? Needs config.
                "attachments": state.get("attachments"),
                "llm_response": state.get("response"), # For product agent
                "intent": state.get("intent"),
                "memory_context": state.get("memory_context"),
                "product_cards": state.get("product_cards"),
                "vision_notes": state.get("vision_notes"),
                "shopping_status": state.get("shopping_status")
            }
            
            # The agent `run` or `execute` maps inputs -> outputs
            try:
                # Pre-check for VisionAgent to avoid running if no images
                if agent_conf.type == "VisionAgent":
                    atts = req.get("attachments") or []
                    if not any(att.get("type") == "image" for att in atts):
                        return {}

                # `BaseAgent.run` expects a dict
                result = await agent_instance.run(req)
                output = result.get("output", {})
                
                # Now map output back to AgentState updates
                updates = {}
                
                # This mapping is specific to each agent type often.
                # We might need `AgentConfig` to define "output_map"
                # For now, we'll do some basic heuristic mapping based on Agent Name
                
                if agent_conf.type == "MemoryAgent":
                    updates["memory_context"] = output
                    
                elif agent_conf.type == "VisionAgent":
                    # Check if there are any actual images
                    atts = req.get("attachments") or []
                    has_images = any(att.get("type") == "image" for att in atts)
                    
                    if has_images:
                        updates["vision_notes"] = output.get("vision_notes")
                    else:
                        # If no images, we shouldn't have run, but if we did/are here, 
                        # just ensure we don't return partial notes or errors.
                        # Ideally we skip earlier, but identifying 'VisionAgent' dynamically 
                        # to skip invocation requires checking before 'await agent_instance.run(req)'
                        updates["vision_notes"] = ""
                    
                elif agent_conf.type == "ShoppingAgent":
                     updates["shopping_status"] = output.get("status")
                     updates["shopping_result"] = output
                     if output.get("status") == "question":
                         updates["response"] = output.get("response")
                     elif output.get("search_query"):
                         updates["query"] = output.get("search_query")
                         updates["intent"] = "product_search" # Force intent
                         
                elif agent_conf.type == "WriterAgent":
                    updates["response"] = output.get("response")
                    updates["citations"] = output.get("citations")
                    
                elif agent_conf.type == "ProductAgent":
                    updates["product_cards"] = output.get("products")
                    updates["structured_products"] = output.get("structured_products")

                elif agent_conf.type == "IntentAgent":
                    updates["intent"] = output.get("intent")
                    updates["intent_confidence"] = output.get("intent_confidence")
                    
                # Generic fallback
                if "agents_used" not in updates:
                     updates["agents_used"] = [agent_conf.type]
                else:
                     updates["agents_used"].append(agent_conf.type)
                     
                return updates
                
            except Exception as e:
                logger.error(f"Error in node {agent_conf.id}: {e}")
                return {"response": f"System Error in {agent_conf.id}"}

        return node_wrapper
