# LLM Platform Backend

A production-ready, modular FastAPI backend for multi-LLM interactions with vector search, multi-agent orchestration, and comprehensive query processing.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-brightgreen.svg)](https://www.mongodb.com/atlas)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [API Documentation](#-api-documentation)
- [Development](#-development)
- [Deployment](#-deployment)
- [Testing](#-testing)
- [Contributing](#-contributing)

---

## ✨ Features

### Core Capabilities
- 🤖 **Multi-Agent System** - Coordinated agents for memory, shopping, writing, and vision
- 🔍 **Vector Search** - MongoDB Atlas vector search with 1536-dim embeddings
- 💬 **Streaming Responses** - Server-Sent Events (SSE) for real-time LLM output
- 🎯 **Multiple LLM Providers** - OpenAI, Anthropic, Google, OpenRouter support
- 📊 **Session Management** - Complete user session tracking and analytics
- 📁 **File Upload** - Support for document processing and RAG

### Technical Features
- ✅ **Type-Safe** - Full Pydantic validation
- ✅ **Async/Await** - High-performance async operations
- ✅ **Repository Pattern** - Clean data access layer
- ✅ **Service Layer** - Business logic separation
- ✅ **Factory Pattern** - Dynamic provider instantiation
- ✅ **Docker Ready** - Production containerization
- ✅ **Modular Architecture** - 50+ organized files

---

## 🏗️ Architecture

### Layered Architecture

```
┌─────────────────────────────────────┐
│         API Layer (FastAPI)         │  ← HTTP endpoints
├─────────────────────────────────────┤
│        Service Layer                │  ← Business logic
├─────────────────────────────────────┤
│       Repository Layer              │  ← Data access
├─────────────────────────────────────┤
│      Database (MongoDB)             │  ← Persistence
└─────────────────────────────────────┘
```

### Key Components

- **API Routes** - RESTful endpoints with FastAPI
- **Services** - Business logic (QueryService, MemoryService, etc.)
- **Repositories** - MongoDB data access patterns
- **Agents** - Multi-agent orchestration system
- **Providers** - LLM provider abstractions
- **Schemas** - Pydantic models for validation

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- MongoDB Atlas account (or local MongoDB)
- OpenAI API key (minimum)
- Docker & Docker Compose (optional)

### Installation

#### Option 1: Local Development

```bash
# Clone the repository
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and MongoDB URI

# Run the server
uvicorn app.main:app --reload
```

#### Option 2: Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop
docker-compose down
```

### Verify Installation

Open your browser to:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health
- **OpenAPI**: http://localhost:8000/openapi.json

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── agents/              # Multi-agent system
│   │   ├── base_agent.py
│   │   ├── coordinator.py   # Agent coordinator
│   │   ├── memory_agent.py  # Memory & RAG
│   │   ├── product_agent.py # Product search
│   │   ├── shopping_agent.py
│   │   ├── vision_agent.py
│   │   └── writer_agent.py
│   │
│   ├── api/v1/             # API routes
│   │   ├── health.py       # Health endpoints
│   │   ├── query.py        # Main query processing
│   │   ├── events.py       # Event logging
│   │   ├── sessions.py     # Session management
│   │   ├── products.py     # Product search
│   │   ├── files.py        # File uploads
│   │   └── router.py       # Route aggregator
│   │
│   ├── core/               # Core configuration
│   │   ├── config.py       # Settings management
│   │   └── events.py       # Startup/shutdown
│   │
│   ├── db/                 # Database layer
│   │   ├── mongodb.py      # MongoDB connection
│   │   └── repositories/   # Data access
│   │       ├── query_repo.py
│   │       ├── session_repo.py
│   │       ├── summary_repo.py
│   │       └── ...
│   │
│   ├── providers/          # LLM providers
│   │   ├── openai.py
│   │   ├── anthropic.py
│   │   ├── google.py
│   │   ├── openrouter.py
│   │   └── factory.py
│   │
│   ├── schemas/            # Pydantic models
│   │   ├── query.py
│   │   ├── session.py
│   │   ├── product.py
│   │   └── base.py
│   │
│   ├── services/           # Business logic
│   │   ├── query_service.py     # Main orchestrator
│   │   ├── memory_service.py    # Memory retrieval
│   │   ├── embedding_service.py # Vector embeddings
│   │   ├── file_service.py
│   │   └── session_service.py
│   │
│   ├── tests/              # Test suite
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   │
│   ├── utils/              # Utilities
│   │   └── vector_search.py
│   │
│   └── main.py             # Application entry point
│
├── uploads/                # Uploaded files
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
└── docker-compose.yml     # Docker Compose setup
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Application
APP_NAME="LLM Platform"
APP_VERSION="2.0.0"
DEBUG=false
ENVIRONMENT="production"

# Server
HOST="0.0.0.0"
PORT=8000

# Database
MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net/"
MONGO_DB="LLMPlatform"

# LLM API Keys (at least one required)
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."
GOOGLE_API_KEY="..."
OPENROUTER_API_KEY="..."

# External Services (optional)
SERPAPI_KEY="..."  # For product search

# CORS
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]

# Logging
LOG_LEVEL="INFO"
```

### MongoDB Atlas Setup

1. Create a MongoDB Atlas cluster
2. Create database: `LLMPlatform`
3. **Important**: Create vector search index:
   - Collection: `queries`
   - Index name: `vector_index`
   - Configuration:
     ```json
     {
       "fields": [{
         "type": "vector",
         "path": "embedding",
         "numDimensions": 1536,
         "similarity": "cosine"
       }]
     }
     ```

See `DATABASE_OPTIMIZATION.md` for detailed instructions.

---

## 📚 API Documentation

### Main Endpoints

#### Query Processing
```bash
# Standard query
POST /api/v1/query/
Content-Type: application/json

{
  "user_id": "user123",
  "session_id": "sess456",
  "query": "How do I reset my password?",
  "model_provider": "openai",
  "model_name": "gpt-4o-mini"
}

# Streaming query
POST /api/v1/query/stream
# Returns Server-Sent Events (SSE)
```

#### Session Management
```bash
# Start session
POST /api/v1/session/start

# Add event
POST /api/v1/session/event

# Get session
GET /api/v1/session/{session_id}
```

#### File Upload
```bash
# Upload file
POST /api/v1/files/upload
Content-Type: multipart/form-data

# List files
GET /api/v1/files/?user_id=user123
```

### Interactive API Docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🛠️ Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/unit/test_query_service.py
```

### Code Quality

```bash
# Format code
black app/

# Lint
flake8 app/

# Type checking
mypy app/
```

### Database Migrations

```bash
# Run migration script
python -m app.scripts.migrate_collections
```

---

## 🐳 Deployment

### Docker Production Build

```bash
# Build
docker-compose build

# Run in detached mode
docker-compose up -d

# Scale (if needed)
docker-compose up -d --scale backend=3

# View logs
docker-compose logs -f backend

# Stop
docker-compose down
```

### Environment-Specific Deployment

```bash
# Staging
docker-compose -f docker-compose.staging.yml up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### Health Monitoring

```bash
# Check health
curl http://localhost:8000/api/v1/health

# Check status
curl http://localhost:8000/api/v1/status
```

---

## 🧪 Testing

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── e2e/           # End-to-end tests
└── conftest.py    # Pytest fixtures
```

### Running Tests

```bash
# All tests
pytest

# Specific category
pytest app/tests/unit/
pytest app/tests/integration/

# With coverage
pytest --cov=app --cov-report=term-missing

# Verbose
pytest -v
```

---

## 📊 Database Collections

| Collection | Purpose | Vector Search |
|------------|---------|---------------|
| `queries` | Q&A with embeddings | ✅ Yes |
| `sessions` | User sessions & events | ❌ No |
| `summaries` | Conversation summaries | ❌ No |
| `products` | Product catalog | ❌ No |
| `files` | File metadata | ❌ No |

---

## 🔧 Troubleshooting

### Common Issues

**MongoDB Connection Failed**
```bash
# Check connection string in .env
MONGODB_URI="mongodb+srv://..."

# Verify IP whitelist in MongoDB Atlas
```

**API Key Errors**
```bash
# Verify .env file is loaded
python -c "from app.core.config import settings; print(settings.OPENAI_API_KEY[:10])"

# Check load_dotenv() in config.py
```

**Vector Search Not Working**
```bash
# Ensure vector index is created in MongoDB Atlas
# Collection: queries
# Index name: vector_index
# Dimensions: 1536
```

---

## 📈 Performance

- **Async Operations**: All I/O operations are async
- **Connection Pooling**: MongoDB connection pool
- **Lazy Loading**: Providers initialized on demand
- **Streaming**: SSE for large responses
- **Caching**: Response caching (optional)

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Standards

- Follow PEP 8
- Use type hints
- Write docstrings
- Add tests for new features
- Update documentation

---

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- MongoDB for vector search capabilities
- OpenAI, Anthropic, Google for LLM APIs
- LangGraph for agent orchestration
