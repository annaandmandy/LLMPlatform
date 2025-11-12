LLM Multi-Agent Upgrade — Claude TODO README
🎯 Goal

Upgrade my current FastAPI + Next.js + MongoDB LLM platform
into a modular multi-agent architecture with the following abilities:

Context memory (short-term chat history)

Mid-term summarization + long-term RAG memory

Product search and preview card generation

Modular Agents (Coordinator / Memory / Product / Writer)

Easy extension for future agents (Research, Analytics…)

Claude should generate or refactor Python + TypeScript code accordingly.

🧩 System Overview

Frontend: Next.js / React / Tailwind
Backend: FastAPI / MongoDB / LangChain-compatible structure
LLM Providers: OpenAI · Anthropic · Google · OpenRouter

🧱 Proposed Agents
Agent	Responsibility	Tech
🧑‍✈️ CoordinatorAgent	Detect intent, route task to sub-agents	FastAPI orchestration layer
🧠 MemoryAgent	Summarize, embed, RAG retrieval	LangChain or custom embedding + MongoDB + vector store
🛍️ ProductAgent	Query product DB / external API + return cards	FastAPI endpoint + schema.org/Product structure
✍️ WriterAgent	Combine results, produce final markdown answer	LLM call with templated prompt
✅ Tasks for Claude
1️⃣ Refactor /query → /agent/query

Goal: make it a unified entry point handled by CoordinatorAgent.
Steps:

Create agents/coordinator.py with route_request(request):

intent = detect_intent(request.query)
if intent == "product_search":
    return product_agent.handle(request)
elif intent == "summarize":
    return memory_agent.summarize(request)
elif intent == "retrieve_memory":
    return memory_agent.retrieve(request)
else:
    return writer_agent.respond(request)


Keep backward compatibility with /query.

2️⃣ Implement MemoryAgent

Files: agents/memory_agent.py

Functions:

summarize_session(session_id) → every 10 turns store summary in summaries collection

store_embedding(session_id, role, content) → save embedding vector in vectors collection

query_similar(text, top_k=3) → cosine similarity search

retrieve_context(query) → return related past context to CoordinatorAgent

Collections:

summaries: { "session_id": "...", "summaries": [ { "t": "...", "text": "..." } ] }
vectors: { "session_id": "...", "role": "user", "content": "...", "embedding": [0.12, …] }

3️⃣ Implement ProductAgent

Files: agents/product_agent.py

Goal: return product info cards.
Steps:

Create /search/products endpoint (FastAPI):

@app.get("/search/products")
async def search_products(query: str):
    results = db.products.find({"$text": {"$search": query}}).limit(10)
    return list(results)


Structure each result as:

{
  "title": "Eco Smart Filter",
  "price": 59.99,
  "image": "https://cdn.myshop.com/filter.jpg",
  "url": "https://myshop.com/product/filter",
  "seller": "EcoStore"
}


In Frontend (/components/ProductCards.tsx),
render Tailwind grid of preview cards with image, price, link, and OpenGraph metadata.

4️⃣ Implement WriterAgent

Files: agents/writer_agent.py

Goal: merge context from other agents and craft final reply.
Prompt Example:

System: You are an assistant that integrates memory and product data.
User query: {user_query}
Relevant memory: {memory_context}
Product results: {product_context}
Generate an organized markdown reply.

5️⃣ Add detect_intent() Utility

Files: utils/intent_classifier.py

Use small LLM call or keyword rules:

if "buy" in q or "price" in q: return "product_search"
if "remember" in q or "summary" in q: return "summarize"
if "show" in q and "history" in q: return "retrieve_memory"
return "general"

6️⃣ Frontend Integration

Modify:

QueryBox.tsx:
include history (last 10 messages) in fetch body.

Home.tsx:
switch to /agent/query endpoint.

MessageHistory.tsx:
render markdown with product cards if present.

7️⃣ Memory Management Rules
Layer	Source	Retain	Purpose
LocalStorage	Current session	10 messages	Fast load
MongoDB (sessions)	Full events	Unlimited	Raw log
MongoDB (summaries)	Every 10 turns	1 per batch	Mid-term recall
Vector DB	Embeddings	All	Long-term semantic memory
8️⃣ Optional: LangGraph Workflow

Claude may design a simple LangGraph YAML or Python graph:

Planner → [Memory | Product | Research] → Writer


with visualization and metrics (token usage, latency).

🚀 Deliverables

Claude should output:

All new agents/*.py modules

Updated FastAPI routes (/agent/query, /search/products)

MongoDB schemas for sessions, summaries, vectors

Example frontend components for product preview cards

Optional LangGraph workflow example

💬 End Goal

A modular multi-agent LLM system that can chat, remember, summarize, retrieve, search products, and render smart preview cards — structured for long-term scalability and easier maintenance.