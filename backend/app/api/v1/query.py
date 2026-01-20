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
    Uses LangGraph events to show 'Chain of Thought' reasoning.
    """
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for streaming response."""
        try:
            # Use the new streaming method in QueryService
            async for event in query_service.stream_query(request):
                # Format as SSE
                yield f"data: {json.dumps(event)}\n\n"
            
        except Exception as e:
            import traceback
            logger.error(f"Streaming failed: {e}\n{traceback.format_exc()}")
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
            "X-Accel-Buffering": "no",
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
