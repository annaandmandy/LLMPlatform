# 🧠 Project Spec: FastAPI + LiteLLM + MongoDB Backend for Multi-User LLM Interaction Logging

## 📘 Overview

You are Claude, a coding assistant that will generate a **Python FastAPI backend** project.

The goal is to create **one backend service** that handles multiple users interacting with an LLM interface and records every action:
- user queries to the LLM  
- clicks on recommended links  
- browsing or navigation events  
- conversions or other interactions  

All of these should be **stored in MongoDB** for later analysis.

The system will be used by a front-end (e.g., Next.js) that sends JSON events to this backend.

---

## 🎯 Architecture Summary

Frontend (Next.js or any client)
↓ (HTTP)
FastAPI backend (with LiteLLM + MongoDB)
↓
MongoDB Atlas (cloud database)


---

## ⚙️ Functional Requirements

### Core Goals
1. Handle user queries and responses through `/query`
2. Record **all** user interactions (clicks, browsing, conversions) through `/log_event`
3. Allow export of the complete dataset through `/export_data`
4. Support multiple users simultaneously
5. Use LiteLLM for unified multi-model access

---

## 🧩 API Design

### `/query` (POST)
**Purpose:** Generate an LLM response and log the query.

**Request JSON**
```json
{
  "user_id": "u_123",
  "session_id": "123",
  "query": "Compare Nike and Adidas branding"
}

{
  "response": "Nike focuses on innovation and emotional storytelling...",
  "source": [{"title": "The 23 Best Boxed Chocolates of 2025, Tested & Reviewed", "url": "https://www.seriouseats.com/best-chocolate-boxes-8414371", "content": "Sometimes simple is best, and this was a lovely box of dainty chocolates with classic flavors, like hazelnut, almond, crunchy praline (which had a faint saltiness that we loved), and whipped ganache. Like many a good box of chocolates, this one not only had classic combinations and new flavors, but it was also a box of well-crafted bonbons. We also loved the Classic Box of Chocolates (21 bonbons in seven flavors) which is made in partnership with Feve Artisan Chocolatiers. Plus, it’s a beautiful box with a vast array of flavors, including classics like chocolate raspberry, as well as floral caramels and spicy ganaches. If you like fruity, floral flavors, this is the perfect box of chocolates."}, {"title": "25 Chocolate Brands, Ranked Worst To Best - Tasting Table", "url": "https://www.tastingtable.com/788370/chocolate-brands-ranked-worst-to-best/", "content": "We feel like other chocolate brands are better tasting and affordable, hence our lower ranking of Cadbury. Scharffen Berger sells baking chocolate and chocolate bars, which differs from many of the other brands on our list. Today, Hershey is the umbrella for over 90 brands and products, including sweets, mints, and snacks, but here we'll stick with discussing the company's best chocolate offerings. The chocolates from Lindt taste incredibly high-quality, creamy, and delicious, so it's no secret the brand snagged such a high spot on this list. Not only does the Vermont-based company (a family-run business that has been around since 1983) sell bars like seemingly every other brand on our ranking, but it also makes delicious chocolate-covered caramels, English toffee, baking chocolate, hot chocolate, and more. This is chocolate, after all."}, {"title": "The Best Chocolate Brands in 2025 | MSA", "url": "https://www.mysubscriptionaddiction.com/directory/chocolate", "content": "The Best Chocolate Brands in 2025 · Vegancuts Snack Box · Mantry · Tasterie · Charleston Epicurean · Japan Crate · TreatsBox · Caroo · Secret Snacks."}, ]
}
Behavior

Use LiteLLM’s completion() to get the model response.

Log { user_id, session_id, query, response, timestamp, model_used } to the queries collection in MongoDB.

Return the response text.

/log_event (POST)

Purpose: Record user interactions such as clicks, browsing, and conversions.

Request JSON
{
  "user_id": "u_123",
  "session_id":"123",
  "event_type": "click",
  "query": "Compare Nike and Adidas",
  "target_url": "https://nike.com",
  "page_url": "https://experiment.com/results",
  "extra_data": {
    "mouse_position": [230, 440],
    "scroll_depth": 0.65
  }
}

Behavior

Accept any event_type (e.g., "click", "browse", "conversion", "hover", "scroll").

Save all event fields plus a UTC timestamp into the events collection in MongoDB.

Support dynamic additional keys via extra_data.

/export_data (GET)

Purpose: Retrieve all logs for analysis.

Behavior

Combine or export data from both queries and events collections.

Return JSON array:

[
  { "type": "query", "user_id": "u_123", "session_id":"123", "query": "...", "response": "..." },
  { "type": "event", "user_id": "u_123", "session_id":"123", "event_type": "click", "target_url": "..." }
]

Project Structure

Claude should generate this structure:

fastapi-llm-logger/
├── main.py
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md

main.py

Implement the following endpoints:

/query:

Receives { user_id, query }

Calls LiteLLM → stores query + response in MongoDB

/log_event:

Receives { user_id, event_type, ... }

Saves all interaction data to MongoDB

/export_data:

Returns all records as JSON

Additional details:

Use async def endpoints

Include a /status route returning { "status": "running" }

Automatically add UTC timestamps

Use environment variables for configuration

requirements.txt
fastapi
uvicorn
litellm
pymongo
python-dotenv

.env.example
MONGODB_URI=mongodb+srv://<user>:<password>@cluster0.mongodb.net
MONGO_DB=llm_experiment
LITELLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-xxxxxxx

Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

⚙️ Behavior Details

All endpoints return JSON.

Each record saved to MongoDB must include:

user_id

timestamp (UTC)

All original request fields

/query and /log_event write to separate collections: queries, events.

Backend should catch exceptions and return clear error JSON:

{ "error": "database connection failed" }

✅ Output Expectation

Claude must produce:

Complete Python FastAPI backend source code

All files listed in the structure above

Working MongoDB + LiteLLM integration

Ready-to-deploy Dockerfile and .env.example

Code that supports saving query + click + browse + conversion events

💡 Developer Style Guide

Follow PEP8

Use async def for endpoints

Add meaningful logging (console print or logging module)

Keep code minimal and readable (no extra dependencies)

Include clear comments explaining each endpoint

🧩 Summary

Claude, please generate a complete backend project that:

Uses FastAPI + LiteLLM + MongoDB

Logs queries, clicks, browsing events, conversions

Is multi-user capable

Is ready to deploy on Render with Docker

Provides /query, /log_event, /export_data, /status endpoints

Output all code, files, and example configurations exactly as described.