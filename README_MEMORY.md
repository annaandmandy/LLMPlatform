# LLMPlatform Memory System

This document describes the memory and context retrieval system used in LLMPlatform.

## Overview

The memory system provides persistent context across conversations by:
1. Storing message embeddings for semantic search (RAG)
2. Generating periodic session summaries
3. Maintaining user-specific key/value facts
4. Injecting relevant context into LLM prompts

---

## Memory Block Architecture

### Summary Generation (Every N Messages)

**Configuration:**
- Default interval: **10 message pairs** (20 turns)
- Configured in `MemoryAgent.__init__(summary_interval=10)`

**When Summaries Are Created:**
```
Query received → Response generated → Pair count checked
                                           ↓
                              If pair_count % 10 == 0
                                           ↓
                              Generate session summary
```

**Two Summary Methods:**

| Method | Model | Trigger | Output |
|--------|-------|---------|--------|
| LLM-based | gpt-4o-mini | Primary | 4-6 bullet points, <120 tokens |
| Rule-based | N/A | Fallback if LLM fails | Extracted Q&A pairs + key points |

**LLM Summary Prompt:**
- Analyzes last 12 messages
- Captures: tasks, decisions, preferences, constraints, data values
- Temperature: 0.2 (deterministic)

**Summary Storage (MongoDB `summaries` collection):**
```python
{
  "session_id": str,
  "user_id": str,
  "summaries": [
    {
      "t": datetime,           # When created
      "text": str,             # Summary content
      "message_count": int,    # Messages summarized
      "model": str             # "gpt-4o-mini" or "rule_based"
    }
  ],
  "created_at": datetime
}
```

---

## Similarity Check (Semantic Search)

### Embedding Model
- **Model**: `text-embedding-3-small` (OpenAI)
- **Dimensions**: 1536
- **Location**: `utils/embeddings.py`

### Similarity Calculation
```python
# Cosine similarity
similarity = dot(vec1, vec2) / (norm(vec1) * norm(vec2))
# Range: 0.0 to 1.0 (for text)
# Threshold: 0.45 minimum
```

### Search Process

1. **Create query embedding** from user's message
2. **Fetch candidate vectors** (up to 200 recent from session)
3. **Cross-session lookup** if session has <50 vectors (extends from user's other sessions)
4. **Compute similarity** for all candidates
5. **Return top-K** (default K=8) where similarity > 0.45

**Vector Storage (MongoDB `vectors` collection):**
```python
{
  "session_id": str,
  "user_id": str,
  "message_index": int,
  "role": "user" | "assistant",
  "content": str,
  "embedding": List[float],    # 1536 dimensions
  "timestamp": datetime
}
```

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `top_k` | 8 | Max similar messages to retrieve |
| Similarity threshold | 0.45 | Minimum similarity score |
| Vector fetch limit | 200 | Max vectors to compare per query |
| Cross-session trigger | <50 | Vectors threshold to expand search |

---

## Information Fed Into Prompts

### Complete Memory Bundle

When `use_memory=true`, the following data is retrieved and injected:

```python
memory_context = {
  "context": [                    # Semantically similar messages
    {
      "role": str,
      "content": str,
      "similarity": float,        # 0.45 - 1.0
      "timestamp": datetime,
      "session_id": str
    }
  ],
  "recent_messages": [            # Last 6 Q&A pairs
    {
      "role": str,
      "content": str,
      "timestamp": datetime
    }
  ],
  "summaries": [                  # Session summaries
    {
      "session_id": str,
      "summary": str,
      "message_count": int,
      "model": str,
      "timestamp": datetime
    }
  ],
  "memories": [                   # User key/value facts
    {
      "key": str,
      "value": str,
      "updated_at": datetime,
      "tokenCount": int
    }
  ],
  "query_embedding_dim": 1536
}
```

### Prompt Assembly Order

The `WriterAgent._build_prompt()` method assembles context in this order:

```
1. Recent Conversation History (last 10 items, 200 chars each)
2. Image Understanding (if images analyzed)
3. Relevant Past Context:
   a. Session/Global Summaries (3 most recent, 240 chars each)
   b. Stored User Facts (5 items, full key/value)
   c. Semantically Similar Messages (4 items with scores, 200 chars each)
   d. Recent Turns (6 items, 180 chars each)
4. User Location (if available)
5. User Query
```

### Content Truncation Limits

| Content Type | Max Items | Max Chars |
|--------------|-----------|-----------|
| History messages | 10 | 200 |
| Summaries | 3 | 240 |
| User memories | 5 | Full |
| Retrieved context | 4 | 200 |
| Recent messages | 6 | 180 |

---

## MongoDB Collections

| Collection | Purpose | Key Fields |
|------------|---------|------------|
| `vectors` | Message embeddings for RAG | session_id, embedding, content |
| `summaries` | Periodic session summaries | session_id, summaries[] |
| `memories` | User facts (key/value) | user_id, key, value |
| `sessions` | Raw session events | session_id, events[] |

---

## System Flow Diagram

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│         /query Endpoint             │
│         (main.py:717)               │
└─────────────────────────────────────┘
    │
    ├─→ Intent Detection (keyword + embedding)
    │
    ├─→ Log prompt event to sessions
    │
    ▼
┌─────────────────────────────────────┐
│   If use_memory=true:               │
│   MemoryAgent.run(context_bundle)   │
│   ┌─────────────────────────────┐   │
│   │ 1. Semantic search (top-8)  │   │
│   │ 2. Recent messages (6 pairs)│   │
│   │ 3. Session summaries (3)    │   │
│   │ 4. User memories (8)        │   │
│   └─────────────────────────────┘   │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│   CoordinatorAgent routes by intent │
│            ↓                        │
│   WriterAgent receives context      │
│   ┌─────────────────────────────┐   │
│   │ _build_prompt() assembles:  │   │
│   │ • History                   │   │
│   │ • Summaries                 │   │
│   │ • Memories                  │   │
│   │ • Similar messages          │   │
│   │ • Location                  │   │
│   │ • Query                     │   │
│   └─────────────────────────────┘   │
│            ↓                        │
│   Call LLM provider                 │
└─────────────────────────────────────┘
    │
    ├─→ Store embeddings (async)
    │
    ├─→ Log response event
    │
    ▼
┌─────────────────────────────────────┐
│ If pair_count % 10 == 0:            │
│   Generate session summary          │
│   (LLM-based or rule-based)         │
└─────────────────────────────────────┘
    │
    ▼
  Response
```

---

## API Response with Memory

When memory is enabled, the `/query` response includes:

```python
{
  "response": str,
  "citations": List[Dict],
  "memory_context": {
    "context": [...],
    "recent_messages": [...],
    "summaries": [...],
    "memories": [...]
  },
  "intent": str,
  "agents_used": List[str],
  "need_memory": bool,
  "memory_reason": str
}
```

---

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | Required | For embeddings and summaries |
| `USE_LLM_INTENT` | false | Enable embedding-based intent |

### MemoryAgent Parameters

```python
MemoryAgent(
    db=mongodb_instance,
    summary_interval=10  # Message pairs before summary
)
```

### Request Parameters

```python
# In /query request body
{
  "use_memory": true,    # Enable/disable memory retrieval
  "top_k": 8             # Number of similar messages to retrieve
}
```

---

## Design Decisions

1. **Similarity Threshold (0.45)**: Permissive to allow moderately related content
2. **Summary Interval (10 pairs)**: Balances freshness vs. API costs
3. **Hybrid Summaries**: Rule-based fallback ensures reliability
4. **Async Embedding Storage**: Non-blocking for faster responses
5. **Cross-Session Retrieval**: Enables user-level context continuity
6. **Token-Aware Truncation**: Prevents context overflow

---

## File Locations

| Component | Path |
|-----------|------|
| Memory Agent | `fastapi-llm-logger/agents/memory_agent.py` |
| Writer Agent | `fastapi-llm-logger/agents/writer_agent.py` |
| Embeddings | `fastapi-llm-logger/utils/embeddings.py` |
| Main Endpoint | `fastapi-llm-logger/main.py` |
| Provider Prompts | `fastapi-llm-logger/config/provider_prompts.json` |
