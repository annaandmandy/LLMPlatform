"""
Query Routes - Main endpoints for LLM query processing.

Handles both standard and streaming query requests.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import logging
import json
import asyncio

from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import query_service
from app.db.mongodb import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])


@router.post("/", response_model=QueryResponse)
async def query_llm(
    request: QueryRequest,
    db = Depends(get_db)
) -> QueryResponse:
    """
    Process a user query with LLM.
    
    This is the main endpoint for query processing. It:
    1. Generates embeddings
    2. Retrieves memory context
    3. Processes through multi-agent system or direct provider
    4. Logs to database
    5. Returns structured response
    
    Args:
        request: QueryRequest with user query and parameters
        
    Returns:
        QueryResponse with LLM response and metadata
    """
    try:
        response = await query_service.process_query(request)
        return response
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def query_llm_stream(
    request: QueryRequest,
    db = Depends(get_db)
):
    """
    Process a user query with streaming response.
    
    Returns Server-Sent Events (SSE) for streaming LLM responses.
    Useful for real-time feedback and long-running queries.
    
    Args:
        request: QueryRequest with user query and parameters
        
    Returns:
        StreamingResponse with SSE events
    """
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for streaming response."""
        try:
            # Import here to avoid circular dependency
            from app.providers.factory import ProviderFactory
            from app.services.memory_service import memory_service
            from app.services.embedding_service import embedding_service
            from datetime import datetime
            
            # Use QueryService to process end-to-end (includes agents, memory, embeddings)
            result = await query_service.process_query(request)
            
            response_text = result.response
            citations = result.citations
            product_cards = result.product_cards
            options = result.options
            
            # Simulate streaming by sending response in chunks
            # This provides a better UX even without true streaming in providers
            chunk_size = 50  # characters per chunk
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i + chunk_size]
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                # Small delay to simulate streaming (optional)
                await asyncio.sleep(0.01)
            
            # Send citations if any
            if citations:
                yield f"data: {json.dumps({'type': 'node', 'node_type': 'citations', 'citations': citations})}\n\n"
            
            # Send product cards if any
            if product_cards:
                yield f"data: {json.dumps({'type': 'node', 'node_type': 'product_cards', 'product_cards': product_cards})}\n\n"
            
            # Send final data with metadata
            final_data = {
                'type': 'final',
                'options': options,
                'metadata': {
                    'model': request.model_name
                }
            }
            yield f"data: {json.dumps(final_data)}\n\n"
            
            # 4. Send completion event
            yield f"data: {json.dumps({'type': 'done', 'message': 'Query complete'})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            error_data = {
                'type': 'error',
                'error': str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.get("/history/{user_id}")
async def get_query_history(
    user_id: str,
    session_id: str = None,
    limit: int = 50,
    db = Depends(get_db)
):
    """
    Get query history for a user.
    
    Args:
        user_id: User ID to filter by
        session_id: Optional session ID filter
        limit: Maximum number of queries to return (default: 50)
        
    Returns:
        List of query documents
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    queries_collection = db["queries"]
    
    # Build query
    query = {"user_id": user_id}
    if session_id:
        query["session_id"] = session_id
    
    try:
        # Fetch queries
        cursor = queries_collection.find(query).sort("timestamp", -1).limit(limit)
        queries = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for q in queries:
            q["_id"] = str(q["_id"])
            # Remove large embedding arrays for performance
            if "embedding" in q:
                q["embedding_size"] = len(q["embedding"])
                del q["embedding"]
        
        return {
            "user_id": user_id,
            "total": len(queries),
            "queries": queries
        }
        
    except Exception as e:
        logger.error(f"Failed to get query history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
