# Backend Architecture Suggestions - Production-Grade Refactoring

**Project**: LLM Platform (FastAPI + MongoDB)  
**Analysis Date**: 2025-12-28  
**Current Version**: 2.0.0

---

## Table of Contents
1. [Current Architecture Analysis](#current-architecture-analysis)
2. [Proposed Production-Grade Structure](#proposed-production-grade-structure)
3. [Feature Upgrades](#feature-upgrades)
4. [Migration Plan](#migration-plan)
5. [Best Practices Recommendations](#best-practices-recommendations)

---

## 1. Current Architecture Analysis

### Current Structure
```
fastapi-llm-logger/
├── main.py                    # ⚠️ 1814 lines - TOO LARGE
├── database.py                # 22 lines - minimal
├── requirements.txt
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── coordinator.py
│   ├── graph.py
│   ├── memory_agent.py
│   ├── product_agent.py
│   ├── shopping_agent.py
│   ├── vision_agent.py
│   └── writer_agent.py
├── utils/
│   ├── __init__.py
│   ├── embeddings.py
│   ├── intent_classifier.py
│   └── intent_keywords.json
├── config/
│   └── provider_prompts.json
├── uploads/
├── cache/
└── scripts/
```

### Issues Identified

#### 1. **Monolithic main.py (1814 lines)**
- Contains all API routes, LLM provider functions, schemas, initialization logic
- Violates Single Responsibility Principle
- Hard to test, maintain, and scale
- Too many concerns in one file

#### 2. **Missing Core Directories**
- ❌ No `/api` folder for route organization
- ❌ No `/models` or `/schemas` folder for Pydantic models
- ❌ No `/services` folder for business logic
- ❌ No `/middleware` folder for custom middleware
- ❌ No `/core` folder for configuration and dependencies
- ❌ No `/tests` folder for unit/integration tests

#### 3. **Configuration Issues**
- Environment variables scattered
- No centralized config management
- No settings validation using Pydantic BaseSettings

#### 4. **Database Layer**
- Too simple (only 22 lines)
- No repository pattern
- No data access abstraction
- Direct collection access throughout codebase

#### 5. **LLM Provider Logic**
- Hardcoded in main.py
- No abstraction or factory pattern
- Difficult to add new providers
- No streaming support architecture

#### 6. **No Observability**
- Basic logging only
- No structured logging
- No metrics/monitoring
- No tracing for debugging

---

## 2. Proposed Production-Grade Structure

### Recommended Directory Structure

```
fastapi-llm-logger/
│
├── app/                                # Main application package
│   ├── __init__.py
│   │
│   ├── main.py                        # FastAPI app initialization (< 100 lines)
│   │
│   ├── api/                           # API layer - All routes
│   │   ├── __init__.py
│   │   ├── deps.py                    # Route dependencies
│   │   └── v1/                        # API versioning
│   │       ├── __init__.py
│   │       ├── router.py              # Main router aggregator
│   │       ├── query.py               # /query endpoints
│   │       ├── sessions.py            # /session endpoints
│   │       ├── events.py              # /log_event endpoints
│   │       ├── products.py            # /search/products endpoints
│   │       ├── memories.py            # /memories CRUD endpoints
│   │       ├── files.py               # /files upload endpoints
│   │       └── health.py              # /status, /health
│   │
│   ├── core/                          # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py                  # Pydantic Settings management
│   │   ├── security.py                # Auth, CORS, rate limiting
│   │   ├── logging.py                 # Structured logging setup
│   │   └── events.py                  # Startup/shutdown events
│   │
│   ├── models/                        # Database models (if using ORM)
│   │   ├── __init__.py
│   │   ├── query.py
│   │   ├── session.py
│   │   ├── memory.py
│   │   └── product.py
│   │
│   ├── schemas/                       # Pydantic schemas (Request/Response)
│   │   ├── __init__.py
│   │   ├── base.py                    # Base schemas
│   │   ├── query.py                   # QueryRequest, QueryResponse
│   │   ├── session.py                 # SessionStartRequest, etc.
│   │   ├── event.py                   # Event schemas
│   │   ├── memory.py                  # Memory CRUD schemas
│   │   └── product.py                 # Product schemas
│   │
│   ├── services/                      # Business logic layer
│   │   ├── __init__.py
│   │   ├── query_service.py           # Query processing logic
│   │   ├── session_service.py         # Session management
│   │   ├── event_service.py           # Event logging
│   │   ├── memory_service.py          # Memory operations
│   │   └── file_service.py            # File upload/processing
│   │
│   ├── providers/                     # LLM provider integrations
│   │   ├── __init__.py
│   │   ├── base.py                    # Base provider interface
│   │   ├── factory.py                 # Provider factory
│   │   ├── openai_provider.py         # OpenAI integration
│   │   ├── anthropic_provider.py      # Anthropic integration
│   │   ├── google_provider.py         # Google integration
│   │   ├── openrouter_provider.py     # OpenRouter integration
│   │   └── streaming/                 # Streaming implementations
│   │       ├── __init__.py
│   │       ├── sse_streamer.py        # Server-Sent Events
│   │       └── websocket_streamer.py  # WebSocket support
│   │
│   ├── agents/                        # Multi-agent system (keep existing)
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── coordinator.py
│   │   ├── graph.py
│   │   ├── memory_agent.py
│   │   ├── product_agent.py
│   │   ├── shopping_agent.py
│   │   ├── vision_agent.py
│   │   └── writer_agent.py
│   │
│   ├── db/                            # Database layer
│   │   ├── __init__.py
│   │   ├── mongodb.py                 # MongoDB client & connection
│   │   ├── repositories/              # Repository pattern
│   │   │   ├── __init__.py
│   │   │   ├── base.py                # Base repository
│   │   │   ├── query_repo.py
│   │   │   ├── session_repo.py
│   │   │   ├── event_repo.py
│   │   │   ├── memory_repo.py
│   │   │   └── product_repo.py
│   │   └── migrations/                # DB migration scripts
│   │       └── __init__.py
│   │
│   ├── middleware/                    # Custom middleware
│   │   ├── __init__.py
│   │   ├── request_id.py              # Request ID tracking
│   │   ├── timing.py                  # Request timing
│   │   ├── error_handler.py           # Global error handling
│   │   └── rate_limit.py              # Rate limiting
│   │
│   ├── utils/                         # Utilities (keep existing + add more)
│   │   ├── __init__.py
│   │   ├── embeddings.py
│   │   ├── intent_classifier.py
│   │   ├── validators.py              # Input validation helpers
│   │   ├── formatters.py              # Response formatting
│   │   └── helpers.py                 # General helpers
│   │
│   └── exceptions/                    # Custom exceptions
│       ├── __init__.py
│       ├── base.py                    # Base exception classes
│       └── handlers.py                # Exception handlers
│
├── tests/                             # Test suite
│   ├── __init__.py
│   ├── conftest.py                    # Pytest fixtures
│   ├── unit/                          # Unit tests
│   │   ├── test_services/
│   │   ├── test_providers/
│   │   └── test_agents/
│   ├── integration/                   # Integration tests
│   │   ├── test_api/
│   │   └── test_db/
│   └── e2e/                          # End-to-end tests
│
├── scripts/                           # Utility scripts
│   ├── init_db.py                     # Database initialization
│   ├── seed_data.py                   # Seed test data
│   └── migrate.py                     # Migration runner
│
├── alembic/                           # DB migrations (if using SQL later)
│   └── versions/
│
├── config/                            # Configuration files
│   ├── provider_prompts.json
│   └── intent_keywords.json
│
├── uploads/                           # File uploads (keep)
├── cache/                             # Cache directory (keep)
├── logs/                              # Log files (add)
│
├── .env.example
├── .env
├── .gitignore
├── requirements.txt
├── requirements-dev.txt               # Development dependencies
├── pyproject.toml                     # Modern Python project config
├── pytest.ini                         # Pytest configuration
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 3. Feature Upgrades

### 3.1 Display Chain of Thought for Available Models

**Problem**: Currently no support for displaying reasoning steps (chain of thought) from models that support it.

**Solution**: Implement structured thought streaming

#### Implementation Strategy

**① Identify Models with CoT Support**
- OpenAI: `o1-preview`, `o1-mini` (reasoning tokens)
- Anthropic: Extended thinking mode (some models)
- DeepSeek: `deepseek-reasoner` (思维链)
- Google: Gemini models with extended output

**② Create Thought Extractor Service**

```python
# app/services/thought_extractor.py

class ThoughtExtractor:
    """Extract and format chain-of-thought from different providers"""
    
    async def extract_thoughts(
        self, 
        response: Any, 
        provider: str, 
        model: str
    ) -> Optional[Dict[str, Any]]:
        """
        Returns:
        {
            "steps": [
                {"step": 1, "description": "Analyzing...", "duration_ms": 150},
                {"step": 2, "description": "Reasoning...", "duration_ms": 200}
            ],
            "total_thinking_time_ms": 350,
            "reasoning_tokens": 42  # if available
        }
        """
        pass
```

**③ Update Response Schema**

```python
# app/schemas/query.py

class QueryResponse(BaseModel):
    response: str
    citations: Optional[List[Dict]] = None
    
    # NEW: Chain of thought support
    chain_of_thought: Optional[Dict[str, Any]] = None
    supports_cot: bool = False
```

**④ Frontend Integration**
- Add collapsible "Thinking Process" section
- Display reasoning steps with timing
- Show token usage for reasoning

**Files to Create/Modify**:
- `app/services/thought_extractor.py` (NEW)
- `app/providers/base.py` - Add `supports_cot()` method
- `app/schemas/query.py` - Add CoT fields
- `app/api/v1/query.py` - Include CoT in response

---

### 3.2 Word-by-Word Response Streaming

**Problem**: Current implementation only has basic SSE streaming at graph-node level, not token-level streaming.

**Goal**: Implement real-time token-by-token streaming for better UX.

#### Architecture Options

**Option A: Server-Sent Events (SSE) - RECOMMENDED**
- ✅ Simple, widely supported
- ✅ Built into FastAPI via `StreamingResponse`
- ✅ Works over HTTP/1.1
- ❌ Unidirectional (server → client only)

**Option B: WebSocket**
- ✅ Bidirectional
- ✅ Real-time, low latency
- ❌ More complex (connection management, reconnection)
- ❌ Overkill for simple streaming

**Option C: Redis Pub/Sub**
- ✅ Good for multi-instance deployments
- ✅ Enables horizontal scaling
- ❌ Adds infrastructure complexity
- ❌ Not needed for current scale

**Option D: Kafka**
- ✅ Excellent for event sourcing, logging
- ✅ Message persistence, replay
- ❌ Heavy infrastructure overhead
- ❌ Overkill for real-time streaming

**RECOMMENDATION: Use SSE (Option A) with optional Redis for multi-instance**

#### Implementation Plan

**① Create Streaming Service**

```python
# app/services/streaming_service.py

from typing import AsyncGenerator
import asyncio

class StreamingService:
    async def stream_llm_response(
        self,
        provider: str,
        model: str,
        query: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream tokens from LLM providers
        
        Yields:
            JSON-encoded events:
            - {"type": "thought", "content": "..."}  # Chain of thought
            - {"type": "token", "content": "hello"} # Response token
            - {"type": "citation", "data": {...}}   # Source citation
            - {"type": "done", "metadata": {...}}   # Completion
        """
        provider_instance = self.provider_factory.get_provider(provider)
        
        async for event in provider_instance.stream_chat(model, query, **kwargs):
            yield self._format_sse_event(event)
```

**② Update Provider Implementations**

```python
# app/providers/base.py

from abc import ABC, abstractmethod
from typing import AsyncGenerator

class BaseLLMProvider(ABC):
    @abstractmethod
    async def stream_chat(
        self, 
        model: str, 
        messages: List[Dict],
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat completion tokens"""
        pass
    
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Check if provider supports streaming"""
        pass
```

**③ Create Streaming Endpoint**

```python
# app/api/v1/query.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.post("/query/stream")
async def stream_query(
    request: QueryRequest,
    streaming_service: StreamingService = Depends()
):
    """Stream LLM response word-by-word using SSE"""
    
    async def event_generator():
        async for event in streaming_service.stream_llm_response(
            provider=request.model_provider,
            model=request.model_name,
            query=request.query,
            history=request.history
        ):
            yield f"data: {event}\n\n"
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

**④ Add WebSocket Support (Optional)**

```python
# app/api/v1/websocket.py

from fastapi import APIRouter, WebSocket

router = APIRouter()

@router.websocket("/ws/query")
async def websocket_query(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # Receive query
            data = await websocket.receive_json()
            
            # Stream response
            async for token in streaming_service.stream_llm_response(...):
                await websocket.send_json(token)
            
            await websocket.send_json({"type": "done"})
    except WebSocketDisconnect:
        logger.info("Client disconnected")
```

**Files to Create/Modify**:
- `app/services/streaming_service.py` (NEW)
- `app/providers/base.py` - Add streaming interface
- `app/providers/openai_provider.py` - Implement streaming
- `app/providers/anthropic_provider.py` - Implement streaming
- `app/providers/google_provider.py` - Implement streaming
- `app/api/v1/query.py` - Add `/query/stream` endpoint
- `app/api/v1/websocket.py` (NEW - optional)

---

### 3.3 File Upload & RAG Support

**Problem**: Current file upload is basic (validation + storage only). No RAG integration.

**Goal**: Enable file upload → text extraction → embedding → retrieval for context-aware responses.

#### RAG Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     RAG Pipeline                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ① Upload File                                              │
│     │                                                        │
│     ├─► Validate (type, size)                              │
│     ├─► Store (uploads/ or S3)                             │
│     └─► Save metadata (files_collection)                   │
│                                                              │
│  ② Extract Text                                             │
│     │                                                        │
│     ├─► PDF → PyPDF2 / pdfplumber                          │
│     ├─► DOCX → python-docx                                  │
│     ├─► Images → OCR (Tesseract/Google Vision)             │
│     ├─► TXT/MD → Direct read                               │
│     └─► Audio → Whisper API (transcription)                │
│                                                              │
│  ③ Chunk Text                                               │
│     │                                                        │
│     ├─► Semantic chunking (LangChain)                      │
│     ├─► Fixed-size chunks (512-1024 tokens)                │
│     └─► Overlap (128 tokens for context)                   │
│                                                              │
│  ④ Generate Embeddings                                      │
│     │                                                        │
│     ├─► text-embedding-3-small (OpenAI)                    │
│     ├─► text-embedding-ada-002 (fallback)                  │
│     └─► Voyage AI / Cohere (alternatives)                  │
│                                                              │
│  ⑤ Store Vectors                                            │
│     │                                                        │
│     ├─► MongoDB Atlas Vector Search                        │
│     │   (or Qdrant/Pinecone/Weaviate)                      │
│     └─► Link: file_id → chunk_id → embedding               │
│                                                              │
│  ⑥ Retrieval (Query Time)                                   │
│     │                                                        │
│     ├─► Embed user query                                   │
│     ├─► Vector similarity search (cosine)                  │
│     ├─► Retrieve top-k chunks (k=3-5)                      │
│     └─► Re-rank (optional: Cohere Rerank API)              │
│                                                              │
│  ⑦ Augment Prompt                                           │
│     │                                                        │
│     ├─► Inject retrieved context                           │
│     ├─► Add metadata (filename, page, etc.)                │
│     └─► Send to LLM                                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Implementation

**① File Processing Service**

```python
# app/services/rag/file_processor.py

from pathlib import Path
from typing import List, Dict

class FileProcessor:
    """Extract text from various file formats"""
    
    def __init__(self):
        self.extractors = {
            "application/pdf": self._extract_pdf,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": self._extract_docx,
            "text/plain": self._extract_text,
            "text/markdown": self._extract_text,
            "image/*": self._extract_image_ocr,
            "audio/*": self._extract_audio_transcription
        }
    
    async def extract_text(self, file_path: Path, mime_type: str) -> str:
        """Extract text from file based on MIME type"""
        pass
    
    async def _extract_pdf(self, file_path: Path) -> str:
        """Extract text from PDF using PyPDF2 or pdfplumber"""
        pass
    
    async def _extract_image_ocr(self, file_path: Path) -> str:
        """OCR image using Google Vision API or Tesseract"""
        pass
```

**② Text Chunking Service**

```python
# app/services/rag/chunker.py

from langchain.text_splitter import RecursiveCharacterTextSplitter

class TextChunker:
    """Chunk text into semantic units for embedding"""
    
    def __init__(
        self, 
        chunk_size: int = 512, 
        chunk_overlap: int = 128
    ):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Returns:
        [
            {
                "text": "chunk content...",
                "chunk_index": 0,
                "metadata": {...}
            },
            ...
        ]
        """
        pass
```

**③ Embedding Service**

```python
# app/services/rag/embedding_service.py

from openai import AsyncOpenAI
from typing import List

class EmbeddingService:
    """Generate embeddings for text chunks"""
    
    def __init__(self):
        self.client = AsyncOpenAI()
        self.model = "text-embedding-3-small"  # 1536 dimensions
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        pass
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embedding for efficiency"""
        pass
```

**④ Vector Store Service**

```python
# app/services/rag/vector_store.py

from typing import List, Dict

class VectorStore:
    """Store and retrieve embeddings (MongoDB Atlas Vector Search)"""
    
    def __init__(self, db):
        self.collection = db["vectors"]
        # Create vector search index in MongoDB Atlas
    
    async def store_embeddings(
        self,
        file_id: str,
        chunks: List[Dict],
        embeddings: List[List[float]]
    ):
        """Store text chunks with embeddings"""
        documents = [
            {
                "file_id": file_id,
                "chunk_index": i,
                "text": chunk["text"],
                "embedding": embedding,
                "metadata": chunk.get("metadata", {})
            }
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
        await self.collection.insert_many(documents)
    
    async def search_similar(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        file_ids: List[str] = None
    ) -> List[Dict]:
        """Vector similarity search using $vectorSearch"""
        # MongoDB Atlas Vector Search query
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": top_k * 2,
                    "limit": top_k,
                    "filter": {"file_id": {"$in": file_ids}} if file_ids else {}
                }
            },
            {
                "$project": {
                    "text": 1,
                    "metadata": 1,
                    "file_id": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        # Execute and return results
        pass
```

**⑤ RAG Orchestrator**

```python
# app/services/rag/rag_service.py

class RAGService:
    """Orchestrate the complete RAG pipeline"""
    
    def __init__(
        self,
        file_processor: FileProcessor,
        chunker: TextChunker,
        embedding_service: EmbeddingService,
        vector_store: VectorStore
    ):
        self.file_processor = file_processor
        self.chunker = chunker
        self.embedding_service = embedding_service
        self.vector_store = vector_store
    
    async def ingest_file(self, file_id: str, file_path: Path, mime_type: str):
        """Complete ingestion pipeline"""
        # 1. Extract text
        text = await self.file_processor.extract_text(file_path, mime_type)
        
        # 2. Chunk text
        chunks = self.chunker.chunk_text(text, metadata={"file_id": file_id})
        
        # 3. Generate embeddings
        texts = [chunk["text"] for chunk in chunks]
        embeddings = await self.embedding_service.embed_batch(texts)
        
        # 4. Store vectors
        await self.vector_store.store_embeddings(file_id, chunks, embeddings)
    
    async def retrieve_context(
        self, 
        query: str, 
        top_k: int = 3,
        file_ids: List[str] = None
    ) -> List[Dict]:
        """Retrieve relevant context for query"""
        # 1. Embed query
        query_embedding = await self.embedding_service.embed_text(query)
        
        # 2. Vector search
        results = await self.vector_store.search_similar(
            query_embedding, 
            top_k=top_k,
            file_ids=file_ids
        )
        
        return results
```

**⑥ Update Query Flow**

```python
# app/services/query_service.py

class QueryService:
    def __init__(self, rag_service: RAGService):
        self.rag_service = rag_service
    
    async def process_query_with_rag(
        self, 
        query: str,
        user_id: str,
        session_id: str,
        use_rag: bool = True
    ):
        rag_context = None
        
        if use_rag:
            # Get user's uploaded files
            user_files = await self.get_user_files(user_id)
            file_ids = [f["_id"] for f in user_files]
            
            # Retrieve relevant context
            rag_results = await self.rag_service.retrieve_context(
                query, 
                top_k=3,
                file_ids=file_ids
            )
            
            # Format context
            rag_context = self._format_rag_context(rag_results)
        
        # Augment prompt with RAG context
        augmented_query = self._augment_query(query, rag_context)
        
        # Call LLM with augmented prompt
        response = await self.llm_provider.generate(augmented_query)
        
        return response
```

**⑦ API Endpoints**

```python
# app/api/v1/files.py

from fastapi import APIRouter, UploadFile, File

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
    rag_service: RAGService = Depends()
):
    """Upload file and process for RAG"""
    # 1. Save file
    file_id, file_path = await save_upload(file, user_id)
    
    # 2. Async processing (background task)
    background_tasks.add_task(
        rag_service.ingest_file,
        file_id=file_id,
        file_path=file_path,
        mime_type=file.content_type
    )
    
    return {
        "file_id": file_id,
        "status": "processing",
        "message": "File uploaded successfully. Processing in background."
    }

@router.get("/")
async def list_files(user_id: str = Depends(get_current_user)):
    """List user's uploaded files"""
    pass

@router.delete("/{file_id}")
async def delete_file(file_id: str, user_id: str = Depends()):
    """Delete file and associated embeddings"""
    pass
```

**Files to Create**:
- `app/services/rag/file_processor.py` (NEW)
- `app/services/rag/chunker.py` (NEW)
- `app/services/rag/embedding_service.py` (NEW)
- `app/services/rag/vector_store.py` (NEW)
- `app/services/rag/rag_service.py` (NEW)
- `app/api/v1/files.py` (NEW)
- `app/db/repositories/file_repo.py` (NEW)
- `app/schemas/file.py` (NEW)

**Dependencies to Add** (`requirements.txt`):
```
# RAG dependencies
pypdf2>=3.0.0
pdfplumber>=0.10.0
python-docx>=1.0.0
pytesseract>=0.3.10  # OCR
pillow>=10.0.0  # Image processing
langchain>=0.1.0  # Text splitting
openai>=1.0.0  # Embeddings
```

**MongoDB Atlas Setup**:
```javascript
// Create vector search index in MongoDB Atlas
db.vectors.createSearchIndex({
  "name": "vector_index",
  "type": "vectorSearch",
  "definition": {
    "fields": [
      {
        "type": "vector",
        "path": "embedding",
        "numDimensions": 1536,  // text-embedding-3-small
        "similarity": "cosine"
      },
      {
        "type": "filter",
        "path": "file_id"
      }
    ]
  }
})
```

---

## 4. Migration Plan

### Phase 1: Foundation (Week 1-2)
1. ✅ Create new directory structure
2. ✅ Setup `app/core/config.py` with Pydantic Settings
3. ✅ Move schemas to `app/schemas/`
4. ✅ Implement repository pattern in `app/db/repositories/`
5. ✅ Create base middleware

### Phase 2: Refactor Core (Week 3-4)
1. ✅ Extract LLM providers to `app/providers/`
2. ✅ Move routes to `app/api/v1/`
3. ✅ Create service layer `app/services/`
4. ✅ Update `main.py` to use new structure
5. ✅ Add structured logging

### Phase 3: Add Features (Week 5-6)
1. ✅ Implement Chain-of-Thought extraction
2. ✅ Add SSE streaming service
3. ✅ Implement RAG pipeline
4. ✅ Create file upload endpoints

### Phase 4: Testing & Deployment (Week 7-8)
1. ✅ Write unit tests
2. ✅ Write integration tests
3. ✅ Update Docker configuration
4. ✅ Deploy to staging
5. ✅ Performance testing
6. ✅ Production deployment

---

## 5. Best Practices Recommendations

### 5.1 Configuration Management

```python
# app/core/config.py

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App
    APP_NAME: str = "LLM Platform"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    MONGODB_URI: str
    MONGO_DB: str = "llm_experiment"
    
    # LLM Providers
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    
    # Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: float = 10
    
    # RAG
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 128
    
    # Streaming
    ENABLE_SSE: bool = True
    ENABLE_WEBSOCKET: bool = False
    
    # Security
    CORS_ORIGINS: list = ["*"]
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Observability
    LOG_LEVEL: str = "INFO"
    ENABLE_METRICS: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### 5.2 Dependency Injection

```python
# app/api/deps.py

from fastapi import Depends
from app.core.config import settings
from app.db.mongodb import get_db

async def get_services():
    """Dependency injection for services"""
    db = await get_db()
    
    # Initialize services
    rag_service = RAGService(...)
    streaming_service = StreamingService(...)
    
    return {
        "rag_service": rag_service,
        "streaming_service": streaming_service
    }
```

### 5.3 Error Handling

```python
# app/exceptions/base.py

class AppException(Exception):
    """Base exception for all app errors"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class FileProcessingError(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=422)

# app/exceptions/handlers.py

from fastapi import Request, status
from fastapi.responses import JSONResponse

async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "type": exc.__class__.__name__}
    )
```

### 5.4 Structured Logging

```python
# app/core/logging.py

import logging
import sys
from loguru import logger

def setup_logging():
    # Remove default handler
    logger.remove()
    
    # Add custom handler with JSON formatting
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        level="INFO",
        serialize=False  # Set True for JSON logs
    )
    
    # Add file handler
    logger.add(
        "logs/app.log",
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        level="DEBUG"
    )
```

### 5.5 API Versioning

```python
# app/api/v1/router.py

from fastapi import APIRouter
from app.api.v1 import query, sessions, events, products, files

api_router = APIRouter()

api_router.include_router(query.router, prefix="/query", tags=["query"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(files.router, prefix="/files", tags=["files"])

# app/main.py
from app.api.v1.router import api_router

app = FastAPI()
app.include_router(api_router, prefix="/api/v1")
```

### 5.6 Testing Strategy

```python
# tests/conftest.py

import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from app.main import app
from app.core.config import settings

@pytest.fixture
async def test_db():
    """Test database fixture"""
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client["test_db"]
    yield db
    await client.drop_database("test_db")
    client.close()

@pytest.fixture
def test_client():
    """Test client fixture"""
    from fastapi.testclient import TestClient
    return TestClient(app)
```

---

## Summary

### Key Improvements for Production

1. **✅ Modular Architecture**: Separate concerns (API, services, providers, db)
2. **✅ Scalability**: Repository pattern, dependency injection
3. **✅ Testability**: Clear separation, dependency injection, test fixtures
4. **✅ Maintainability**: Smaller files, clear structure, type hints
5. **✅ Observability**: Structured logging, metrics, tracing
6. **✅ Feature-Rich**: Chain-of-thought, streaming, RAG support

### Estimated Effort

- **Refactoring**: 2-3 weeks (full-time)
- **Chain-of-Thought**: 3-5 days
- **Streaming (SSE)**: 3-5 days
- **RAG Pipeline**: 1-2 weeks
- **Testing**: 1 week

### Next Steps

1. Review and approve this architecture proposal
2. Create implementation tasks/issues
3. Start with Phase 1 (Foundation)
4. Iterate and deploy incrementally
5. Monitor and optimize

---

**Do you want me to start implementing any of these suggestions? Let me know which part you'd like to prioritize!** 🚀
