# LLM Platform Backend 🚀

A production-ready, enterprise-grade FastAPI backend for multi-LLM interactions with vector search, multi-agent orchestration, and intelligent query processing. Built with modern Python practices and designed for scalability.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-green.svg)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-brightgreen.svg)](https://www.mongodb.com/atlas)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [API Documentation](#-api-documentation)
- [Development](#-development)
- [Deployment](#-deployment)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

**LLM Platform Backend** is a sophisticated multi-agent AI system that provides:

- **Unified Interface** for multiple LLM providers (OpenAI, Anthropic, Google, OpenRouter)
- **Intelligent Agent Orchestration** with specialized agents for memory, shopping, vision, and writing
- **Vector Search** powered by MongoDB Atlas for semantic similarity and RAG
- **Real-time Streaming** with Server-Sent Events (SSE)
- **Production-Ready** with comprehensive logging, monitoring, and error handling

### Use Cases

- 💬 **Conversational AI** - Build chatbots with memory and context awareness
- 🛍️ **Shopping Assistants** - Product search with intelligent recommendation flow
- 📊 **Document Q&A** - RAG-powered question answering over your documents
- 🔍 **Semantic Search** - Find similar queries and responses using vector embeddings
- 🎨 **Vision AI** - Process images with vision-capable models

---

## ✨ Features

### 🤖 Multi-Agent System

Built on **LangGraph**, our agent system provides intelligent coordination:

- **CoordinatorAgent** - Routes requests to specialized agents
- **MemoryAgent** - RAG-based context retrieval and conversation summarization
- **ShoppingAgent** - Interactive product discovery with 3-round interview
- **WriterAgent** - Context-aware response generation with provider-specific prompting
- **VisionAgent** - Image understanding and analysis
- **ProductAgent** - Real-time product search via SerpAPI/Google Shopping

### 🔍 Vector Search & RAG

- **1536-dimensional embeddings** using OpenAI's `text-embedding-3-small`
- **MongoDB Atlas Vector Search** with cosine similarity
- **Semantic retrieval** for relevant past conversations
- **Conversation summarization** for long-term memory

### 🎯 Multiple LLM Providers

Provider-agnostic design with factory pattern:

- **OpenAI** - GPT-4, GPT-4 Turbo, GPT-4o, including search preview models
- **Anthropic** - Claude 3 Opus, Sonnet, Haiku
- **Google** - Gemini 2.0, Gemini 1.5
- **OpenRouter** - Access to Perplexity, Grok, and other models

### 💬 Advanced Query Processing

- **Streaming responses** with Server-Sent Events (SSE) # not yet done
- **Shopping mode** with interactive option selection
- **Vision support** for image-based queries
- **Web search integration** via search-preview models
- **Citation extraction** from LLM responses

### 📊 Session Management

- **Event tracking** - Click, scroll, input, and custom events
- **Session analytics** - Duration, query count, engagement metrics
- **Experiment assignment** - A/B testing support
- **Device fingerprinting** - Browser, OS, viewport tracking

### 🔧 Technical Excellence

- **Type-Safe** - Full Pydantic validation for all APIs
- **Async/Await** - High-performance async operations throughout
- **Repository Pattern** - Clean data access layer
- **Service Layer** - Business logic separation from routes
- **Factory Pattern** - Dynamic provider instantiation
- **Dependency Injection** - FastAPI's built-in DI system
- **Comprehensive Logging** - Structured logging with context
- **Error Handling** - Graceful degradation and user-friendly errors

---

## 🏗️ Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────────────┐
│              API Layer (FastAPI)                    │  ← REST endpoints, SSE streaming
├─────────────────────────────────────────────────────┤
│           Agent Orchestration Layer                 │  ← Multi-agent coordination
│  (CoordinatorAgent → Specialized Agents)            │
├─────────────────────────────────────────────────────┤
│              Service Layer                          │  ← Business logic
│  (QueryService, MemoryService, EmbeddingService)    │
├─────────────────────────────────────────────────────┤
│             Repository Layer                        │  ← Data access patterns
│  (QueryRepo, SessionRepo, SummaryRepo)              │
├─────────────────────────────────────────────────────┤
│             Provider Layer                          │  ← LLM integrations
│  (OpenAI, Anthropic, Google, OpenRouter)            │
├─────────────────────────────────────────────────────┤
│         Database (MongoDB Atlas)                    │  ← Persistence + Vector Search
└─────────────────────────────────────────────────────┘
```

### Request Flow

```
User Request
    ↓
FastAPI Endpoint
    ↓
QueryService (orchestration)
    ↓
CoordinatorAgent (routing)
    ↓
├─ MemoryAgent (context retrieval)
├─ ShoppingAgent (if mode=shopping)
├─ VisionAgent (if attachments present)
├─ ProductAgent (if products mentioned)
└─ WriterAgent (response generation)
    ↓
LLM Provider (OpenAI, Anthropic, etc.)
    ↓
Response Processing
    ↓
Database Logging
    ↓
Streaming to Client (SSE)
```

---

## 🚀 Quick Start

### Prerequisites

- **Python** 3.11 or higher
- **MongoDB Atlas** account (or local MongoDB)
- **API Keys** for at least one LLM provider:
  - OpenAI, Anthropic, Google, or OpenRouter
- **Docker & Docker Compose** (optional, for containerization)

### Installation

#### Option 1: Local Development (Recommended)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys and MongoDB URI

# Run the server
uvicorn app.main:app --reload --reload-dir app
```

**Why `--reload-dir app`?** This prevents infinite reload loops by watching only the `app/` directory, excluding `.venv/` and other system files.

#### Option 2: UV Package Manager (Faster)

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create environment and install dependencies
uv sync

# Run server
uv run uvicorn app.main:app --reload --reload-dir app
```

#### Option 3: Docker

```bash
# Ensure Docker Desktop is running

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop
docker-compose down
```

### Verify Installation

Open your browser to:

- **API Documentation (Swagger)**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

You should see:
```json
{
  "status": "healthy",
  "database": {"connected": true},
  "agents": {"initialized": true},
  "providers": {"count": 4}
}
```

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── agents/                 # Multi-agent system (LangGraph)
│   │   ├── __init__.py         # Agent initialization
│   │   ├── base_agent.py       # Abstract base class
│   │   ├── coordinator.py      # Main routing agent
│   │   ├── memory_agent.py     # RAG & conversation memory
│   │   ├── product_agent.py    # Product search & extraction
│   │   ├── shopping_agent.py   # Shopping interview flow
│   │   ├── vision_agent.py     # Image understanding
│   │   ├── writer_agent.py     # Response generation
│   │   └── graph.py            # LangGraph workflow
│   │
│   ├── api/v1/                 # API routes
│   │   ├── __init__.py
│   │   ├── health.py           # Health & status endpoints
│   │   ├── query.py            # Query processing (sync & streaming)
│   │   ├── sessions.py         # Session management
│   │   ├── products.py         # Product search
│   │   ├── files.py            # File upload & management
│   │   └── router.py           # Route aggregator
│   │
│   ├── core/                   # Core configuration
│   │   ├── config.py           # Settings (Pydantic BaseSettings)
│   │   └── events.py           # Startup/shutdown lifecycle
│   │
│   ├── db/                     # Database layer
│   │   ├── mongodb.py          # MongoDB connection & indexes
│   │   └── repositories/       # Data access patterns
│   │       ├── query_repo.py
│   │       ├── session_repo.py
│   │       ├── summary_repo.py
│   │       ├── file_repo.py
│   │       └── product_repo.py
│   │
│   ├── providers/              # LLM provider abstractions
│   │   ├── base.py             # Abstract provider interface
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── google_provider.py
│   │   ├── openrouter_provider.py
│   │   └── factory.py          # Provider factory pattern
│   │
│   ├── schemas/                # Pydantic models
│   │   ├── base.py             # Base schemas & mixins
│   │   ├── query.py            # Query request/response
│   │   ├── session.py          # Session & events
│   │   ├── product.py          # Product schemas
│   │   ├── memory.py           # Memory schemas
│   │   ├── event.py            # Event logging
│   │   └── __init__.py
│   │
│   ├── services/               # Business logic layer
│   │   ├── query_service.py    # Main query orchestration
│   │   ├── memory_service.py   # Memory operations
│   │   ├── embedding_service.py # Vector embeddings
│   │   ├── event_service.py    # Event logging
│   │   ├── file_service.py     # File handling
│   │   ├── session_service.py  # Session management
│   │   └── __init__.py
│   │
│   ├── scripts/                # Utility scripts
│   │   ├── migrate_collections.py  # Database migration
│   │   ├── test_phase1.py     # Phase 1 tests (config & DB)
│   │   ├── test_phase2.py     # Phase 2 tests (schemas)
│   │   ├── test_phase3.py     # Phase 3 tests (providers)
│   │   ├── test_phase4.py     # Phase 4 tests (routes)
│   │   └── test_phase5.py     # Phase 5 tests (services)
│   │
│   ├── utils/                  # Utility functions
│   │   └── vector_search.py    # Vector search helpers
│   │
│   └── main.py                 # FastAPI application entry point
│
├── uploads/                    # User-uploaded files (gitignored)
├── logs/                       # Application logs (gitignored)
├── .env                        # Environment variables (gitignored)
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
├── .watchfilesignore           # Uvicorn watch exclusions
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Docker Compose configuration
├── pyproject.toml              # UV/Poetry configuration
├── requirements.txt            # pip dependencies
├── uv.lock                     # UV lock file
└── README.md                   # This file
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory (copy from `.env.example`):

```bash
# ==================== Application ====================
APP_NAME="LLM Platform"
APP_VERSION="2.0.0"
DEBUG=false
ENVIRONMENT="development"  # development, staging, production

# ==================== Server ====================
HOST="0.0.0.0"
PORT=8000
WORKERS=1

# ==================== Database ====================
MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/"
MONGO_DB="LLMPlatform"

# ==================== LLM API Keys ====================
# At least one provider key is required
OPENAI_API_KEY="sk-proj-..."
ANTHROPIC_API_KEY="sk-ant-..."
GOOGLE_API_KEY="..."
OPENROUTER_API_KEY="..."

# ==================== External Services ====================
SERPAPI_KEY=""  # Optional: For product search via Google Shopping

# ==================== File Upload ====================
UPLOAD_DIR="uploads"
MAX_FILE_SIZE=10485760  # 10MB in bytes

# ==================== CORS ====================
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# ==================== Logging ====================
LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE="app/logs/app.log"

# ==================== Security ====================
SECRET_KEY="your-secret-key-change-this-in-production"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ==================== Agent Configuration ====================
MEMORY_SUMMARY_INTERVAL=4      # Summarize every N message pairs
PRODUCT_SEARCH_MAX_RESULTS=1   # Max products per search

# ==================== Model Defaults ====================
DEFAULT_MODEL_PROVIDER="openai"
DEFAULT_MODEL_NAME="gpt-4o-mini"
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=1024
```

### MongoDB Atlas Setup

1. **Create Cluster**
   - Go to [MongoDB Atlas](https://cloud.mongodb.com/)
   - Create a free M0 cluster

2. **Configure Network Access**
   - Add your IP address to IP Whitelist
   - Or allow access from anywhere (0.0.0.0/0) for development

3. **Create Database User**
   - Create a user with read/write permissions
   - Save credentials for `MONGODB_URI`

4. **Get Connection String**
   ```
   mongodb+srv://<username>:<password>@cluster.mongodb.net/
   ```

5. **Create Vector Search Index** (Critical for RAG)
   - Navigate to: Database → Browse Collections
   - Select database: `LLMPlatform`
   - Select collection: `queries`
   - Go to "Search Indexes" tab
   - Click "Create Search Index" → "Atlas Vector Search"
   - Configuration:
     ```json
     {
       "fields": [
         {
           "type": "vector",
           "path": "embedding",
           "numDimensions": 1536,
           "similarity": "cosine"
         }
       ]
     }
     ```
   - Index name: `vector_index`

---

## 📚 API Documentation

### Core Endpoints

#### 1. Query Processing

**Standard Query (JSON Response)**
```bash
POST /api/v1/query/
Content-Type: application/json

{
  "user_id": "user_123",
  "session_id": "session_456",
  "query": "Recommend noise-cancelling headphones under $200",
  "model_provider": "openai",
  "model_name": "gpt-4o-mini",
  "mode": "shopping",
  "web_search": true,
  "use_memory": true
}
```

**Streaming Query (SSE)**
```bash
POST /api/v1/query/stream
Content-Type: application/json

# Returns Server-Sent Events:
# data: {"type": "chunk", "content": "Here are some great options..."}
# data: {"type": "node", "node": "WriterAgent"}
# data: {"type": "final", "options": [...], "metadata": {...}}
# data: {"type": "done", "message": "Query complete"}
```

#### 2. Session Management

```bash
# Start Session
POST /api/v1/session/start
{
  "session_id": "sess_abc",
  "user_id": "user_123",
  "environment": {
    "device": "Desktop",
    "browser": "Chrome 120",
    "os": "macOS",
    "viewport": {"width": 1920, "height": 1080}
  }
}

# Log Event
POST /api/v1/session/event
{
  "session_id": "sess_abc",
  "event": {
    "t": 1703001234567,
    "type": "click",
    "data": {"element": "submit_button"}
  }
}

# Get Session
GET /api/v1/session/{session_id}?include_events=true

# End Session
POST /api/v1/session/end
{
  "session_id": "sess_abc"
}
```

#### 3. File Upload

```bash
# Upload File
POST /api/v1/files/upload
Content-Type: multipart/form-data

file: <file_data>
user_id: user_123

# List User Files
GET /api/v1/files/?user_id=user_123

# Delete File
DELETE /api/v1/files/{file_id}
```

#### 4. Health & Status

```bash
# Health Check
GET /api/v1/health

# Detailed Status
GET /api/v1/status
```

### Interactive API Documentation

Once the server is running, access:

- **Swagger UI**: http://localhost:8000/docs
  - Interactive API testing
  - Request/response examples
  - Schema documentation

- **ReDoc**: http://localhost:8000/redoc
  - Alternative documentation UI
  - Better for reading

- **OpenAPI JSON**: http://localhost:8000/openapi.json
  - Raw OpenAPI specification
  - For client generation

---

## 🛠️ Development

### Running the Server

```bash
# Development mode with auto-reload (recommended)
source .venv/bin/activate
uvicorn app.main:app --reload --reload-dir app

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# With custom port
uvicorn app.main:app --reload --reload-dir app --port 8080
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/unit/test_query_service.py

# Run with verbose output
pytest -v

# Run only unit tests
pytest app/tests/unit/

# Run integration tests
pytest app/tests/integration/
```

### Code Quality

```bash
# Format code
black app/

# Lint
flake8 app/

# Type checking
mypy app/

# Sort imports
isort app/
```

### Database Migrations

```bash
# Run collection migration
python -m app.scripts.migrate_collections

# Test Phase 1 (Config & DB)
python -m app.scripts.test_phase1

# Test Phase 2 (Schemas)
python -m app.scripts.test_phase2

# Test Phase 3 (Providers)
python -m app.scripts.test_phase3

# Test Phase 4 (Routes)
python -m app.scripts.test_phase4

# Test Phase 5 (Services)
python -m app.scripts.test_phase5
```

---

## 🐳 Deployment

### Docker Production Build

```bash
# Build image
docker-compose build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# Scale horizontally (requires load balancer)
docker-compose up -d --scale backend=3
```

### Environment-Specific Deployments

```bash
# Staging
docker-compose -f docker-compose.staging.yml up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### Health Monitoring

```bash
# Health endpoint
curl http://localhost:8000/api/v1/health

# Expected response:
{
  "status": "healthy",
  "database": {"connected": true, "collections": 5},
  "agents": {"initialized": true},
  "providers": {"count": 4, "available": ["openai", "anthropic", "google", "openrouter"]}
}

# Status endpoint (more detailed)
curl http://localhost:8000/api/v1/status
```

### Production Checklist

- [ ] Set `DEBUG=false` in `.env`
- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure production `MONGODB_URI`
- [ ] Set appropriate `CORS_ORIGINS`
- [ ] Configure logging level (`LOG_LEVEL=INFO`)
- [ ] Set up MongoDB Atlas vector index
- [ ] Configure rate limiting (if needed)
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy for uploads
- [ ] Use environment-specific API keys
- [ ] Enable HTTPS/SSL

---

## 🧪 Testing

### Test Structure

```
app/tests/
├── unit/                    # Unit tests (isolated)
│   ├── test_query_service.py
│   ├── test_memory_agent.py
│   ├── test_providers.py
│   └── ...
├── integration/             # Integration tests
│   ├── test_api_endpoints.py
│   ├── test_database.py
│   └── ...
├── e2e/                     # End-to-end tests
│   └── test_full_flow.py
└── conftest.py              # Pytest fixtures
```

### Running Tests

```bash
# All tests
pytest

# Specific category
pytest app/tests/unit/
pytest app/tests/integration/
pytest app/tests/e2e/

# With coverage report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html to view

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run tests matching pattern
pytest -k "test_query"

# Parallel execution (requires pytest-xdist)
pytest -n auto
```

### Test Coverage Goals

- Unit tests: >80% coverage
- Integration tests: Critical paths covered
- E2E tests: Main user flows validated

---

## 📊 Database Schema

### Collections Overview

| Collection | Purpose | Indexed Fields | Vector Search |
|------------|---------|----------------|---------------|
| `queries` | User queries with responses and embeddings | `user_id`, `session_id`, `timestamp` | ✅ Yes (`embedding` field) |
| `sessions` | User sessions with events | `user_id`, `session_id`, `start_t` | ❌ No |
| `summaries` | Conversation summaries | `user_id`, `session_id`, `created_at` | ❌ No |
| `products` | Product catalog cache | `search_query`, `created_at` | ❌ No |
| `files` | Uploaded file metadata | `user_id`, `uploaded_at` | ❌ No |

### Query Document Structure

```json
{
  "_id": "ObjectId",
  "user_id": "user_123",
  "session_id": "session_456",
  "query": "What are the best headphones?",
  "response": "Here are some excellent options...",
  "embedding": [0.123, 0.456, ...],  // 1536 dimensions
  "citations": [
    {"title": "Review Site", "url": "https://..."}
  ],
  "product_cards": [
    {"title": "Sony WH-1000XM5", "price": "$399", "url": "https://..."}
  ],
  "intent": "shopping",
  "model_provider": "openai",
  "model_name": "gpt-4o-mini",
  "timestamp": "ISODate(...)",
  "agents_used": ["MemoryAgent", "ShoppingAgent", "WriterAgent"],
  "metadata": {...}
}
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Server Won't Start - Address Already in Use

**Problem**: `ERROR: [Errno 48] Address already in use`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
uvicorn app.main:app --reload --reload-dir app --port 8080
```

#### 2. Infinite Reload Loop

**Problem**: Server constantly reloading with warnings about `.venv/` files

**Solution**:
```bash
# Use --reload-dir flag to watch only app/ directory
uvicorn app.main:app --reload --reload-dir app
```

#### 3. MongoDB Connection Failed

**Problem**: `Unable to connect to MongoDB`

**Solutions**:
```bash
# Verify connection string in .env
MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/"

# Check IP whitelist in MongoDB Atlas
# - Go to Network Access
# - Add your current IP or 0.0.0.0/0

# Test connection
python -c "from app.db.mongodb import connect_db; import asyncio; asyncio.run(connect_db())"
```

#### 4. Vector Search Not Working

**Problem**: RAG/memory retrieval not finding related queries

**Solution**:
- Ensure vector search index is created in MongoDB Atlas
- Collection: `queries`
- Index name: `vector_index`
- Field: `embedding`
- Dimensions: 1536
- Similarity: cosine

```bash
# Run migration script to help set up
python -m app.scripts.migrate_collections
```

#### 5. API Key Errors

**Problem**: `API key not configured` or `401 Unauthorized`

**Solutions**:
```bash
# Verify .env is loaded
python -c "from app.core.config import settings; print('OpenAI:', settings.OPENAI_API_KEY[:10])"

# Check .env location
ls -la .env

# Ensure .env is in backend/ directory
# Not in parent directory or nested folders
```

#### 6. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'app'`

**Solution**:
```bash
# Ensure you're in the backend/ directory
cd backend

# Activate virtual environment
source .venv/bin/activate

# Verify Python path
python -c "import sys; print('\n'.join(sys.path))"
```

#### 7. Docker Issues

**Problem**: `Cannot connect to the Docker daemon`

**Solution**:
```bash
# Start Docker Desktop
open -a Docker  # macOS

# Verify Docker is running
docker ps

# Remove obsolete 'version' from docker-compose.yml
# (Already fixed in latest version)
```

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Getting Started

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/yourusername/LLMPlatform.git
   cd LLMPlatform/backend
   ```
3. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
4. **Make your changes**
5. **Run tests**
   ```bash
   pytest
   black app/
   flake8 app/
   ```
6. **Commit with meaningful message**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
7. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```
8. **Open a Pull Request**

### Code Standards

- **Follow PEP 8** - Python style guide
- **Use type hints** - For all function signatures
- **Write docstrings** - Google style preferred
- **Add tests** - For new features and bug fixes
- **Update docs** - Keep README and docstrings current
- **Atomic commits** - One logical change per commit
- **Descriptive commit messages** - Use conventional commits format

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: feat, fix, docs, style, refactor, test, chore

**Examples**:
```
feat(agents): add new retrieval agent for RAG
fix(query): resolve streaming timeout issue
docs(readme): update installation instructions
```

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 LLM Platform Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

This project wouldn't be possible without these excellent tools and services:

- **[FastAPI](https://fastapi.tiangolo.com/)** - High-performance async web framework
- **[MongoDB Atlas](https://www.mongodb.com/atlas)** - Vector search and database
- **[LangGraph](https://github.com/langchain-ai/langgraph)** - Agent orchestration framework
- **[OpenAI](https://openai.com/)** - GPT models and embeddings
- **[Anthropic](https://www.anthropic.com/)** - Claude models
- **[Google](https://ai.google.dev/)** - Gemini models
- **[Pydantic](https://docs.pydantic.dev/)** - Data validation
- **[Uvicorn](https://www.uvicorn.org/)** - ASGI server

---

## 📞 Support

- **Documentation**: [API Docs](http://localhost:8000/docs)
- **Issues**: [GitHub Issues](https://github.com/yourusername/LLMPlatform/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/LLMPlatform/discussions)

---

## 🗺️ Roadmap

- [ ] WebSocket support for bidirectional streaming
- [ ] Redis caching layer for improved performance
- [ ] Rate limiting and quota management
- [ ] Multi-tenancy support
- [ ] Advanced analytics dashboard
- [ ] Plugin system for custom agents
- [ ] Kubernetes deployment configs
- [ ] GraphQL API alternative
- [ ] Real-time collaboration features
- [ ] Enhanced security (OAuth, JWT)

---

**Built with ❤️ by the LLM Platform team**
