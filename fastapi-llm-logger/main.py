"""
FastAPI + OpenAI + Anthropic + MongoDB Backend for Multi-User LLM Interaction Logging

This backend handles:
- User queries to multiple LLM providers (OpenAI, Anthropic, or OpenRouter)
- Event logging (clicks, browsing, conversions)
- Data export for analysis
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
import os
import json
import logging
import warnings
from pathlib import Path
from dotenv import load_dotenv
from pymongo import ReturnDocument
from bson import ObjectId
import requests
from openai import OpenAI
from database import connect_to_mongo
import anthropic
from google import genai
from google.genai import types

# ==== ENV + LOGGING ====
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress noisy pydantic warnings from third-party Operation models
warnings.filterwarnings(
    "ignore",
    message=r'Field name "(name|metadata|done|error)" shadows an attribute in parent "Operation"',
    category=UserWarning,
)

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
    global db, queries_collection, events_collection, sessions_collection
    global summaries_collection, vectors_collection, products_collection
    global agent_logs_collection, memories_collection, files_collection

    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning(f"Unable to create upload directory {UPLOAD_DIR}: {e}")
    
    # Connect to MongoDB (Async)
    db = await connect_to_mongo()
    if db is not None:
        queries_collection = db["queries"]
        events_collection = db["events"]
        sessions_collection = db["sessions"]
        summaries_collection = db["summaries"]
        vectors_collection = db["vectors"]
        products_collection = db["products"]
        agent_logs_collection = db["agent_logs"]
        memories_collection = db["memories"]
        files_collection = db["files"]
        logger.info("✅ Connected to MongoDB (Async)")
        
        # Initialize agents with async db
        initialize_agents()
    else:
        logger.error("❌ Failed to connect to MongoDB")

# ==== MONGODB CONFIG ====
MONGODB_URI = os.getenv("MONGODB_URI")
MONGO_DB = os.getenv("MONGO_DB", "llm_experiment")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
MAX_FILE_SIZE_MB = float(os.getenv("MAX_FILE_SIZE_MB", "10"))
ALLOWED_MIME_PREFIXES = ["image/", "text/", "application/pdf"]
ALLOWED_MIME_TYPES = set(
    (os.getenv("ALLOWED_MIME_TYPES") or "").split(",")
    if os.getenv("ALLOWED_MIME_TYPES")
    else []
)

# ==== MONGODB CONFIG ====
# Collections will be initialized in startup_event
mongo_client = None
db = None
queries_collection = None
events_collection = None
sessions_collection = None
summaries_collection = None
vectors_collection = None
products_collection = None
agent_logs_collection = None
memories_collection = None
files_collection = None

# ==== API KEYS ====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY")

# ==== REQUEST SCHEMAS ====
class AppBaseModel(BaseModel):
    model_config = ConfigDict(protected_namespaces=())


class MessageHistory(AppBaseModel):
    """Message in conversation history"""
    role: str  # "user" or "assistant"
    content: str

class LocationInfo(AppBaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None

class QueryRequest(AppBaseModel):
    user_id: str
    session_id: str
    query: str
    model_provider: str  # "openai", "anthropic", or "openrouter"
    model_name: Optional[str] = None
    web_search: Optional[bool] = False
    use_memory: Optional[bool] = False
    use_product_search: Optional[bool] = False
    history: Optional[List[MessageHistory]] = []  # NEW: Conversation history for multi-agent context
    location: Optional[LocationInfo] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    mode: Optional[str] = "chat"  # "chat" or "shopping"


class LogEventRequest(AppBaseModel):
    user_id: str
    session_id: str
    event_type: str
    query: Optional[str] = None
    target_url: Optional[str] = None
    page_url: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


# ==== NEW SESSION-BASED SCHEMAS ====
class Environment(AppBaseModel):
    device: str
    browser: str
    os: str
    viewport: Dict[str, int]  # {"width": 1920, "height": 1080}
    language: Optional[str] = "en"
    connection: Optional[str] = None
    location: Optional[LocationInfo] = None


class EventData(AppBaseModel):
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


class Event(AppBaseModel):
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


class SessionStartRequest(AppBaseModel):
    """Request to start a new session"""
    session_id: str
    user_id: str
    experiment_id: Optional[str] = "default"
    environment: Environment


class SessionEventRequest(AppBaseModel):
    """Request to add an event to a session"""
    session_id: str
    event: Event


class SessionEndRequest(AppBaseModel):
    """Request to end a session"""
    session_id: str


# ==== MEMORIES CRUD (simple, user-scoped) ====
class MemoryPayload(AppBaseModel):
    user_id: str
    key: str
    value: str


class ExperimentPayload(AppBaseModel):
    experiment_id: str

def _validate_file(upload: UploadFile):
    if not upload.content_type:
        raise HTTPException(status_code=400, detail="Missing content type")
    mime = upload.content_type.lower()
    if ALLOWED_MIME_TYPES:
        if mime not in ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=400, detail="File type not allowed")
    else:
        if not any(mime.startswith(prefix) for prefix in ALLOWED_MIME_PREFIXES):
            raise HTTPException(status_code=400, detail="File type not allowed")

def _save_upload(upload: UploadFile) -> Dict[str, Any]:
    _validate_file(upload)
    data = upload.file.read()
    if len(data) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE_MB} MB limit")
    safe_name = upload.filename or f"file_{datetime.utcnow().timestamp()}"
    dest = UPLOAD_DIR / safe_name
    counter = 1
    while dest.exists():
        dest = UPLOAD_DIR / f"{counter}_{safe_name}"
        counter += 1
    with open(dest, "wb") as f:
        f.write(data)
    return {"path": str(dest), "size": len(data), "mime": upload.content_type, "name": safe_name}


# ==== MULTI-AGENT SYSTEM INITIALIZATION ====
from agents import CoordinatorAgent, MemoryAgent, ProductAgent, WriterAgent, VisionAgent, ShoppingAgent
from agents.writer_agent import DEFAULT_SYSTEM_PROMPT
from utils.intent_classifier import detect_intent
from agents.graph import graph_app, set_agents

# Initialize agents
coordinator_agent = None
memory_agent = None
product_agent = None
writer_agent = None
shopping_agent = None

def initialize_agents():
    """Initialize the multi-agent system"""
    global coordinator_agent, memory_agent, product_agent, writer_agent, shopping_agent

    if db is None:
        logger.warning("⚠️ Database not connected, multi-agent system disabled")
        return

    try:
        logger.info("🤖 Initializing multi-agent system...")

        # Initialize individual agents
        memory_agent = MemoryAgent(db=db)
        product_agent = ProductAgent(db=db)
        writer_agent = WriterAgent(db=db)
        vision_agent = VisionAgent(db=db)
        shopping_agent = ShoppingAgent(db=db)
        coordinator_agent = CoordinatorAgent(db=db)

        # Configure WriterAgent with LLM functions
        llm_functions = {
            "openai": call_openai,
            "anthropic": call_anthropic,
            "google": call_gemini,
            "openrouter": call_openrouter,
            "openrouter_perplexity": call_openrouter,
            "openrouter_grok": call_openrouter,
        }
        writer_agent.set_llm_functions(llm_functions)

        # Link agents to coordinator (kept for backward compatibility if needed)
        coordinator_agent.set_agents(memory_agent, product_agent, writer_agent, vision_agent, shopping_agent)

        # Inject agents into LangGraph
        set_agents({
            "memory_agent": memory_agent,
            "product_agent": product_agent,
            "writer_agent": writer_agent,
            "vision_agent": vision_agent,
            "shopping_agent": shopping_agent,
            "coordinator_agent": coordinator_agent
        })

        logger.info("✅ Multi-agent system initialized successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize multi-agent system: {e}")


def format_location_text(location: Optional[Dict[str, Any]]) -> Optional[str]:
    """Convert location metadata into a readable string for prompts."""
    if not location:
        return None

    parts = []

    city = location.get("city")
    region = location.get("region")
    country = location.get("country")
    if city:
        parts.append(city)
    if region and region not in parts:
        parts.append(region)
    if country and country not in parts:
        parts.append(country)

    lat = location.get("latitude")
    lon = location.get("longitude")
    if lat is not None and lon is not None:
        parts.append(f"lat {lat:.4f}, lon {lon:.4f}")

    if not parts:
        return None

    accuracy = location.get("accuracy")
    if accuracy:
        parts.append(f"(accuracy ±{accuracy:.0f}m)")

    return ", ".join(parts)


# ==== HELPER FUNCTIONS ====
def call_openai(model: str, query: str, system_prompt: str | None = None, attachments: Optional[List[Dict[str, Any]]] = None):
    from openai import OpenAI
    import os
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    system_message = system_prompt or DEFAULT_SYSTEM_PROMPT

    def _build_messages(include_images: bool):
        user_content: Any
        if include_images and attachments:
            parts = [{"type": "text", "text": query}]
            for att in attachments:
                if att.get("type") == "image" and att.get("base64"):
                    parts.append({"type": "image_url", "image_url": {"url": att["base64"]}})
            user_content = parts
        else:
            user_content = query
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_content},
        ]

    # Detect built-in search models
    use_chat_api = any(tag in model for tag in ["search-preview", "search-api"])

    if use_chat_api:
        # --- Chat Completions API for web-search-enabled models ---
        include_images = bool(attachments)
        messages = _build_messages(include_images)
        try:
            response = client.chat.completions.create(model=model, messages=messages)
        except Exception as err:
            # If the account has zero image quota or hits image rate limits, retry without images
            if include_images and "input-images" in str(err).lower():
                logger.warning("Image quota/rate limit hit for OpenAI; retrying without images")
                messages = _build_messages(False)
                response = client.chat.completions.create(model=model, messages=messages)
            else:
                raise
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
        messages = _build_messages(bool(attachments))
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


def call_anthropic(model: str, query: str, system_prompt: str | None = None):
    """
    Call Claude 3.5 with the new web_search_20250305 tool.
    Handles Anthropic SDK's typed content blocks safely.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    system_message = system_prompt or DEFAULT_SYSTEM_PROMPT

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 5
        }],
        system=system_message,
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

def call_gemini(model: str, query: str, system_prompt: str | None = None):
    """
    Call Google Gemini (2.x / 1.5) API with web grounding enabled.
    Handles typed SDK objects and converts response safely to dict.
    """
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    # Enable Google Search grounding
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(tools=[grounding_tool])

    # Generate content
    system_message = system_prompt or DEFAULT_SYSTEM_PROMPT

    response = client.models.generate_content(
        model=model,
        contents=[
            {"role": "user", "parts": [{"text": f"{system_message}\n\n{query}"}]}
        ],
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


def call_openrouter(model: str, query: str, system_prompt: str | None = None):
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
                "content": system_prompt or DEFAULT_SYSTEM_PROMPT
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
        product_structured = None
        memory_context = None
        intent_info = None

        history_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.history
        ] if request.history else []
        history_count = len(history_messages)

        use_memory = True  # always enable memory
        # Intent detection (LLM/embedding backed, see utils/intent_classifier.py)
        intent_info = await detect_intent(request.query)
        intent_label = intent_info.get("intent", "general")
        use_product_search = intent_label == "product_search"
        location_data = request.location.model_dump(exclude_none=True) if request.location else None
        attachments = request.attachments or []
        if location_data is None and sessions_collection is not None:
            session_env = await sessions_collection.find_one(
                {"session_id": request.session_id},
                {"environment.location": 1}
            )
            if session_env:
                location_data = session_env.get("environment", {}).get("location")
        location_text = format_location_text(location_data)

        processed_query = request.query
        history_for_agents = history_messages[-6:]

        # Try using multi-agent system first
        if location_data and sessions_collection is not None:
            await sessions_collection.update_one(
                {"session_id": request.session_id},
                {"$set": {"environment.location": location_data}}
            )

        # Try to lazily (re)initialize agents if they are missing but DB is up
        if coordinator_agent is None and db is not None:
            logger.warning("Multi-agent system not initialized; attempting to initialize now")
            initialize_agents()

        if coordinator_agent is not None:
            logger.info("🤖 Using LangGraph multi-agent system")

            # Prepare LangGraph state
            initial_state = {
                "query": processed_query,
                "user_id": request.user_id,
                "session_id": request.session_id,
                "history": history_for_agents,
                "mode": request.mode,
                "attachments": attachments,
                "location": location_data,
                "model": model,
                "agents_used": []
            }

            # Run graph
            graph_output = await graph_app.ainvoke(initial_state)

            # Map output to response variables
            response_text = graph_output.get("response") or ""
            citations = graph_output.get("citations") or []
            product_cards = graph_output.get("product_cards")
            product_structured = graph_output.get("structured_products")
            memory_context = graph_output.get("memory_context")
            intent_label = graph_output.get("intent")
            
            # Handle Shopping Mode specialized output
            shopping_status = graph_output.get("shopping_status")
            if shopping_status == "question":
                response_text = graph_output["response"]
                options = graph_output.get("shopping_result", {}).get("options")
                
                # Return intermediate question directly
                return {
                    "response": response_text,
                    "citations": [],
                    "product_cards": [],
                    "tokens": None,
                    "intent": "shopping_interview",
                    "options": options,
                    "model_used": model,
                    "memory_context": memory_context
                }

            tokens = None # Token tracking needs update in graph response if critical
            raw = {} 

            intent_info = {
                "intent": intent_label,
                "confidence": graph_output.get("intent_confidence"),
                "agents_used": graph_output.get("agents_used", [])
            }

            # Store embeddings for RAG (async, don't wait)
            if memory_agent and not attachments:
                # Store user/assistant text embeddings only when no binary attachments interfere
                try:
                    await memory_agent.store_message_embedding(
                        session_id=request.session_id,
                        user_id=request.user_id,
                        role="user",
                        content=request.query,
                        message_index=history_count if history_count else 0
                    )
                    await memory_agent.store_message_embedding(
                        session_id=request.session_id,
                        user_id=request.user_id,
                        role="assistant",
                        content=response_text,
                        message_index=history_count + 1 if history_count else 1
                    )
                except Exception as e:
                    logger.warning(f"Failed to store embeddings: {e}")

            if not raw:
                raw = {}

        else:
            # Fallback to direct LLM call
            logger.info("⚠️ Multi-agent system unavailable, using direct LLM call")

            system_prompt = DEFAULT_SYSTEM_PROMPT
            intent_info = {
                "intent": intent_label,
                "confidence": 1.0,
                "agents_used": []
            }
            memory_context = None
            if memory_agent:
                try:
                    mem_result = await memory_agent.run(
                        {
                            "action": "context_bundle",
                            "query": processed_query,
                            "session_id": request.session_id,
                            "user_id": request.user_id,
                        }
                    )
                    memory_context = mem_result.get("output")
                except Exception as e:
                    logger.warning(f"MemoryAgent retrieval failed (fallback path): {e}")

            llm_input = processed_query
            if history_for_agents:
                history_text = "\n".join(
                    f"{msg['role'].capitalize()}: {msg['content']}"
                    for msg in history_for_agents
                )
                llm_input = (
                    "Recent context:\n"
                    f"{history_text}\n\n"
                    f"Current question: {processed_query}"
                )
            if memory_context:
                memory_parts = []
                summaries = (memory_context.get("summaries") or []) if isinstance(memory_context, dict) else []
                retrieved = (memory_context.get("context") or []) if isinstance(memory_context, dict) else []
                recents = (memory_context.get("recent_messages") or []) if isinstance(memory_context, dict) else []
                memories = (memory_context.get("memories") or []) if isinstance(memory_context, dict) else []

                if summaries:
                    memory_parts.append("Summaries:")
                    for s in summaries[:2]:
                        memory_parts.append(f"- {s.get('summary', '')[:240]}")
                if memories:
                    memory_parts.append("Stored facts:")
                    for mem in memories[:4]:
                        memory_parts.append(f"- {mem.get('key')}: {mem.get('value')}")
                if retrieved:
                    memory_parts.append("Similar messages:")
                    for ctx in retrieved[:4]:
                        memory_parts.append(f"- (sim {ctx.get('similarity',0):.2f}) {ctx.get('content','')[:180]}")
                if recents:
                    memory_parts.append("Recent turns:")
                    for msg in recents[-4:]:
                        memory_parts.append(f"- {msg.get('role','user')}: {msg.get('content','')[:160]}")

                if memory_parts:
                    llm_input = f"{llm_input}\n\nMemory context:\n" + "\n".join(memory_parts)
            if location_text:
                llm_input = f"User location: {location_text}\n\n{llm_input}"

            if request.model_provider == "openai":
                response_text, citations, raw, tokens = call_openai(
                    model,
                    llm_input,
                    system_prompt=system_prompt,
                    attachments=attachments,
                )
            elif request.model_provider == "anthropic":
                response_text, citations, raw, tokens = call_anthropic(model, llm_input, system_prompt=system_prompt)
            elif request.model_provider == "openrouter":
                response_text, citations, raw, tokens = call_openrouter(model, llm_input, system_prompt=system_prompt)
            elif request.model_provider == "google":
                response_text, citations, raw, tokens = call_gemini(model, llm_input, system_prompt=system_prompt)
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
        query_log["use_memory_toggle"] = use_memory
        query_log["use_product_search_toggle"] = use_product_search
        if location_data:
            query_log["user_location"] = location_data

        if use_memory and history_for_agents:
            query_log["need_memory"] = True
            query_log["memory_reason"] = "always_on"
            query_log["history_window_size"] = len(history_for_agents)

        # Add multi-agent specific fields if available
        if intent_info:
            query_log["intent"] = intent_info.get("intent")
            query_log["intent_confidence"] = intent_info.get("confidence")
            query_log["agents_used"] = intent_info.get("agents_used")

        if product_cards:
            query_log["product_cards"] = product_cards

        if product_structured:
            query_log["product_structured"] = product_structured

        queries_collection.insert_one(query_log)

        # NEW: Also log to sessions collection
        # Log the prompt event
        # Log the prompt event
        prompt_event = {
            "t": start_time_ms,
            "type": "prompt",
            "data": {
                "text": request.query,
                "attachments": attachments,
                "mode": request.mode  # Log the interaction mode (e.g., 'shopping' or 'chat')
            }
        }

        # Log the model response event
        response_event_data = {
            "text": response_text,
            "model": model,
            "provider": request.model_provider,
            "latency_ms": latency_ms,
            "response_length": len(response_text),
            "citations": citations,
            "mode": request.mode  # Log mode in response as well
        }

        # Add token usage if available
        if tokens:
            response_event_data["tokens"] = tokens

        if product_structured:
            response_event_data["products"] = product_structured


        response_event = {
            "t": end_time_ms,
            "type": "model_response",
            "data": response_event_data
        }

        # Add both events to session (if session exists)
        session_doc = await sessions_collection.find_one_and_update(
            {"session_id": request.session_id},
            {
                "$push": {"events": {"$each": [prompt_event, response_event]}},
                "$inc": {"message_pairs_logged": 1}
            },
            return_document=ReturnDocument.AFTER
        )

        if session_doc:
            logger.info(f"✅ Query logged to session {request.session_id}")

            # Automatically summarize every N pairs if memory agent available
            pair_count = session_doc.get("message_pairs_logged", 0)
            summary_interval = getattr(memory_agent, "summary_interval", 0) if memory_agent else 0
            if memory_agent and summary_interval and pair_count % summary_interval == 0:
                try:
                    await memory_agent.summarize_session(request.session_id)
                    logger.info(f"📝 Session {request.session_id} summarized at {pair_count} pairs")
                except Exception as summarize_error:
                    logger.warning(f"Failed to summarize session {request.session_id}: {summarize_error}")
        else:
            logger.warning(f"⚠️ Session {request.session_id} not found, only logged to legacy collections")

        # Return response with optional product_cards
        response_data = {
            "response": response_text,
            "citations": citations
        }

        if use_memory and history_for_agents:
            response_data["need_memory"] = True
            response_data["memory_reason"] = "always_on"
        if location_data:
            response_data["user_location"] = location_data

        if product_cards:
            response_data["product_cards"] = product_cards

        if product_structured:
            response_data["product_json"] = product_structured

        if use_memory and memory_context:
            response_data["memory_context"] = memory_context

        if intent_info:
            response_data["intent"] = intent_info.get("intent")
            response_data["agents_used"] = intent_info.get("agents_used")

        # NEW: Pass options if present (from ShoppingAgent)
        if agent_output.get("options"):
            response_data["options"] = agent_output.get("options")

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
        await sessions_collection.update_one(
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
        await sessions_collection.update_one(
            {"session_id": request.session_id},
            {"$push": {"events": error_event}}
        )

        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


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
            final_state = None
            accumulated_response = ""
            accumulated_citations = []
            accumulated_product_cards = None
            
            async for event in graph_app.astream(initial_state):
                # event is a dict with node name as key
                for node_name, node_output in event.items():
                    # Send update for each node
                    update_data = {
                        "type": "node",
                        "node": node_name,
                        "status": "completed"
                    }
                    yield f"data: {json.dumps(update_data)}\n\n"
                    
                    # Accumulate data from each node (skip if None)
                    if node_output:
                        if node_output.get("response"):
                            accumulated_response = node_output["response"]
                        if node_output.get("citations"):
                            accumulated_citations = node_output["citations"]
                        if node_output.get("product_cards"):
                            accumulated_product_cards = node_output["product_cards"]
                        
                        final_state = node_output  # Keep last state for other fields
            
            # Send final response with accumulated data
            if final_state:
                response_data = {
                    "type": "final",
                    "response": accumulated_response or "",
                    "citations": accumulated_citations or [],
                    "product_cards": accumulated_product_cards,
                    "options": final_state.get("shopping_result", {}).get("options") if final_state.get("shopping_result") else None,
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
    existing_session = await sessions_collection.find_one({"session_id": request.session_id})

    if existing_session:
        # Session already exists, don't create duplicate
        incoming_location = (request.environment.location.dict(exclude_none=True)
                             if request.environment and request.environment.location
                             else None)
        stored_location = existing_session.get("environment", {}).get("location")
        if incoming_location and not stored_location:
            await sessions_collection.update_one(
                {"session_id": request.session_id},
                {"$set": {"environment.location": incoming_location}}
            )
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
        "events": [],
        "message_pairs_logged": 0
    }

    sessions_collection.insert_one(session_doc)
    logger.info(f"🎬 Session started: {request.session_id} for user {request.user_id}")

    return {"status": "success", "session_id": request.session_id, "existing": False}


@app.post("/session/event")
async def log_session_event(request: SessionEventRequest):
    """Add an event to an existing session"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    result = await sessions_collection.update_one(
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

    result = await sessions_collection.update_one(
        {"session_id": request.session_id},
        {"$set": {"end_time": datetime.utcnow()}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")

    logger.info(f"🏁 Session ended: {request.session_id}")

    return {"status": "success"}


# ==== MEMORIES CRUD (simple, user-scoped) ====
class MemoryPayload(AppBaseModel):
    user_id: str
    key: str
    value: str


@app.get("/memories")
async def list_memories(user_id: str):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    cursor = db.memories.find({"user_id": user_id}).sort("updated_at", -1)
    memories = await asyncio.to_thread(list, cursor)
    for m in memories:
        m["_id"] = str(m.get("_id", ""))
    return {"memories": memories}


@app.post("/memories")
async def create_memory(payload: MemoryPayload):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    doc = {
        "user_id": payload.user_id,
        "key": payload.key.strip(),
        "value": payload.value.strip(),
        "tokenCount": len(payload.value.split()),
        "updated_at": datetime.utcnow(),
    }
    await asyncio.to_thread(
        db.memories.update_one,
        {"user_id": payload.user_id, "key": payload.key},
        {"$set": doc},
        upsert=True,
    )
    return {"status": "ok"}


@app.patch("/memories/{key}")
async def update_memory(key: str, payload: MemoryPayload):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    result = await asyncio.to_thread(
        db.memories.update_one,
        {"user_id": payload.user_id, "key": key},
        {
            "$set": {
                "value": payload.value.strip(),
                "tokenCount": len(payload.value.split()),
                "updated_at": datetime.utcnow(),
            }
        },
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "ok"}


@app.delete("/memories/{key}")
async def delete_memory(key: str, user_id: str):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    await asyncio.to_thread(db.memories.delete_one, {"user_id": user_id, "key": key})
    return {"status": "ok"}


# ==== FILES (upload/list/download) ====
@app.post("/files")
async def upload_file(
    user_id: str = Form(...),
    session_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    saved = _save_upload(file)
    doc = {
        "user_id": user_id,
        "session_id": session_id,
        "name": saved["name"],
        "path": saved["path"],
        "mime": saved["mime"],
        "size": saved["size"],
        "created_at": datetime.utcnow(),
    }
    result = await asyncio.to_thread(files_collection.insert_one, doc)
    file_id = str(result.inserted_id)
    return {
        "file_id": file_id,
        "name": saved["name"],
        "mime": saved["mime"],
        "size": saved["size"],
    }


@app.get("/files")
async def list_files(user_id: str):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    cursor = files_collection.find({"user_id": user_id}).sort("created_at", -1)
    items = await asyncio.to_thread(list, cursor)
    files_out = []
    for item in items:
        files_out.append(
            {
                "file_id": str(item.get("_id")),
                "name": item.get("name"),
                "mime": item.get("mime"),
                "size": item.get("size"),
                "created_at": item.get("created_at"),
                "session_id": item.get("session_id"),
            }
        )
    return {"files": files_out}


@app.get("/files/{file_id}")
async def download_file(file_id: str, user_id: str):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file id")

    doc = files_collection.find_one({"_id": oid, "user_id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")
    path = Path(doc["path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="File missing on server")
    return FileResponse(path, media_type=doc.get("mime") or "application/octet-stream", filename=doc.get("name"))


@app.delete("/files/{file_id}")
async def delete_file(file_id: str, user_id: str):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file id")
    doc = files_collection.find_one({"_id": oid, "user_id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")
    path = Path(doc["path"])
    if path.exists():
        try:
            path.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete file from disk: {e}")
    await asyncio.to_thread(files_collection.delete_one, {"_id": oid, "user_id": user_id})
    return {"status": "ok"}


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Retrieve a complete session with all events"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    session = await sessions_collection.find_one({"session_id": session_id}, {"_id": 0})

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Convert datetime objects to ISO format
    if "start_time" in session and session["start_time"]:
        session["start_time"] = session["start_time"].isoformat()
    if "end_time" in session and session["end_time"]:
        session["end_time"] = session["end_time"].isoformat()

    return session


@app.get("/session/{session_id}/experiment")
async def get_session_experiment(session_id: str):
    """Get experiment_id for a session"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    session = await sessions_collection.find_one({"session_id": session_id}, {"experiment_id": 1, "_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"experiment_id": session.get("experiment_id")}


@app.patch("/session/{session_id}/experiment")
async def update_session_experiment(session_id: str, payload: ExperimentPayload):
    """Update experiment_id for a session"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    result = await sessions_collection.update_one(
        {"session_id": session_id},
        {"$set": {"experiment_id": payload.experiment_id}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"experiment_id": payload.experiment_id}


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
