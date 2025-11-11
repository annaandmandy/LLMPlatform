"""
FastAPI + OpenAI + Anthropic + MongoDB Backend for Multi-User LLM Interaction Logging

This backend handles:
- User queries to multiple LLM providers (OpenAI, Anthropic, or OpenRouter)
- Event logging (clicks, browsing, conversions)
- Data export for analysis
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import os
import json
import logging
from dotenv import load_dotenv
from pymongo import MongoClient
import requests
from openai import OpenAI
import anthropic
from google import genai
from google.genai import types

# ==== ENV + LOGGING ====
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==== FASTAPI APP ====
app = FastAPI(title="LLM Interaction Logger", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to initialize multi-agent system
@app.on_event("startup")
async def startup_event():
    """Initialize multi-agent system on startup"""
    initialize_agents()

# ==== MONGODB CONFIG ====
MONGODB_URI = os.getenv("MONGODB_URI")
MONGO_DB = os.getenv("MONGO_DB", "llm_experiment")

try:
    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client[MONGO_DB]
    queries_collection = db["queries"]
    events_collection = db["events"]
    sessions_collection = db["sessions"]  # NEW: Session-based tracking

    # NEW: Multi-agent collections
    summaries_collection = db["summaries"]
    vectors_collection = db["vectors"]
    products_collection = db["products"]
    agent_logs_collection = db["agent_logs"]

    logger.info("✅ Connected to MongoDB")
except Exception as e:
    logger.error(f"❌ MongoDB connection failed: {e}")
    db = None


# ==== API KEYS ====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY")

# ==== REQUEST SCHEMAS ====
class MessageHistory(BaseModel):
    """Message in conversation history"""
    role: str  # "user" or "assistant"
    content: str

class QueryRequest(BaseModel):
    user_id: str
    session_id: str
    query: str
    model_provider: str  # "openai", "anthropic", or "openrouter"
    model_name: Optional[str] = None
    web_search: Optional[bool] = False
    history: Optional[List[MessageHistory]] = []  # NEW: Conversation history for multi-agent context


class LogEventRequest(BaseModel):
    user_id: str
    session_id: str
    event_type: str
    query: Optional[str] = None
    target_url: Optional[str] = None
    page_url: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


# ==== NEW SESSION-BASED SCHEMAS ====
class Environment(BaseModel):
    device: str
    browser: str
    os: str
    viewport: Dict[str, int]  # {"width": 1920, "height": 1080}
    language: Optional[str] = "en"
    connection: Optional[str] = None


class EventData(BaseModel):
    """Event-specific data fields"""
    # Generic fields
    text: Optional[str] = None
    target: Optional[str] = None
    target_url: Optional[str] = None  # URL for link clicks
    x: Optional[float] = None
    y: Optional[float] = None

    # Scroll-specific
    scrollY: Optional[float] = None
    speed: Optional[float] = None
    direction: Optional[str] = None  # "up" or "down"

    # Model response fields
    model: Optional[str] = None
    provider: Optional[str] = None
    latency_ms: Optional[float] = None
    tokens: Optional[Dict[str, int]] = None  # {"prompt": 10, "completion": 50, "total": 60}
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    response_length: Optional[int] = None
    response_id: Optional[str] = None
    citations: Optional[List[Dict[str, Any]]] = None

    # Feedback/error fields
    feedback: Optional[str] = None  # "up", "down", "neutral"
    error_code: Optional[str] = None
    retry_model: Optional[str] = None

    # Activity tracking
    activity_state: Optional[str] = None  # "active" or "idle"
    duration_ms: Optional[int] = None
    visible_time_ms: Optional[float] = None
    selected_text: Optional[str] = None

    # Navigation/topic tracking
    topic: Optional[str] = None
    sentiment: Optional[str] = None
    page_url: Optional[str] = None


class Event(BaseModel):
    """Individual event within a session"""
    t: int  # timestamp in milliseconds since epoch
    type: str  # "prompt", "model_response", "scroll", "click", "hover", "key", "navigate", "copy", "selection", "activity", "feedback", "error", "system"
    data: EventData

    class Config:
        # Exclude null/None values when converting to dict
        use_enum_values = True

    def dict(self, **kwargs):
        # Override dict method to exclude None values
        kwargs['exclude_none'] = True
        d = super().dict(**kwargs)
        # Also clean the nested data dict
        if 'data' in d and d['data']:
            d['data'] = {k: v for k, v in d['data'].items() if v is not None}
        return d


class SessionStartRequest(BaseModel):
    """Request to start a new session"""
    session_id: str
    user_id: str
    experiment_id: Optional[str] = "default"
    environment: Environment


class SessionEventRequest(BaseModel):
    """Request to add an event to a session"""
    session_id: str
    event: Event


class SessionEndRequest(BaseModel):
    """Request to end a session"""
    session_id: str


# ==== MULTI-AGENT SYSTEM INITIALIZATION ====
from agents import CoordinatorAgent, MemoryAgent, ProductAgent, WriterAgent
from utils.embeddings import preload_model

# Initialize agents
coordinator_agent = None
memory_agent = None
product_agent = None
writer_agent = None

def initialize_agents():
    """Initialize the multi-agent system"""
    global coordinator_agent, memory_agent, product_agent, writer_agent

    if db is None:
        logger.warning("⚠️ Database not connected, multi-agent system disabled")
        return

    try:
        logger.info("🤖 Initializing multi-agent system...")

        # Initialize individual agents
        memory_agent = MemoryAgent(db=db)
        product_agent = ProductAgent(db=db)
        writer_agent = WriterAgent(db=db)
        coordinator_agent = CoordinatorAgent(db=db)

        # Configure WriterAgent with LLM functions
        llm_functions = {
            "openai": call_openai,
            "anthropic": call_anthropic,
            "google": call_gemini,
            "openrouter": call_openrouter
        }
        writer_agent.set_llm_functions(llm_functions)

        # Link agents to coordinator
        coordinator_agent.set_agents(memory_agent, product_agent, writer_agent)

        # Preload embedding model for faster first query
        preload_model()

        logger.info("✅ Multi-agent system initialized successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize multi-agent system: {e}")


# ==== HELPER FUNCTIONS ====
def call_openai(model: str, query: str):
    from openai import OpenAI
    import os
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    messages = [
        {"role": "system", "content": (
            "You are ChatGPT: a concise, markdown-savvy assistant. "
            "Use short paragraphs and lists when helpful. Provide citations if possible."
        )},
        {"role": "user", "content": query}
    ]

    # Detect built-in search models
    use_chat_api = any(tag in model for tag in ["search-preview", "search-api"])

    if use_chat_api:
        # --- Chat Completions API for web-search-enabled models ---
        response = client.chat.completions.create(model=model, messages=messages)
        msg = response.choices[0].message
        text = msg.content or ""
        sources = []

        # annotations live at message level
        if hasattr(msg, "annotations"):
            for ann in msg.annotations:
                ann_type = getattr(ann, "type", None)
                if ann_type == "url_citation":
                    uc = getattr(ann, "url_citation", {})
                    sources.append({
                        "title": getattr(uc, "title", "") or uc.get("title", ""),
                        "url": getattr(uc, "url", "") or uc.get("url", "")
                    })

    else:
        # --- Responses API for standard models ---
        response = client.responses.create(
            model=model,
            input=messages,
            tools=[{"type": "web_search"}]
        )
        text, sources = "", []
        for item in getattr(response, "output", []):
            for content in getattr(item, "content", []) or []:
                if getattr(content, "type", None) == "output_text":
                    text += getattr(content, "text", "")
                for ann in getattr(content, "annotations", []) or []:
                    if getattr(ann, "type", None) == "url_citation":
                        sources.append({
                            "title": getattr(ann, "title", ""),
                            "url": getattr(ann, "url", "")
                        })

    # Extract token usage
    tokens = None
    if hasattr(response, "usage"):
        usage = response.usage
        tokens = {
            "prompt": getattr(usage, "prompt_tokens", 0),
            "completion": getattr(usage, "completion_tokens", 0),
            "total": getattr(usage, "total_tokens", 0)
        }

    return text.strip(), sources, getattr(response, "model_dump", lambda: response)(), tokens


def call_anthropic(model: str, query: str):
    """
    Call Claude 3.5 with the new web_search_20250305 tool.
    Handles Anthropic SDK's typed content blocks safely.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 5
        }],
        messages=[{"role": "user", "content": query}]
    )

    text_parts = []
    citations = []

    # Safely iterate content blocks (these are typed SDK objects)
    for block in getattr(response, "content", []):
        # Unified way to get type
        block_type = getattr(block, "type", None) or (block.get("type") if isinstance(block, dict) else None)

        # ---- TEXT BLOCKS ----
        if block_type == "text":
            text_value = getattr(block, "text", "") or (block.get("text") if isinstance(block, dict) else "")
            text_parts.append(text_value)

            # ✅ Inline citations inside text blocks
            block_citations = getattr(block, "citations", []) or (block.get("citations") if isinstance(block, dict) else [])
            for cite in block_citations or []:
                citations.append({
                    "title": getattr(cite, "title", "") or (cite.get("title") if isinstance(cite, dict) else ""),
                    "url": getattr(cite, "url", "") or (cite.get("url") if isinstance(cite, dict) else ""),
                    "snippet": getattr(cite, "cited_text", "") or (cite.get("cited_text") if isinstance(cite, dict) else "")
                })

        # ---- WEB SEARCH RESULTS ----
        elif block_type == "web_search_tool_result":
            block_content = getattr(block, "content", []) or (block.get("content") if isinstance(block, dict) else [])
            for result in block_content or []:
                result_type = getattr(result, "type", None) or (result.get("type") if isinstance(result, dict) else None)
                if result_type == "web_search_result":
                    citations.append({
                        "title": getattr(result, "title", "") or (result.get("title") if isinstance(result, dict) else ""),
                        "url": getattr(result, "url", "") or (result.get("url") if isinstance(result, dict) else ""),
                        "snippet": getattr(result, "page_age", "") or (result.get("page_age") if isinstance(result, dict) else "")
                    })

        # (optional) ignore ServerToolUseBlock, etc.
        else:
            continue

    # remove duplicates by URL
    seen, unique = set(), []
    for c in citations:
        url = c.get("url")
        if url and url not in seen:
            seen.add(url)
            unique.append(c)

    # Extract token usage
    tokens = None
    if hasattr(response, "usage"):
        usage = response.usage
        tokens = {
            "prompt": getattr(usage, "input_tokens", 0),
            "completion": getattr(usage, "output_tokens", 0),
            "total": getattr(usage, "input_tokens", 0) + getattr(usage, "output_tokens", 0)
        }

    text = "\n".join(text_parts).strip()
    return text, unique, response.model_dump(), tokens

def call_gemini(model: str, query: str):
    """
    Call Google Gemini (2.x / 1.5) API with web grounding enabled.
    Handles typed SDK objects and converts response safely to dict.
    """
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    # Enable Google Search grounding
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(tools=[grounding_tool])

    # Generate content
    response = client.models.generate_content(
        model=model,
        contents=query,
        config=config,
    )

    # --- Extract text ---
    text = ""
    if hasattr(response, "candidates") and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, "content") and candidate.content.parts:
            for part in candidate.content.parts:
                if hasattr(part, "text"):
                    text += part.text + "\n"

    # --- Extract citations ---
    citations = []
    candidate = response.candidates[0]
    metadata = getattr(candidate, "grounding_metadata", None)

    if metadata and getattr(metadata, "grounding_chunks", None):
        for chunk in metadata.grounding_chunks:
            web_obj = getattr(chunk, "web", None)
            if web_obj:
                citations.append({
                    "title": getattr(web_obj, "title", ""),
                    "url": getattr(web_obj, "uri", "")
                })
            elif isinstance(chunk, dict) and "web" in chunk:
                web = chunk["web"]
                citations.append({
                    "title": web.get("title", ""),
                    "url": web.get("uri", "")
                })

    # remove duplicates
    seen, unique = set(), []
    for c in citations:
        if c["url"] and c["url"] not in seen:
            seen.add(c["url"])
            unique.append(c)

    # Extract token usage
    tokens = None
    if hasattr(response, "usage_metadata"):
        usage = response.usage_metadata
        tokens = {
            "prompt": getattr(usage, "prompt_token_count", 0),
            "completion": getattr(usage, "candidates_token_count", 0),
            "total": getattr(usage, "total_token_count", 0)
        }

    # ✅ Convert response to dict safely
    try:
        raw = response.as_dict()  # works in google-genai >= 0.2.0
    except AttributeError:
        # fallback: build manually if as_dict is missing
        raw = {
            "candidates": [
                {
                    "content": [
                        getattr(p, "text", "")
                        for p in getattr(response.candidates[0].content, "parts", [])
                        if hasattr(p, "text")
                    ],
                    "grounding_metadata": str(getattr(response.candidates[0], "grounding_metadata", "")),
                }
            ]
        }

    return text.strip(), unique, raw, tokens


def call_openrouter(model: str, query: str):
    """Call OpenRouter API directly (handles Grok and Perplexity citations)."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:3000",   # optional but recommended
        "X-Title": "LLM Brand Experiment",
        "Content-Type": "application/json"
    }

    # Strip "openrouter/" prefix if sent by frontend
    if model.startswith("openrouter/"):
        model = model.split("openrouter/")[-1]

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that provides informative and referenced answers."
            },
            {"role": "user", "content": query}
        ]
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload),
        timeout=600
    )

    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("❌ OpenRouter request failed:", e)
        print("Response text:", response.text)
        raise

    data = response.json()
    text = data["choices"][0]["message"]["content"]

    # --- ✅ Extract citations safely ---
    citations = []

    # Case 1: Perplexity models return `references` directly
    if "references" in data:
        for ref in data["references"]:
            citations.append({
                "title": ref.get("title", ""),
                "url": ref.get("url", ""),
                "content": ref.get("content", "")
            })

    # --- Case 2: xAI / Grok or GPT-4o-mini:online style ---
    message = data["choices"][0]["message"]

    # A. annotations field (common for Grok and GPT-4o-mini:online)
    if "annotations" in message:
        for ann in message["annotations"]:
            if ann.get("type") == "url_citation":
                citations.append({
                    "title": ann.get("title") or ann.get("url_citation", {}).get("title", ""),
                    "url": ann.get("url") or ann.get("url_citation", {}).get("url", ""),
                    "content": ann.get("content") or ann.get("url_citation", {}).get("content", "")
                })

    # B. metadata.citations (used by OpenAI-style models on OpenRouter)
    elif "metadata" in message and "citations" in message["metadata"]:
        for c in message["metadata"]["citations"]:
            citations.append({
                "title": c.get("title", ""),
                "url": c.get("url", ""),
                "content": c.get("snippet", "")
            })

    # Extract token usage
    tokens = None
    if "usage" in data:
        usage = data["usage"]
        tokens = {
            "prompt": usage.get("prompt_tokens", 0),
            "completion": usage.get("completion_tokens", 0),
            "total": usage.get("total_tokens", 0)
        }

    return text.strip(), citations, data, tokens

# ==== API ENDPOINTS ====
@app.get("/")
async def root():
    return {"message": "LLM Interaction Logger API (Multi-Provider)", "version": "2.0.0"}


@app.get("/status")
async def status():
    return {
        "status": "running",
        "mongodb_connected": db is not None,
        "providers_available": {
            "openai": bool(OPENAI_API_KEY),
            "anthropic": bool(ANTHROPIC_API_KEY),
            "openrouter": bool(OPENROUTER_API_KEY),
        },
    }


@app.post("/query")
async def query_llm(request: QueryRequest):
    """
    Query LLM using multi-agent architecture.

    This endpoint now routes through the multi-agent system which:
    1. Detects intent (product search, memory retrieval, general)
    2. Routes to appropriate agents (Memory, Product, Writer)
    3. Synthesizes final response with enriched context

    Falls back to direct LLM call if multi-agent system is unavailable.
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    logger.info(f"🔍 Processing query: {request.query} from user {request.user_id}")

    start_time = datetime.utcnow()
    start_time_ms = int(start_time.timestamp() * 1000)

    try:
        model = request.model_name
        product_cards = None
        intent_info = None

        # Try using multi-agent system first
        if coordinator_agent is not None:
            logger.info("🤖 Using multi-agent system")

            # Prepare request for coordinator
            agent_request = {
                "query": request.query,
                "session_id": request.session_id,
                "user_id": request.user_id,
                "model": model,
                "history": [{"role": msg.role, "content": msg.content} for msg in request.history] if request.history else []
            }

            # Run through multi-agent system
            result = await coordinator_agent.run(agent_request)
            agent_output = result["output"]

            response_text = agent_output["response"]
            citations = agent_output.get("citations", [])
            tokens = agent_output.get("tokens")
            intent_info = {
                "intent": agent_output.get("intent"),
                "confidence": agent_output.get("intent_confidence"),
                "agents_used": agent_output.get("agents_used", [])
            }

            # Extract product cards if present
            product_cards = agent_output.get("product_cards")

            # Store embeddings for RAG (async, don't wait)
            if memory_agent:
                # Store user query embedding
                try:
                    await memory_agent.store_message_embedding(
                        session_id=request.session_id,
                        role="user",
                        content=request.query,
                        message_index=len(request.history) if request.history else 0
                    )
                    # Store assistant response embedding
                    await memory_agent.store_message_embedding(
                        session_id=request.session_id,
                        role="assistant",
                        content=response_text,
                        message_index=len(request.history) + 1 if request.history else 1
                    )
                except Exception as e:
                    logger.warning(f"Failed to store embeddings: {e}")

            raw = {}  # Multi-agent raw response placeholder

        else:
            # Fallback to direct LLM call
            logger.info("⚠️ Multi-agent system unavailable, using direct LLM call")

            if request.model_provider == "openai":
                response_text, citations, raw, tokens = call_openai(model, request.query)
            elif request.model_provider == "anthropic":
                response_text, citations, raw, tokens = call_anthropic(model, request.query)
            elif request.model_provider == "openrouter":
                response_text, citations, raw, tokens = call_openrouter(model, request.query)
            elif request.model_provider == "google":
                response_text, citations, raw, tokens = call_gemini(model, request.query)
            else:
                raise HTTPException(status_code=400, detail="Invalid model provider")

        end_time = datetime.utcnow()
        end_time_ms = int(end_time.timestamp() * 1000)
        latency_ms = (end_time - start_time).total_seconds() * 1000

        # Log to MongoDB (keeping for backward compatibility)
        query_log = {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "query": request.query,
            "response": response_text,
            "model_provider": request.model_provider,
            "model_used": model,
            "timestamp": start_time,
            "citations": citations,
            "raw": raw if raw else {},
            "tokens": tokens,
            "latency_ms": latency_ms,
        }

        # Add multi-agent specific fields if available
        if intent_info:
            query_log["intent"] = intent_info.get("intent")
            query_log["intent_confidence"] = intent_info.get("confidence")
            query_log["agents_used"] = intent_info.get("agents_used")

        if product_cards:
            query_log["product_cards"] = product_cards

        queries_collection.insert_one(query_log)

        # NEW: Also log to sessions collection
        # Log the prompt event
        prompt_event = {
            "t": start_time_ms,
            "type": "prompt",
            "data": {"text": request.query}
        }

        # Log the model response event
        response_event_data = {
            "text": response_text,
            "model": model,
            "provider": request.model_provider,
            "latency_ms": latency_ms,
            "response_length": len(response_text),
            "citations": citations
        }

        # Add token usage if available
        if tokens:
            response_event_data["tokens"] = tokens


        response_event = {
            "t": end_time_ms,
            "type": "model_response",
            "data": response_event_data
        }

        # Add both events to session (if session exists)
        result = sessions_collection.update_one(
            {"session_id": request.session_id},
            {"$push": {"events": {"$each": [prompt_event, response_event]}}}
        )

        if result.matched_count > 0:
            logger.info(f"✅ Query logged to session {request.session_id}")
        else:
            logger.warning(f"⚠️ Session {request.session_id} not found, only logged to legacy collections")

        # Return response with optional product_cards
        response_data = {
            "response": response_text,
            "citations": citations
        }

        if product_cards:
            response_data["product_cards"] = product_cards

        if intent_info:
            response_data["intent"] = intent_info.get("intent")
            response_data["agents_used"] = intent_info.get("agents_used")

        return response_data

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")

        # Log error event to session
        error_event = {
            "t": int(datetime.utcnow().timestamp() * 1000),
            "type": "error",
            "data": {
                "error_code": str(e),
                "text": f"API request failed: {str(e)}"
            }
        }
        sessions_collection.update_one(
            {"session_id": request.session_id},
            {"$push": {"events": error_event}}
        )

        raise HTTPException(status_code=500, detail=f"API request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing query: {e}")

        # Log error event to session
        error_event = {
            "t": int(datetime.utcnow().timestamp() * 1000),
            "type": "error",
            "data": {
                "error_code": str(e),
                "text": f"Error: {str(e)}"
            }
        }
        sessions_collection.update_one(
            {"session_id": request.session_id},
            {"$push": {"events": error_event}}
        )

        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/log_event")
async def log_event(request: LogEventRequest):
    """Record user interaction events (clicks, browsing, conversions) - LEGACY"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    event_log = {
        "user_id": request.user_id,
        "session_id": request.session_id,
        "event_type": request.event_type,
        "query": request.query,
        "target_url": request.target_url,
        "page_url": request.page_url,
        "extra_data": request.extra_data or {},
        "timestamp": datetime.utcnow()
    }
    events_collection.insert_one(event_log)
    logger.info(f"📦 Event logged: {request.event_type} for user {request.user_id}")

    return {"status": "success", "message": "Event logged successfully"}


# ==== PRODUCT SEARCH ENDPOINT ====
@app.get("/search/products")
async def search_products(query: str, max_results: int = 10):
    """
    Search products in the products collection.

    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 10)

    Returns:
        List of product cards
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    if product_agent is None:
        raise HTTPException(status_code=503, detail="Product agent not initialized")

    try:
        logger.info(f"🛍️ Searching products: {query}")

        # Use ProductAgent to search
        result = await product_agent.run({
            "query": query,
            "max_results": max_results
        })

        products = result["output"].get("products", [])

        logger.info(f"Found {len(products)} products")

        return {
            "products": products,
            "total": len(products),
            "query": query
        }

    except Exception as e:
        logger.error(f"Error searching products: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching products: {str(e)}")


# ==== SESSION-BASED ENDPOINTS ====
@app.post("/session/start")
async def start_session(request: SessionStartRequest):
    """Initialize a new session with metadata and environment details (or return existing)"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    # Check if session already exists
    existing_session = sessions_collection.find_one({"session_id": request.session_id})

    if existing_session:
        # Session already exists, don't create duplicate
        logger.info(f"♻️ Session already exists: {request.session_id}")
        return {"status": "success", "session_id": request.session_id, "existing": True}

    # Session doesn't exist, create new one
    session_doc = {
        "session_id": request.session_id,
        "user_id": request.user_id,
        "experiment_id": request.experiment_id,
        "start_time": datetime.utcnow(),
        "end_time": None,
        "environment": request.environment.dict(),
        "events": []
    }

    sessions_collection.insert_one(session_doc)
    logger.info(f"🎬 Session started: {request.session_id} for user {request.user_id}")

    return {"status": "success", "session_id": request.session_id, "existing": False}


@app.post("/session/event")
async def log_session_event(request: SessionEventRequest):
    """Add an event to an existing session"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    result = sessions_collection.update_one(
        {"session_id": request.session_id},
        {"$push": {"events": request.event.dict()}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")

    logger.info(f"📝 Event added to session {request.session_id}: {request.event.type}")

    return {"status": "success"}


@app.post("/session/end")
async def end_session(request: SessionEndRequest):
    """Mark a session as ended"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    result = sessions_collection.update_one(
        {"session_id": request.session_id},
        {"$set": {"end_time": datetime.utcnow()}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")

    logger.info(f"🏁 Session ended: {request.session_id}")

    return {"status": "success"}


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Retrieve a complete session with all events"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    session = sessions_collection.find_one({"session_id": session_id}, {"_id": 0})

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Convert datetime objects to ISO format
    if "start_time" in session and session["start_time"]:
        session["start_time"] = session["start_time"].isoformat()
    if "end_time" in session and session["end_time"]:
        session["end_time"] = session["end_time"].isoformat()

    return session


@app.get("/export_data")
async def export_data():
    """Export all logged data"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    queries = list(queries_collection.find({}, {"_id": 0}))
    for q in queries:
        q["type"] = "query"
        if "timestamp" in q:
            q["timestamp"] = q["timestamp"].isoformat()

    events = list(events_collection.find({}, {"_id": 0}))
    for e in events:
        e["type"] = "event"
        if "timestamp" in e:
            e["timestamp"] = e["timestamp"].isoformat()

    all_data = queries + events
    all_data.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return {
        "total_records": len(all_data),
        "queries_count": len(queries),
        "events_count": len(events),
        "data": all_data,
    }


@app.get("/tokens/data")
async def get_tokens_data(model_provider: Optional[str] = None, model_used: Optional[str] = None):
    """Get token usage data with optional filters"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    # Build filter query
    filter_query = {"tokens": {"$exists": True, "$ne": None}}

    if model_provider:
        filter_query["model_provider"] = model_provider

    if model_used:
        filter_query["model_used"] = model_used

    # Get queries with token data
    queries = list(queries_collection.find(filter_query, {
        "_id": 0,
        "model_provider": 1,
        "model_used": 1,
        "tokens": 1,
        "timestamp": 1,
        "latency_ms": 1
    }))

    # Convert timestamps to ISO format
    for q in queries:
        if "timestamp" in q and q["timestamp"]:
            q["timestamp"] = q["timestamp"].isoformat()

    # Get unique providers and models for filter options
    all_providers = list(queries_collection.distinct("model_provider", {"tokens": {"$exists": True}}))
    all_models = list(queries_collection.distinct("model_used", {"tokens": {"$exists": True}}))

    # Calculate aggregated statistics
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0
    model_usage_count = {}
    provider_stats = {}
    model_stats = {}
    model_latency_stats = {}

    for q in queries:
        tokens = q.get("tokens", {})
        prompt = tokens.get("prompt", 0)
        completion = tokens.get("completion", 0)
        total = tokens.get("total", 0)

        total_prompt_tokens += prompt
        total_completion_tokens += completion
        total_tokens += total

        # Count model usage
        model = q.get("model_used", "unknown")
        model_usage_count[model] = model_usage_count.get(model, 0) + 1

        # Provider stats
        provider = q.get("model_provider", "unknown")
        if provider not in provider_stats:
            provider_stats[provider] = {"prompt": 0, "completion": 0, "total": 0}
        provider_stats[provider]["prompt"] += prompt
        provider_stats[provider]["completion"] += completion
        provider_stats[provider]["total"] += total

        # Model stats
        if model not in model_stats:
            model_stats[model] = {"prompt": 0, "completion": 0, "total": 0}
        model_stats[model]["prompt"] += prompt
        model_stats[model]["completion"] += completion
        model_stats[model]["total"] += total

        # Latency stats (if available)
        latency = q.get("latency_ms")
        if latency is not None:
            if model not in model_latency_stats:
                model_latency_stats[model] = {"total_latency": 0, "count": 0}
            model_latency_stats[model]["total_latency"] += latency
            model_latency_stats[model]["count"] += 1

    # Calculate average latency per model
    model_avg_latency = {}
    for model, stats in model_latency_stats.items():
        if stats["count"] > 0:
            model_avg_latency[model] = stats["total_latency"] / stats["count"]

    return {
        "queries": queries,
        "filters": {
            "providers": all_providers,
            "models": all_models
        },
        "aggregated": {
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens,
            "model_usage_count": model_usage_count,
            "provider_stats": provider_stats,
            "model_stats": model_stats,
            "model_avg_latency": model_avg_latency
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
