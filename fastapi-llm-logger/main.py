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

# ==== MONGODB CONFIG ====
MONGODB_URI = os.getenv("MONGODB_URI")
MONGO_DB = os.getenv("MONGO_DB", "llm_experiment")

try:
    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client[MONGO_DB]
    queries_collection = db["queries"]
    events_collection = db["events"]
    logger.info("✅ Connected to MongoDB")
except Exception as e:
    logger.error(f"❌ MongoDB connection failed: {e}")
    db = None


# ==== API KEYS ====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ==== REQUEST SCHEMAS ====
class QueryRequest(BaseModel):
    user_id: str
    session_id: str
    query: str
    model_provider: str  # "openai", "anthropic", or "openrouter"
    model_name: Optional[str] = None
    web_search: Optional[bool] = False


class LogEventRequest(BaseModel):
    user_id: str
    session_id: str
    event_type: str
    query: Optional[str] = None
    target_url: Optional[str] = None
    page_url: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


# ==== HELPER FUNCTIONS ====
def call_openai(model: str, query: str):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    """Call OpenAI Responses API safely with native web search."""
    messages = [
        {"role": "system", "content": (
                "You are ChatGPT: a friendly, concise, markdown-savvy assistant. "
                "Use conversational tone, structure answers with short paragraphs and lists when helpful. "
                "Do not reveal chain-of-thought. Be helpful and practical.")},
        {"role": "user", "content": query}
    ]

    response = client.responses.create(
        model=model,
        input=messages,
        tools=[{"type": "web_search"}]
    )

    # --- Safe text extraction ---
    text = ""
    sources = []
    if getattr(response, "output", None):
        for item in response.output:
            contents = getattr(item, "content", []) or []
            for content in contents:
                if getattr(content, "type", None) == "output_text":
                    text += getattr(content, "text", "")
                # --- Extract annotations (GPT-5 format) ---
                annotations = getattr(content, "annotations", []) or []

                for ann in annotations:
                    # GPT-5 annotations are objects, not dicts
                    ann_type = getattr(ann, "type", None) or (ann.get("type") if isinstance(ann, dict) else None)
                    if ann_type == "url_citation":
                        sources.append({
                            "title": getattr(ann, "title", "") or (ann.get("title") if isinstance(ann, dict) else ""),
                            "url": getattr(ann, "url", "") or (ann.get("url") if isinstance(ann, dict) else "")
                        })

    else:
        text = getattr(response, "output_text", "") or ""



    return text.strip(), sources, response.model_dump()


def call_anthropic(model: str, query: str):
    """Call Anthropic API directly (Claude 3 series)"""
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": query}
        ],
        "plugins": [{"id": "web", "max_results": 5}],  # ✅ built-in OpenRouter web plugin
    }

    response = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()

    # Claude 3 returns list of content blocks
    content_blocks = data.get("content", [])
    text_parts = []
    citations = []

    for block in content_blocks:
        if block.get("type") == "text":
            text_parts.append(block.get("text", ""))
        elif block.get("type") == "citations":
            for c in block.get("citations", []):
                citations.append({
                    "source": c.get("source", ""),
                    "url": c.get("url", ""),
                })

    text = "\n".join(text_parts)
    return text, citations, data


def call_openrouter(model: str, query: str):
    """Call OpenRouter API directly (for other models)"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that provides informative and referenced answers."},
            {"role": "user", "content": query}
        ]
    }

    # 🧠 Enable web search if requested
    if model.startswith("openai/"):
        payload["tools"] = [{"type": "web_search"}]
    else:
        payload["plugins"] = [{"id": "web", "max_results": int(5)}]

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    text = data["choices"][0]["message"]["content"]
    citations = data.get("references") or []
    return text, citations, data


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
    """Query selected LLM provider, store response + citations"""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    logger.info(f"🔍 Processing query: {request.query} from user {request.user_id}")

    try:
        model = request.model_name

        if request.model_provider == "openai":
            response_text, citations, raw = call_openai(model, request.query)
        elif request.model_provider == "anthropic":
            response_text, citations, raw = call_anthropic(model, request.query)
        elif request.model_provider == "openrouter":
            response_text, citations, raw = call_openrouter(model, request.query)
        else:
            raise HTTPException(status_code=400, detail="Invalid model provider")

        # Log to MongoDB
        query_log = {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "query": request.query,
            "response": response_text,
            "model_provider": request.model_provider,
            "model_used": model,
            "timestamp": datetime.utcnow(),
            "citations": citations,
            "raw": raw,
        }
        queries_collection.insert_one(query_log)

        return {"response": response_text, "citations": citations}

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise HTTPException(status_code=500, detail=f"API request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/log_event")
async def log_event(request: LogEventRequest):
    """Record user interaction events (clicks, browsing, conversions)"""
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
