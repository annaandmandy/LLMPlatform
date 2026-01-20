"""
Query Service - Main service for handling LLM query processing.

Coordinates providers, memory, embeddings, and agents.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.providers.factory import ProviderFactory
from app.services.memory_service import memory_service
from app.services.embedding_service import embedding_service
from app.db.mongodb import get_db
from app.db.repositories.query_repo import QueryRepository
from app.schemas.query import QueryRequest, QueryResponse, QueryDocument
from app.agents import get_coordinator

logger = logging.getLogger(__name__)


class QueryService:
    """
    Service for processing user queries with LLMs.

    Handles the full query pipeline:
    1. Get memory context
    2. Generate embedding
    3. Process with LLM/agents
    4. Log to database
    """

    def __init__(self):
        """Initialize with repository."""
        self._repo = None

    @property
    def repo(self) -> QueryRepository:
        """Get repository instance (lazy initialization)."""
        if self._repo is None:
            db = get_db()
            if db is None:
                raise RuntimeError("Database not initialized")
            self._repo = QueryRepository(db)
        return self._repo

    async def process_query(
        self,
        request: QueryRequest
    ) -> QueryResponse:
        """
        Process a user query end-to-end.
        
        Args:
            request: QueryRequest with user_id, query, model info, etc.
            
        Returns:
            QueryResponse with generated response
        """
        start_time = datetime.utcnow()
        
        try:
            # 1. Generate embedding for the query
            query_embedding = await embedding_service.generate_embedding(request.query)
            
            # 2. Get memory context (always enabled)
            memory_context = await memory_service.get_memory_context(
                user_id=request.user_id,
                query=request.query,
                query_embedding=query_embedding,
                limit=5
            )
            
            # 3. Try multi-agent system first
            coordinator = get_coordinator()
            
            if coordinator:
                result = await self._process_with_agents(request, memory_context)
            else:
                # Fallback: Direct provider call
                logger.warning("Agents not available, using direct provider call")
                result = await self._process_with_provider(request, memory_context)
            
            # 4. Calculate latency
            end_time = datetime.utcnow()
            latency_ms = (end_time - start_time).total_seconds() * 1000
            
            # 5. Log to database
            await self._log_query(
                request=request,
                response=result["response"],
                embedding=query_embedding,
                memory_context=memory_context,
                result=result,
                latency_ms=latency_ms
            )
            
            # 6. Return response
            return QueryResponse(
                response=result["response"],
                citations=result.get("citations"),
                product_cards=result.get("product_cards"),
                product_json=result.get("product_json"),
                intent=result.get("intent"),
                agents_used=result.get("agents_used"),
                options=result.get("options"),
                shopping_status=result.get("shopping_status"),
                memory_context=memory_context,
                user_location=request.location
            )
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            raise
    
    async def _process_with_agents(
        self,
        request: QueryRequest,
        memory_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process query using multi-agent system."""
        # Use the dynamic Experiment Graph
        from app.services.experiment_service import experiment_service
        
        # Ensure graph is ready (lazy init fallback)
        try:
            graph = experiment_service.get_graph()
        except RuntimeError:
            await experiment_service.initialize()
            graph = experiment_service.get_graph()

        # Build initial AgentState
        # Note: We must align with AgentState definition in app.agents.graph (or schema)
        initial_state = {
            "query": request.query,
            "user_id": request.user_id,
            "session_id": request.session_id,
            "history": [h.model_dump() for h in (request.history or [])],
            "mode": request.mode,
            "attachments": request.attachments,
            "model": request.model_name or "gpt-4o-mini",
            # Inject memory context directly into state
            "memory_context": memory_context,
            
            # Initial defaults
            "agents_used": [],
            "intent": "general", 
            "response": None,
        }

        # Run the graph
        # ainvoke returns the final state
        final_state = await graph.ainvoke(initial_state)
        
        # Map final_state back to the dictionary expected by QueryService/API
        # The API expects keys like "response", "intent", "product_cards" etc.
        
        result = {
            "response": final_state.get("response"),
            "intent": final_state.get("intent"),
            "intent_confidence": final_state.get("intent_confidence", 1.0),
            "agents_used": final_state.get("agents_used", []),
            "citations": final_state.get("citations"),
            "product_cards": final_state.get("product_cards"),
            "product_json": final_state.get("structured_products"),
            "options": final_state.get("shopping_result", {}).get("options") if final_state.get("shopping_status") == "question" else final_state.get("options"), # handle variance in how options are stored
            "shopping_status": final_state.get("shopping_status"),
            "memory_context": final_state.get("memory_context"),
            "vision_notes": final_state.get("vision_notes"),
        }
        
        return result
    
    async def stream_query(
        self,
        request: QueryRequest
    ) -> Any:
        # Use the dynamic Experiment Graph
        from app.services.experiment_service import experiment_service
        
        # Ensure graph is ready
        try:
            graph = experiment_service.get_graph()
        except RuntimeError:
            await experiment_service.initialize()
            graph = experiment_service.get_graph()

        start_time = datetime.utcnow()
        
        # 1. Generate embedding
        query_embedding = await embedding_service.generate_embedding(request.query)
        
        # 2. Get memory context
        memory_context = await memory_service.get_memory_context(
            user_id=request.user_id,
            query=request.query,
            query_embedding=query_embedding,
            limit=5
        )

        # 3. Build AgentState
        initial_state = {
            "query": request.query,
            "user_id": request.user_id,
            "session_id": request.session_id,
            "history": [h.model_dump() for h in (request.history or [])],
            "mode": request.mode,
            "attachments": request.attachments,
            "model": request.model_name or "gpt-4o-mini",
            "memory_context": memory_context,
            "agents_used": [],
            "intent": "general", 
            "response": None,
        }

        full_response = ""
        full_citations = []
        full_product_cards = []
        full_options = []
        intent = "general"
        shopping_status = None
        
        # 4. Stream Events
        # We use astream_events to get internal updates
        async for event in graph.astream_events(initial_state, version="v1"):
            kind = event["event"]
            name = event["name"]
            data = event["data"]
            
            # Filter for specific events we want to surface to UI
            
            # Case A: Chain/Agent Start (Thought)
            # We filter for node IDs from the experiment config (lowercase) OR AgentType names
            # Map node IDs to friendly agent names
            agent_node_map = {
                "memory": "MemoryAgent",
                "vision": "VisionAgent", 
                "writer": "WriterAgent",
                "product": "ProductAgent",
                "shopping": "ShoppingAgent",
                "intent": "IntentAgent",
                # Also support class names directly
                "MemoryAgent": "MemoryAgent",
                "VisionAgent": "VisionAgent",
                "WriterAgent": "WriterAgent",
                "ProductAgent": "ProductAgent",
                "ShoppingAgent": "ShoppingAgent",
                "IntentAgent": "IntentAgent",
            }
            
            if kind == "on_chain_start" and name in agent_node_map:
                 yield {
                     "type": "thought",
                     "agent": agent_node_map[name],
                     "status": "started"
                 }
                 
            # Case B: LLM Streaming (Content)
            # We assume WriterAgent emits the final response via 'on_chat_model_stream'
            # Note: We need to be careful not to stream internal monologue if we add that later.
            # For now, any chat model stream in the graph is probably intended for user, 
            # OR we check if it's inside WriterAgent.
            elif kind == "on_chat_model_stream":
                # Check metadata or parent to ensure it's the response generation
                # For simplicity, we stream all chat tokens as 'chunk'.
                # Ideally check if 'writer' is in tags or parent.
                content = data["chunk"].content
                if content:
                    full_response += content
                    yield {
                        "type": "chunk",
                        "content": content
                    }
            
            # Case C: Node/Chain End (Accumulate detailed results)
            elif kind == "on_chain_end":
                 output = data.get("output")
                 if output and isinstance(output, dict):
                     # Check for WriterAgent response (since it doesn't use LangChain streaming)
                     if "response" in output and output["response"] and not full_response:
                         # Emit the entire response as a single chunk
                         full_response = output["response"]
                         yield {
                             "type": "chunk",
                             "content": full_response
                         }
                     if "citations" in output and output["citations"]:
                         full_citations = output["citations"]
                         yield {
                             "type": "node",
                             "node_type": "citations",
                             "citations": full_citations
                         }
                     if "products" in output and output["products"]:
                         full_product_cards = output["products"]
                         yield {
                             "type": "node",
                             "node_type": "product_cards",
                             "product_cards": full_product_cards
                         }
                     elif "product_cards" in output and output["product_cards"]:
                         full_product_cards = output["product_cards"]
                         yield {
                             "type": "node",
                             "node_type": "product_cards",
                             "product_cards": full_product_cards
                         }
                     if "intent" in output:
                         intent = output["intent"]
                         
        # 5. Log after stream
        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000
        
        result = {
            "intent": intent, # This might need to be extracted better from state
            "citations": full_citations,
            "product_cards": full_product_cards,
            "options": full_options,
            "shopping_status": shopping_status,
            "tokens": {}
        }
        
        # Note: Logging might be slightly incomplete without the final state object
        # but we have the accumulated response.
        await self._log_query(
            request=request,
            response=full_response,
            embedding=query_embedding,
            memory_context=memory_context,
            result=result,
            latency_ms=latency_ms
        )
        
        # Yield final DONE
        yield {"type": "done", "message": "Query complete"}
    
    async def _process_with_provider(
        self,
        request: QueryRequest,
        memory_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback: Direct provider call without agents."""
        
        # Get provider
        provider = ProviderFactory.get_provider(request.model_provider)
        
        # Build system prompt with memory
        memory_str = memory_service.format_memory_for_prompt(memory_context)
        system_prompt = "You are a helpful AI assistant."
        if memory_str:
            system_prompt += f"\n\nContext from previous conversations:\n{memory_str}"
        
        # Call provider
        response_text, citations, raw_response, tokens = await provider.generate(
            model=request.model_name or "gpt-4o-mini",
            query=request.query,
            system_prompt=system_prompt,
            attachments=request.attachments
        )
        
        return {
            "response": response_text,
            "citations": citations,
            "tokens": tokens,
            "intent": None,
            "agents_used": [],
            "product_cards": None,
            "product_json": None,
            "options": None,
            "shopping_status": None
        }
    
    async def _log_query(
        self,
        request: QueryRequest,
        response: str,
        embedding: List[float],
        memory_context: Dict[str, Any],
        result: Dict[str, Any],
        latency_ms: float
    ):
        """Log query to database."""
        try:
            # Build metadata from request and result
            metadata = {
                "model_provider": request.model_provider,
                "model_name": request.model_name,
                "intent": result.get("intent"),
                "mode": request.mode,
                "attachments": request.attachments,
                "user_location": request.location.model_dump() if request.location else None,
                "citations": result.get("citations"),
                "product_cards": result.get("product_cards"),
                "agents_used": result.get("agents_used"),
                "memory_context": memory_context,
                "shopping_status": result.get("shopping_status"),
                "shopping_options": result.get("options"),
                "latency_ms": latency_ms,
                "tokens": result.get("tokens"),
                "success": True
            }

            # Use repository to create query log
            await self.repo.create_query_log(
                user_id=request.user_id,
                session_id=request.session_id,
                query=request.query,
                response=response,
                embedding=embedding,
                metadata=metadata
            )

            logger.info(f"Query logged: {request.user_id}/{request.session_id}")

        except Exception as e:
            logger.error(f"Failed to log query: {e}")


# Global instance
query_service = QueryService()
