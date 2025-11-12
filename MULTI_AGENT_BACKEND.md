# Multi-Agent Backend Deep Dive

This document summarizes how the FastAPI backend wires together its multi-agent system, how requests flow through the agents, and where the current implementation shows gaps or duplicated logic.

## Stack & Bootstrapping
- FastAPI boots the service and, on startup, calls `initialize_agents()` so the multi-agent graph is ready before the first request arrives (`fastapi-llm-logger/main.py:50-249`).
- `initialize_agents()` instantiates `MemoryAgent`, `ProductAgent`, `WriterAgent`, and `CoordinatorAgent`, injects the shared MongoDB handle, registers LLM callables with the writer, and hands the specialized agents to the coordinator (`fastapi-llm-logger/main.py:217-245`).
- Each agent inherits from `BaseAgent`, which wraps `execute()` with latency tracking and optionally logs executions to the `agent_logs` collection through `asyncio.to_thread` so FastAPI’s loop is not blocked (`fastapi-llm-logger/agents/base_agent.py:20-118`).

## Agent Responsibilities
| Agent | Role | Key Implementation Notes |
| --- | --- | --- |
| `CoordinatorAgent` | Entry point that detects intent, picks downstream agents, and merges their outputs. | Runs `detect_intent()` (regex/LLM hybrid) and orchestrates conditional pipelines (`fastapi-llm-logger/agents/coordinator.py:81-221`). |
| `MemoryAgent` | Provides conversation summaries and semantic retrieval from stored embeddings. | Reads from `sessions` and `vectors` collections, exposes `summarize`/`retrieve` actions, and can persist per-message embeddings (`fastapi-llm-logger/agents/memory_agent.py:20-205`). |
| `ProductAgent` | Extracts concrete product mentions and fetches real listings via SerpAPI. | Uses OpenAI JSON mode first, falls back to regex heuristics, then hits Google Shopping (`fastapi-llm-logger/agents/product_agent.py:37-213`). |
| `WriterAgent` | Builds the final prompt (history + memory context + intent instructions) and calls the appropriate provider helper. | Relies on injected callables such as `call_openai`/`call_anthropic` and returns response text, citations, and token data (`fastapi-llm-logger/agents/writer_agent.py:24-210`). |

### Intent Detection
`utils/intent_classifier.py` loads regex patterns from `intent_keywords.json`, offers an optional OpenRouter-powered classifier, and exposes `detect_intent()` for asynchronous use (`fastapi-llm-logger/utils/intent_classifier.py:17-152`).

## /query Workflow
1. **Request intake** – `/query` validates the request body (`QueryRequest`) and immediately aborts if MongoDB is unavailable (`fastapi-llm-logger/main.py:594-608`).
2. **Multi-agent path** – If agents were initialized, the endpoint builds `agent_request` with the query, session/user IDs, selected model, and any prior history, then calls `CoordinatorAgent.run()` (`fastapi-llm-logger/main.py:620-635`).
3. **Intent-based branching** – The coordinator runs `detect_intent()` and routes to different agent combos:
   - `product_search`: call the writer for a narrative answer, then run the product agent for structured cards (`fastapi-llm-logger/agents/coordinator.py:98-125`).
   - `summarize`: memory agent produces a transcript, which becomes the writer’s history (`fastapi-llm-logger/agents/coordinator.py:127-149`).
   - `retrieve_memory`: memory agent fetches relevant past turns so the writer can cite them (`fastapi-llm-logger/agents/coordinator.py:151-175`).
   - `general`: writer runs solo with any supplied history (`fastapi-llm-logger/agents/coordinator.py:176-192`).
4. **Embedding side effects** – After a successful multi-agent response, the backend fires two embedding writes (user query + assistant reply) via `MemoryAgent.store_message_embedding()` so future retrieval has fresh vectors (`fastapi-llm-logger/main.py:651-667`, `fastapi-llm-logger/agents/memory_agent.py:200-235`).
5. **Persistence & telemetry** – The response plus metadata (intent, citations, latency, tokens, product cards) is written to `queries_collection`, and two normalized events (`prompt`, `model_response`) are appended to the live session document (`fastapi-llm-logger/main.py:670-748`).
6. **Fallback path** – If the coordinator failed to initialize the graph, `/query` falls back to a direct `detect_intent()` call plus a provider-specific function (OpenAI/Anthropic/OpenRouter/Google) (`fastapi-llm-logger/main.py:620-709`).

## Memory & Product Data Flow
- **Summaries/RAG** – Session events store both prompts and responses, letting the memory agent rebuild transcripts or compute summaries on demand (`fastapi-llm-logger/agents/memory_agent.py:90-149`). Semantic retrieval is powered by OpenAI embeddings stored in `vectors` (`fastapi-llm-logger/agents/memory_agent.py:170-205`).
- **Product enrichment** – `ProductAgent` is invoked after the writer synthesizes an answer. It extracts up to three product mentions via OpenAI JSON output or regex, then queries SerpAPI for live pricing/info before returning unified cards and structured JSON (`fastapi-llm-logger/agents/product_agent.py:88-213`).

## Logging & Analytics
- Legacy interaction logging remains available via `/log_event`, which writes directly to the `events` collection (`fastapi-llm-logger/main.py:825-844`).
- The newer sessionized flow stores environment metadata, arbitrary UI events, prompts, and model responses under `/session/*` endpoints (`fastapi-llm-logger/main.py:890-969`).
- `/tokens/data` aggregates prompt/completion/total tokens by provider and model for dashboarding (`fastapi-llm-logger/main.py:1001-1080`).

## Notable Gaps & Duplicate Logic
1. **Product context never feeds back into the answer.** In the `product_search` branch the writer is invoked *before* the product agent, and the writer request explicitly sets `product_cards=None` (`fastapi-llm-logger/agents/coordinator.py:98-125`). As a result, the final narrative response cannot reference the real products the second agent discovers, defeating the purpose of multi-agent enrichment.
2. **Model selection can be `None`.** `/query` copies `request.model_name` directly into the agent request and downstream provider calls without a fallback (`fastapi-llm-logger/main.py:615-633`). `WriterAgent` assumes `model` is a string and immediately calls `.lower()` on it (`fastapi-llm-logger/agents/writer_agent.py:95-109`), so any client that omits `model_name` (while still supplying `model_provider`) will trigger an attribute error instead of falling back to the documented default.
3. **Event logging lives in two divergent systems.** The legacy `/log_event` endpoint continues to write to `events_collection`, while real-time session logging writes analogous records under `sessions.events` (`fastapi-llm-logger/main.py:825-969`). Because `/query` only augments sessions and `/log_event` only augments `events`, analytics now have to stitch together two partially overlapping data sources, and events can go missing from one path if callers mix endpoints.
4. **Memory summarization cadence is a stub.** `MemoryAgent` exposes a `summary_interval` parameter but never uses it outside of assignment (`fastapi-llm-logger/agents/memory_agent.py:30-63`). There is no background task or trigger that keeps summaries up to date, so intent-based summarization simply re-processes the entire session on demand, limiting the promised “mid-term memory” behavior.

These gaps are the primary places where the multi-agent workflow either fails to use the data it gathers or duplicates logic that could be unified.
