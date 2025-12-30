# LLM Platform - Intelligent Multi-Agent AI System 🤖

[![Live Demo](https://img.shields.io/badge/demo-live-success)](https://llm-platform.vercel.app/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 🌐 **[View Live Website](https://llm-platform.vercel.app/)**

A production-grade, full-stack AI platform featuring multi-agent orchestration, vector search, and intelligent query processing. Built with FastAPI, Next.js, and MongoDB Atlas.

---

## ✨ Highlights

- 🤖 **Multi-Agent System** - LangGraph-based intelligent agent coordination
- 🔍 **Vector Search** - MongoDB Atlas RAG with 1536-dim embeddings
- 💬 **Real-time Streaming** - Server-Sent Events (SSE) for live responses
- 🎯 **Multi-Provider** - OpenAI, Anthropic, Google, OpenRouter support
- 🛍️ **Shopping Mode** - Interactive product discovery with AI-guided interviews
- 📊 **Session Analytics** - Comprehensive user behavior tracking
- 🎨 **Vision AI** - Image understanding and analysis
- ⚡ **Production-Ready** - Docker, monitoring, comprehensive logging

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│         Next.js Frontend (Vercel)               │
│         - React 18 + TypeScript                 │
│         - Tailwind CSS + shadcn/ui              │
│         - Real-time SSE streaming               │
└────────────────┬────────────────────────────────┘
                 │ HTTPS/JSON
┌────────────────▼────────────────────────────────┐
│      FastAPI Backend (Railway/Docker)           │
│      - Multi-agent orchestration                │
│      - Vector embeddings + RAG                  │
│      - Provider abstraction layer               │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│         MongoDB Atlas (Cloud)                   │
│         - Query storage + embeddings            │
│         - Session tracking                      │
│         - Vector search index                   │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Backend**: Python 3.11+, MongoDB Atlas account
- **Frontend**: Node.js 18+, npm/pnpm
- **APIs**: At least one LLM provider API key

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your MongoDB URI and API keys

# Run server (with auto-reload fix)
uvicorn app.main:app --reload --reload-dir app
```

**Backend runs at:** http://localhost:8000  
**API Docs:** http://localhost:8000/docs

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with backend URL

# Run development server
npm run dev
```

**Frontend runs at:** http://localhost:3000

---

## 📁 Project Structure

```
LLMPlatform/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── agents/            # Multi-agent system (LangGraph)
│   │   │   ├── coordinator.py # Main routing agent
│   │   │   ├── memory_agent.py # RAG & context retrieval
│   │   │   ├── shopping_agent.py # Product discovery
│   │   │   ├── writer_agent.py # Response generation
│   │   │   └── vision_agent.py # Image analysis
│   │   ├── api/v1/            # REST endpoints
│   │   ├── providers/         # LLM provider abstractions
│   │   ├── services/          # Business logic
│   │   ├── db/                # MongoDB repositories
│   │   ├── schemas/           # Pydantic models
│   │   └── main.py           # FastAPI app
│   ├── .env.example
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md             # Backend documentation
│
├── frontend/                  # Next.js application
│   ├── app/                  # Next.js 15 App Router
│   ├── components/           # React components
│   ├── hooks/                # Custom React hooks
│   ├── lib/                  # Utilities & API client
│   ├── .env.example
│   ├── package.json
│   └── README.md            # Frontend documentation
│
└── README.md                # This file
```

---

## 🎯 Key Features

### 1. Multi-Agent Orchestration

Built on **LangGraph**, our intelligent agent system provides:

- **CoordinatorAgent** - Routes requests to specialized agents
- **MemoryAgent** - RAG-based context retrieval with vector search
- **ShoppingAgent** - 3-round interactive product interview
- **WriterAgent** - Provider-specific response generation
- **VisionAgent** - Image understanding with vision-capable models
- **ProductAgent** - Real-time product search via Google Shopping

### 2. Vector Search & RAG

- **OpenAI Embeddings** - `text-embedding-3-small` (1536 dimensions)
- **MongoDB Atlas Vector Search** - Cosine similarity indexing
- **Semantic Retrieval** - Find related past conversations
- **Conversation Summaries** - Long-term memory compression

### 3. Multi-Provider Support

Provider-agnostic design supports:

- ✅ **OpenAI** - GPT-4, GPT-4 Turbo, GPT-4o, search preview
- ✅ **Anthropic** - Claude 3 Opus, Sonnet, Haiku
- ✅ **Google** - Gemini 2.0, Gemini 1.5
- ✅ **OpenRouter** - Perplexity, Grok, and more

### 4. Advanced Features

- **Streaming Responses** - Real-time SSE for live updates
- **Shopping Mode** - Interactive option selection
- **Vision Support** - Image-based queries
- **Session Tracking** - Comprehensive user analytics
- **Citation Extraction** - Automatic source attribution
- **File Upload** - Document processing support

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** - High-performance async web framework
- **LangGraph** - Agent orchestration and workflows
- **MongoDB** - Database with Atlas Vector Search
- **Pydantic** - Data validation and settings
- **Motor** - Async MongoDB driver
- **Uvicorn** - ASGI server

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - High-quality React components
- **Zustand** - State management
- **React Query** - Data fetching

### Infrastructure
- **Docker** - Containerization
- **MongoDB Atlas** - Cloud database + vector search
- **Vercel** - Frontend deployment
- **Railway/Render** - Backend hosting

---

## 📚 API Endpoints

### Query Processing

**Standard Query**
```bash
POST /api/v1/query/
{
  "user_id": "user_123",
  "session_id": "session_456",
  "query": "Recommend noise-cancelling headphones under $200",
  "model_provider": "openai",
  "model_name": "gpt-4o-mini",
  "mode": "shopping"
}
```

**Streaming Query (SSE)**
```bash
POST /api/v1/query/stream
# Returns:
# data: {"type": "chunk", "content": "..."}
# data: {"type": "final", "options": [...]}
# data: {"type": "done"}
```

### Session Management

```bash
POST /api/v1/session/start      # Start session
POST /api/v1/session/event      # Log event
GET  /api/v1/session/{id}       # Get session data
POST /api/v1/session/end        # End session
```

### Other Endpoints

```bash
POST /api/v1/files/upload       # Upload file
GET  /api/v1/files/             # List files
POST /api/v1/products/search    # Search products
GET  /api/v1/health             # Health check
```

**Interactive Docs:** http://localhost:8000/docs

---

## 🚢 Deployment

### Deploy Backend to Railway

1. Push to GitHub
2. Create new project on [Railway](https://railway.app)
3. Connect repository
4. Set root directory: `backend`
5. Add environment variables from `.env.example`
6. Deploy!

### Deploy Frontend to Vercel

1. Push to GitHub
2. Import on [Vercel](https://vercel.com)
3. Set root directory: `frontend`
4. Add `NEXT_PUBLIC_BACKEND_URL` environment variable
5. Deploy!

### Docker Deployment

```bash
# Backend
cd backend
docker-compose up -d

# View logs
docker-compose logs -f backend
```

---

## 🗄️ Database Setup

### MongoDB Atlas

1. Create free cluster at [MongoDB Atlas](https://cloud.mongodb.com)
2. Create database: `LLMPlatform`
3. **Create vector search index:**
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

### Collections

| Collection | Purpose | Vector Search |
|------------|---------|---------------|
| `queries` | Q&A with embeddings | ✅ Yes |
| `sessions` | User sessions & events | ❌ No |
| `summaries` | Conversation summaries | ❌ No |
| `products` | Product catalog | ❌ No |
| `files` | File metadata | ❌ No |

---

## 🔧 Configuration

### Backend (.env)

```bash
# Database
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGO_DB=LLMPlatform

# LLM Providers (at least one required)
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
OPENROUTER_API_KEY=...

# Optional
SERPAPI_KEY=...  # For product search

# CORS
CORS_ORIGINS=["http://localhost:3000", "https://yourapp.com"]
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
# Production: https://your-backend.railway.app
```

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Test specific phase
python -m app.scripts.test_phase1  # Config & DB
python -m app.scripts.test_phase2  # Schemas
python -m app.scripts.test_phase3  # Providers
python -m app.scripts.test_phase4  # Routes
python -m app.scripts.test_phase5  # Services
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# With coverage
npm run test:coverage
```

---

## 🔍 Troubleshooting

### Backend Issues

**Infinite Reload Loop**
```bash
# Use --reload-dir flag
uvicorn app.main:app --reload --reload-dir app
```

**MongoDB Connection Failed**
- Verify `MONGODB_URI` in `.env`
- Check IP whitelist in MongoDB Atlas
- Confirm database user permissions

**Vector Search Not Working**
- Ensure vector index is created (see Database Setup)
- Index name must be `vector_index`
- Field must be `embedding` with 1536 dimensions

### Frontend Issues

**Cannot Connect to Backend**
- Verify `NEXT_PUBLIC_BACKEND_URL` is set
- Check backend is running on correct port
- Verify CORS settings in backend

**Events Not Logging**
- Check browser console for errors
- Verify session is initialized
- Check network tab for failed requests

---

## 📊 Event Tracking

The platform tracks comprehensive user interactions:

| Event Type | Description | Triggered When |
|------------|-------------|----------------|
| `click` | Link clicks | User clicks any URL |
| `scroll` | Scrolling behavior | User scrolls (debounced) |
| `browse` | Page views | User views results |
| `query` | Queries submitted | User sends message |
| `option_select` | Shopping selections | User picks option |

---

## 🗺️ Roadmap

### In Progress
- [ ] WebSocket support for bidirectional streaming
- [ ] Advanced analytics dashboard
- [ ] Multi-tenancy support

### Planned
- [ ] Redis caching layer
- [ ] Rate limiting & quota management
- [ ] Plugin system for custom agents
- [ ] Kubernetes deployment configs
- [ ] GraphQL API alternative
- [ ] Real-time collaboration
- [ ] Enhanced security (OAuth, JWT)

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Amazing async web framework
- [Next.js](https://nextjs.org/) - The React framework for production
- [MongoDB Atlas](https://www.mongodb.com/atlas) - Vector search capabilities
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent orchestration
- [shadcn/ui](https://ui.shadcn.com/) - Beautiful React components
- [Vercel](https://vercel.com/) - Seamless frontend deployment

