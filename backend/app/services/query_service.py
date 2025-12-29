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
        coordinator = get_coordinator()
        
        # Build agent request
        agent_request = {
            "query": request.query,
            "user_id": request.user_id,
            "session_id": request.session_id,
            "model_provider": request.model_provider,
            "model_name": request.model_name,
            "mode": request.mode,
            "memory_context": memory_context,
            "location": request.location.model_dump() if request.location else None,
            "attachments": request.attachments,
        }
        
        # Process through coordinator
        result = await coordinator.process(agent_request)
        
        return result
    
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
        db = get_db()
        if db is None:
            logger.warning("Database not available, skipping query log")
            return
        
        queries_collection = db["queries"]
        
        # Build query document
        query_doc = QueryDocument(
            user_id=request.user_id,
            session_id=request.session_id,
            query=request.query,
            response=response,
            model_provider=request.model_provider,
            model_name=request.model_name,
            embedding=embedding,
            intent=result.get("intent"),
            mode=request.mode,
            attachments=request.attachments,
            user_location=request.location.model_dump() if request.location else None,
            citations=result.get("citations"),
            product_cards=result.get("product_cards"),
            agents_used=result.get("agents_used"),
            memory_context=memory_context,
            shopping_status=result.get("shopping_status"),
            shopping_options=result.get("options"),
            timestamp=datetime.utcnow().isoformat(),
            created_at=datetime.utcnow().isoformat(),
            latency_ms=latency_ms,
            tokens=result.get("tokens"),
            success=True
        )
        
        # Insert into database
        try:
            await queries_collection.insert_one(query_doc.model_dump(exclude_none=True))
            logger.info(f"Query logged: {request.user_id}/{request.session_id}")
        except Exception as e:
            logger.error(f"Failed to log query: {e}")


# Global instance
query_service = QueryService()
