

@app.post("/query/stream")
async def query_llm_stream(request: QueryRequest):
    """
    Streaming version of /query endpoint using Server-Sent Events (SSE).
    
    Streams graph execution updates in real-time:
    - Node transitions ("intent_detected", "shopping_started", etc.)
    - Final response
    
    Client should use EventSource or fetch with stream reading.
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    if coordinator_agent is None:
        raise HTTPException(status_code=503, detail="Multi-agent system not initialized")
    
    logger.info(f"🌊 Streaming query: {request.query} from user {request.user_id}")
    
    async def event_generator():
        try:
            # Prepare initial state (same as non-streaming)
            history_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in request.history
            ] if request.history else []
            
            location_data = request.location.model_dump(exclude_none=True) if request.location else None
            if location_data is None and sessions_collection is not None:
                session_env = await sessions_collection.find_one(
                    {"session_id": request.session_id},
                    {"environment.location": 1}
                )
                if session_env:
                    location_data = session_env.get("environment", {}).get("location")
            
            attachments = request.attachments or []
            history_for_agents = history_messages[-6:]
            
            initial_state = {
                "query": request.query,
                "user_id": request.user_id,
                "session_id": request.session_id,
                "history": history_for_agents,
                "mode": request.mode,
                "attachments": attachments,
                "location": location_data,
                "model": request.model_name,
                "agents_used": []
            }
            
            # Stream graph execution
            async for event in graph_app.astream(initial_state):
                # event is a dict with node name as key
                for node_name, node_output in event.items():
                    # Send update for each node
                    yield f"data: {json.dumps({'type': 'node', 'node': node_name, 'data': {'status': 'completed'}})}\n\n"
            
            # After graph completes, get final state
            final_state = await graph_app.ainvoke(initial_state)
            
            # Send final response
            response_data = {
                "type": "final",
                "response": final_state.get("response") or "",
                "citations": final_state.get("citations") or [],
                "product_cards": final_state.get("product_cards"),
                "options": final_state.get("shopping_result", {}).get("options"),
                "intent": final_state.get("intent"),
                "agents_used": final_state.get("agents_used", [])
            }
            
            yield f"data: {json.dumps(response_data)}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_data = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

