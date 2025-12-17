# FastAPI + MongoDB Backend

## Overview

This is a FastAPI backend service that handles multi-user LLM interactions and logs all user events for analysis.

## Features

- **Multi-Agent System**: Powered by LangGraph with specialized agents:
  - `CoordinatorAgent`: Intent detection and routing
  - `WriterAgent`: Generates final responses with context
  - `ProductAgent`: Searches for products via SerpAPI
  - `MemoryAgent`: Handles conversation history and RAG retrieval
  - `ShoppingAgent`: Conducts diagnostic interviews for recommendations
  - `VisionAgent`: Analyzes image attachments
- **Unified Model Access**: Direct integration with OpenAI, Anthropic, Google Gemini, and OpenRouter
- **Async MongoDB**: High-performance non-blocking writes for logging capabilities

## API Endpoints

### `POST /query`
Generate an LLM response and log the query.

**Request:**
```json
{
  "user_id": "u_123",
  "session_id": "123",
  "query": "Compare Nike and Adidas branding"
}
```

**Response:**
```json
{
  "response": "Nike focuses on innovation...",
  "source": [
    {
      "title": "Example Source",
      "url": "https://example.com",
      "content": "Sample content..."
    }
  ]
}
```

### `POST /log_event`
Record user interactions.

**Request:**
```json
{
  "user_id": "u_123",
  "session_id": "123",
  "event_type": "click",
  "query": "Compare Nike and Adidas",
  "target_url": "https://nike.com",
  "page_url": "https://experiment.com/results",
  "extra_data": {
    "mouse_position": [230, 440],
    "scroll_depth": 0.65
  }
}
```

### `GET /export_data`
Retrieve all logged data.

**Response:**
```json
{
  "total_records": 150,
  "queries_count": 50,
  "events_count": 100,
  "data": [...]
}
```

### `GET /status`
Health check endpoint.

**Response:**
```json
{
  "status": "running",
  "mongodb_connected": true,
  "model": "gpt-4o-mini"
}
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:
```bash
MONGODB_URI=mongodb+srv://...
MONGO_DB=llm_experiment

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
OPENROUTER_API_KEY=sk-or-...

# Tools
SERPAPI_KEY=...
```

### 3. Run Locally

```bash
uvicorn main:app --reload
```

Visit: http://localhost:8000

### 4. Test Endpoints

```bash
# Health check
curl http://localhost:8000/status

# Query test
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "session_id": "test_session", "query": "What is AI?"}'
```

## Docker Deployment

### Quick Start with Docker

**Option 1: Quick Start Script (Recommended)**

```bash
# Make script executable
chmod +x docker-quickstart.sh

# Build and run
./docker-quickstart.sh build
./docker-quickstart.sh run

# Or use docker-compose with local MongoDB
./docker-quickstart.sh compose-dev
```

**Option 2: Manual Docker Commands**

```bash
# Build image
docker build -t llm-logger .

# Run container
docker run -d -p 8000:8000 --env-file .env llm-logger

# View logs
docker logs -f llm-logger
```

**Option 3: Docker Compose**

```bash
# Production (with cloud MongoDB)
docker-compose up -d

# Development (with local MongoDB + Mongo Express UI)
docker-compose -f docker-compose.dev.yml up -d
```

### Docker Files

- **`Dockerfile`** - Standard production image
- **`Dockerfile.dev`** - Development with hot reload
- **`Dockerfile.prod`** - Optimized multi-stage build
- **`docker-compose.yml`** - Production compose
- **`docker-compose.dev.yml`** - Development with local MongoDB
- **`docker-quickstart.sh`** - Convenience script for common operations

For detailed Docker documentation, see [DOCKER.md](DOCKER.md)

## Deploy to Render

1. Push code to GitHub
2. Create new Web Service on Render
3. Connect your GitHub repository
4. Set environment variables in Render dashboard
5. Deploy!

## MongoDB Setup

1. Create a free cluster on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a database user
3. Whitelist your IP address (or use 0.0.0.0/0 for all IPs)
4. Get your connection string and add it to `.env`

## Project Structure

```
fastapi-llm-logger/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── .env.example        # Example environment variables
├── Dockerfile          # Docker configuration
└── README.md           # This file
```

## Collections

### `queries`
Stores all LLM queries and responses:
- user_id
- session_id
- query
- response
- model_used
- timestamp
- sources

### `events`
Stores all user interaction events:
- user_id
- session_id
- event_type
- query
- target_url
- page_url
- extra_data
- timestamp

## License

MIT
