# Backend Migration Task List

**From**: `fastapi-llm-logger/main.py` (1814 lines, monolithic)  
**To**: `backend/app/` (modular, production-grade structure)

---

## 📋 Migration Overview

### Current State
- ✅ Folder structure created
- ⏳ Code still in old `fastapi-llm-logger/main.py`
- ⏳ Need to extract and organize code

### Goal
Migrate all functionality from the monolithic file into the new structure while:
- Maintaining backward compatibility
- Not breaking existing functionality
- Adding tests as we go
- Improving code quality

---

## 🎯 Phase 1: Core Configuration & Database (Priority: HIGH)

### Task 1.1: Setup Configuration Management
**File**: `app/core/config.py`

**What to do**:
1. Extract all environment variables from `main.py` lines 88-117
2. Create Pydantic Settings class
3. Add validation for required fields
4. Setup `.env.example` with all variables

**Source code** (from `fastapi-llm-logger/main.py`):
```python
# Lines 88-117
MONGODB_URI = os.getenv("MONGODB_URI")
MONGO_DB = os.getenv("MONGO_DB", "llm_experiment")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
...
```

**Target**: 
```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    MONGODB_URI: str
    MONGO_DB: str = "llm_experiment"
    
    # API Keys
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None
    
    # ... all other env vars
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**Checklist**:
- [ ] Create `app/core/config.py`
- [ ] Move all env var declarations
- [ ] Add type hints and defaults
- [ ] Create `.env.example` file
- [ ] Test: `from app.core.config import settings`

---

### Task 1.2: Setup Database Connection
**File**: `app/db/mongodb.py`

**What to do**:
1. Move database connection logic from `database.py`
2. Enhance with connection pooling
3. Add error handling
4. Create dependency function

**Source code** (from `fastapi-llm-logger/database.py`):
```python
# Lines 1-22 (entire file)
async def connect_to_mongo():
    global mongo_client, db
    uri = os.getenv("MONGODB_URI")
    ...
```

**Target**:
```python
# app/db/mongodb.py
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

mongodb = MongoDB()

async def connect_db():
    mongodb.client = AsyncIOMotorClient(settings.MONGODB_URI)
    mongodb.db = mongodb.client[settings.MONGO_DB]
    return mongodb.db

async def close_db():
    if mongodb.client:
        mongodb.client.close()

def get_db():
    return mongodb.db
```

**Checklist**:
- [ ] Create `app/db/mongodb.py`
- [ ] Move connection logic
- [ ] Add `connect_db()` and `close_db()`
- [ ] Create `get_db()` dependency
- [ ] Test connection

---

### Task 1.3: Setup Startup/Shutdown Events
**File**: `app/core/events.py`

**What to do**:
1. Extract startup event from `main.py` lines 56-85
2. Extract shutdown event (if any)
3. Initialize agents here

**Source code** (from `main.py`):
```python
# Lines 56-85
@app.on_event("startup")
async def startup_event():
    global db, queries_collection, ...
    db = await connect_to_mongo()
    ...
```

**Target**:
```python
# app/core/events.py
async def startup_event():
    from app.db.mongodb import connect_db
    from app.agents import initialize_agents
    
    # Connect to DB
    db = await connect_db()
    
    # Initialize agents
    await initialize_agents(db)

async def shutdown_event():
    from app.db.mongodb import close_db
    await close_db()
```

**Checklist**:
- [ ] Create `app/core/events.py`
- [ ] Move startup logic
- [ ] Add shutdown logic
- [ ] Test app initialization

---

## 🎯 Phase 2: Schemas & Models (Priority: HIGH)

### Task 2.1: Create Base Schemas
**File**: `app/schemas/base.py`

**What to do**:
1. Extract `AppBaseModel` from `main.py` lines 120-121
2. Create common base classes

**Source code**:
```python
# Lines 120-121
class AppBaseModel(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
```

**Target**:
```python
# app/schemas/base.py
from pydantic import BaseModel, ConfigDict

class AppBaseModel(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

class TimestampMixin(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**Checklist**:
- [ ] Create `app/schemas/base.py`
- [ ] Move `AppBaseModel`
- [ ] Add common mixins
- [ ] Update imports in main.py

---

### Task 2.2: Extract Query Schemas
**File**: `app/schemas/query.py`

**What to do**:
1. Move `QueryRequest` from `main.py` lines 137-150
2. Move `MessageHistory` from lines 124-127
3. Move `LocationInfo` from lines 129-135
4. Create response schemas

**Source code**:
```python
# Lines 124-150
class MessageHistory(AppBaseModel):
    role: str
    content: str

class LocationInfo(AppBaseModel):
    latitude: Optional[float] = None
    ...

class QueryRequest(AppBaseModel):
    user_id: str
    session_id: str
    query: str
    ...
```

**Target**:
```python
# app/schemas/query.py
from app.schemas.base import AppBaseModel
from typing import Optional, List, Dict, Any
from pydantic import Field

class MessageHistory(AppBaseModel):
    role: str
    content: str

class LocationInfo(AppBaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ...

class QueryRequest(AppBaseModel):
    user_id: str
    session_id: str
    query: str
    model_provider: str
    model_name: Optional[str] = None
    ...

class QueryResponse(AppBaseModel):
    response: str
    citations: Optional[List[Dict]] = None
    product_cards: Optional[List[Dict]] = None
    need_memory: Optional[bool] = None
    ...
```

**Checklist**:
- [ ] Create `app/schemas/query.py`
- [ ] Move all query-related schemas
- [ ] Create response schema
- [ ] Add proper type hints
- [ ] Update imports

---

### Task 2.3: Extract Session Schemas
**File**: `app/schemas/session.py`

**What to do**:
1. Move session schemas from `main.py` lines 163-252

**Source code**:
```python
# Lines 163-252
class Environment(AppBaseModel): ...
class EventData(AppBaseModel): ...
class Event(AppBaseModel): ...
class SessionStartRequest(AppBaseModel): ...
class SessionEventRequest(AppBaseModel): ...
class SessionEndRequest(AppBaseModel): ...
```

**Target**: Move all to `app/schemas/session.py`

**Checklist**:
- [ ] Create `app/schemas/session.py`
- [ ] Move all session schemas
- [ ] Update imports

---

### Task 2.4: Extract Other Schemas
**Files**: 
- `app/schemas/event.py`
- `app/schemas/memory.py`
- `app/schemas/product.py`

**What to do**:
1. Move `LogEventRequest` to `event.py`
2. Move `MemoryPayload` to `memory.py`
3. Create product schemas

**Checklist**:
- [ ] Create `app/schemas/event.py`
- [ ] Create `app/schemas/memory.py`
- [ ] Create `app/schemas/product.py`
- [ ] Move respective schemas

---

## 🎯 Phase 3: LLM Providers (Priority: HIGH)

### Task 3.1: Create Base Provider Interface
**File**: `app/providers/base.py`

**What to do**:
1. Create abstract base class for all providers
2. Define common interface

**Target**:
```python
# app/providers/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional

class BaseLLMProvider(ABC):
    """Base class for all LLM providers"""
    
    @abstractmethod
    async def generate(
        self, 
        model: str, 
        query: str,
        system_prompt: Optional[str] = None,
        attachments: Optional[List[Dict]] = None
    ) -> Tuple[str, List[Dict], Dict, Optional[Dict]]:
        """
        Returns: (response_text, citations, raw_response, tokens)
        """
        pass
    
    @abstractmethod
    def supports_streaming(self) -> bool:
        pass
    
    @abstractmethod
    def supports_vision(self) -> bool:
        pass
```

**Checklist**:
- [ ] Create `app/providers/base.py`
- [ ] Define interface methods
- [ ] Add type hints

---

### Task 3.2: Extract OpenAI Provider
**File**: `app/providers/openai_provider.py`

**What to do**:
1. Move `call_openai()` from `main.py` lines 386-471
2. Wrap in class implementing `BaseLLMProvider`

**Source code**:
```python
# Lines 386-471
def call_openai(model: str, query: str, ...):
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    ...
```

**Target**:
```python
# app/providers/openai_provider.py
from openai import OpenAI
from app.providers.base import BaseLLMProvider
from app.core.config import settings

class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate(self, model: str, query: str, ...):
        # Move logic from call_openai()
        ...
        return text, sources, raw, tokens
    
    def supports_streaming(self) -> bool:
        return True
    
    def supports_vision(self) -> bool:
        return "vision" in model or "gpt-4" in model
```

**Checklist**:
- [ ] Create `app/providers/openai_provider.py`
- [ ] Move `call_openai()` logic
- [ ] Implement interface
- [ ] Add async support
- [ ] Test with example query

---

### Task 3.3: Extract Anthropic Provider
**File**: `app/providers/anthropic_provider.py`

**What to do**:
1. Move `call_anthropic()` from `main.py` lines 473-551

**Checklist**:
- [ ] Create `app/providers/anthropic_provider.py`
- [ ] Move logic
- [ ] Implement interface

---

### Task 3.4: Extract Google Provider
**File**: `app/providers/google_provider.py`

**What to do**:
1. Move `call_gemini()` from `main.py` lines 553-639

**Checklist**:
- [ ] Create `app/providers/google_provider.py`
- [ ] Move logic
- [ ] Implement interface

---

### Task 3.5: Extract OpenRouter Provider
**File**: `app/providers/openrouter_provider.py`

**What to do**:
1. Move `call_openrouter()` from `main.py` lines 642-727

**Checklist**:
- [ ] Create `app/providers/openrouter_provider.py`
- [ ] Move logic
- [ ] Implement interface

---

### Task 3.6: Create Provider Factory
**File**: `app/providers/factory.py`

**What to do**:
1. Create factory to instantiate providers
2. Add provider registry

**Target**:
```python
# app/providers/factory.py
from app.providers.openai_provider import OpenAIProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.google_provider import GoogleProvider
from app.providers.openrouter_provider import OpenRouterProvider

class ProviderFactory:
    _providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "openrouter": OpenRouterProvider,
    }
    
    @classmethod
    def get_provider(cls, provider_name: str):
        provider_class = cls._providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")
        return provider_class()
```

**Checklist**:
- [ ] Create `app/providers/factory.py`
- [ ] Implement factory pattern
- [ ] Test provider instantiation

---

## 🎯 Phase 4: API Routes (Priority: HIGH)

### Task 4.1: Extract Health/Status Routes
**File**: `app/api/v1/health.py`

**What to do**:
1. Move `/` endpoint from `main.py` line 730-732
2. Move `/status` endpoint from lines 735-745

**Source code**:
```python
# Lines 730-745
@app.get("/")
async def root():
    return {"message": "LLM Interaction Logger API", "version": "2.0.0"}

@app.get("/status")
async def status():
    return {
        "status": "running",
        "mongodb_connected": db is not None,
        ...
    }
```

**Target**:
```python
# app/api/v1/health.py
from fastapi import APIRouter, Depends
from app.db.mongodb import get_db

router = APIRouter(tags=["health"])

@router.get("/")
async def root():
    return {"message": "LLM Platform API", "version": "2.0.0"}

@router.get("/status")
async def status(db = Depends(get_db)):
    return {
        "status": "running",
        "mongodb_connected": db is not None,
        ...
    }
```

**Checklist**:
- [ ] Create `app/api/v1/health.py`
- [ ] Move endpoints
- [ ] Add router
- [ ] Test endpoints

---

### Task 4.2: Extract Query Routes
**File**: `app/api/v1/query.py`

**What to do**:
1. Move `/query` endpoint from `main.py` lines 748-1119
2. Move `/query/stream` endpoint from lines 1161-1328
3. Extract logic to service layer

**Source code**:
```python
# Lines 748-1119
@app.post("/query")
async def query_llm(request: QueryRequest):
    # 371 lines of logic!
    ...
```

**Target**:
```python
# app/api/v1/query.py
from fastapi import APIRouter, Depends
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import QueryService

router = APIRouter(prefix="/query", tags=["query"])

@router.post("/")
async def query_llm(
    request: QueryRequest,
    service: QueryService = Depends()
) -> QueryResponse:
    # Delegate to service
    return await service.process_query(request)

@router.post("/stream")
async def query_llm_stream(request: QueryRequest):
    # Streaming logic
    ...
```

**Checklist**:
- [ ] Create `app/api/v1/query.py`
- [ ] Move endpoints
- [ ] Extract business logic to service
- [ ] Test endpoints

---

### Task 4.3: Extract Session Routes
**File**: `app/api/v1/sessions.py`

**What to do**:
1. Move `/session/start` from `main.py` lines 1397-1429
2. Move `/session/event` from lines 1432-1462
3. Move `/session/end` from lines 1465-1485
4. Move `/session/{session_id}` from lines 1488-1515

**Checklist**:
- [ ] Create `app/api/v1/sessions.py`
- [ ] Move all session endpoints
- [ ] Create session service
- [ ] Test endpoints

---

### Task 4.4: Extract Event Routes
**File**: `app/api/v1/events.py`

**What to do**:
1. Move `/log_event` from lines 1331-1350

**Checklist**:
- [ ] Create `app/api/v1/events.py`
- [ ] Move event endpoint
- [ ] Test endpoint

---

### Task 4.5: Extract Product Routes
**File**: `app/api/v1/products.py`

**What to do**:
1. Move `/search/products` from lines 1354-1393

**Checklist**:
- [ ] Create `app/api/v1/products.py`
- [ ] Move product endpoint
- [ ] Test endpoint

---

### Task 4.6: Extract Memory Routes
**Files**: 
- `app/api/v1/memories.py`
- `app/api/v1/files.py`

**What to do**:
1. Move memory CRUD endpoints from lines 1518-1600
2. Move file upload endpoints from lines 1602-1810

**Checklist**:
- [ ] Create `app/api/v1/memories.py`
- [ ] Create `app/api/v1/files.py`
- [ ] Move endpoints
- [ ] Test endpoints

---

### Task 4.7: Create Router Aggregator
**File**: `app/api/v1/router.py`

**What to do**:
1. Import all routers
2. Create main API router

**Target**:
```python
# app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1 import health, query, sessions, events, products, memories, files

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(query.router)
api_router.include_router(sessions.router)
api_router.include_router(events.router)
api_router.include_router(products.router)
api_router.include_router(memories.router)
api_router.include_router(files.router)
```

**Checklist**:
- [ ] Create `app/api/v1/router.py`
- [ ] Import all routers
- [ ] Test complete API

---

## 🎯 Phase 5: Services (Priority: MEDIUM)

### Task 5.1: Create Query Service
**File**: `app/services/query_service.py`

**What to do**:
1. Extract business logic from `/query` endpoint
2. Implement `QueryService` class

**Target**:
```python
# app/services/query_service.py
from app.providers.factory import ProviderFactory
from app.agents.graph import graph_app

class QueryService:
    def __init__(self, db):
        self.db = db
        self.provider_factory = ProviderFactory()
    
    async def process_query(self, request: QueryRequest):
        # Multi-agent processing
        result = await graph_app.ainvoke({...})
        
        # Log to database
        await self._log_query(...)
        
        return result
```

**Checklist**:
- [ ] Create `app/services/query_service.py`
- [ ] Move business logic
- [ ] Add logging
- [ ] Test service

---

### Task 5.2: Create Session Service
**File**: `app/services/session_service.py`

**What to do**:
1. Extract session management logic

**Checklist**:
- [ ] Create `app/services/session_service.py`
- [ ] Implement methods
- [ ] Test service

---

### Task 5.3: Create Other Services
**Files**:
- `app/services/event_service.py`
- `app/services/memory_service.py`
- `app/services/file_service.py`

**Checklist**:
- [ ] Create all service files
- [ ] Move logic from endpoints
- [ ] Test each service

---

## 🎯 Phase 6: Repositories (Priority: MEDIUM)

### Task 6.1: Create Base Repository
**File**: `app/db/repositories/base.py`

**Target**:
```python
# app/db/repositories/base.py
from typing import Generic, TypeVar, Optional, List

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, db, collection_name: str):
        self.collection = db[collection_name]
    
    async def create(self, data: dict) -> str:
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)
    
    async def find_by_id(self, id: str) -> Optional[dict]:
        return await self.collection.find_one({"_id": ObjectId(id)})
    
    async def find_many(self, filter: dict, limit: int = 100) -> List[dict]:
        cursor = self.collection.find(filter).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def update(self, id: str, data: dict):
        await self.collection.update_one({"_id": ObjectId(id)}, {"$set": data})
    
    async def delete(self, id: str):
        await self.collection.delete_one({"_id": ObjectId(id)})
```

**Checklist**:
- [ ] Create `app/db/repositories/base.py`
- [ ] Implement CRUD methods
- [ ] Add type hints

---

### Task 6.2: Create Specific Repositories
**Files**:
- `app/db/repositories/query_repo.py`
- `app/db/repositories/session_repo.py`
- `app/db/repositories/event_repo.py`
- `app/db/repositories/memory_repo.py`
- `app/db/repositories/product_repo.py`

**Target**:
```python
# app/db/repositories/query_repo.py
from app.db.repositories.base import BaseRepository

class QueryRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "queries")
    
    async def find_by_session(self, session_id: str):
        return await self.find_many({"session_id": session_id})
    
    async def find_by_user(self, user_id: str, limit: int = 50):
        return await self.find_many({"user_id": user_id}, limit=limit)
```

**Checklist**:
- [ ] Create all repository files
- [ ] Inherit from `BaseRepository`
- [ ] Add custom query methods
- [ ] Test each repository

---

## 🎯 Phase 7: Utilities & Helpers (Priority: LOW)

### Task 7.1: Move Utility Functions
**File**: Keep existing `app/utils/` but add:

**What to do**:
1. Move `format_location_text()` from `main.py` lines 353-382
2. Move `_validate_file()` from lines 264-273
3. Move `_save_upload()` from lines 275-288

**Checklist**:
- [ ] Create `app/utils/helpers.py`
- [ ] Move utility functions
- [ ] Update imports

---

## 🎯 Phase 8: Update Main Application (Priority: HIGH)

### Task 8.1: Simplify main.py
**File**: `app/main.py`

**What to do**:
1. Reduce to < 100 lines
2. Just app initialization and middleware

**Target**:
```python
# app/main.py (should be ~50 lines)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.events import startup_event, shutdown_event
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Events
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

# Routes
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
```

**Checklist**:
- [ ] Simplify main.py
- [ ] Remove all route definitions
- [ ] Keep only app setup
- [ ] Test app startup

---

## 🎯 Phase 9: Agents (Priority: LOW)

### Task 9.1: Keep Existing Agents
**What to do**:
1. Keep `app/agents/` as is
2. Update imports to use new structure

**Checklist**:
- [ ] Update agent imports
- [ ] Test agent initialization
- [ ] Update `graph.py` imports

---

## 🎯 Phase 10: Testing & Cleanup (Priority: MEDIUM)

### Task 10.1: Add Tests
**Files**: `app/tests/`

**What to do**:
1. Create test fixtures in `conftest.py`
2. Write unit tests for services
3. Write integration tests for API

**Checklist**:
- [ ] Create `tests/conftest.py`
- [ ] Write service tests
- [ ] Write API tests
- [ ] Run all tests

---

### Task 10.2: Update Dependencies
**File**: `requirements.txt`

**What to do**:
1. Add new dependencies if needed:
   - `pydantic-settings`
   - `pytest`
   - `httpx`

**Checklist**:
- [ ] Update `requirements.txt`
- [ ] Create `requirements-dev.txt`
- [ ] Run `pip install -r requirements.txt`

---

### Task 10.3: Update Docker Configuration
**Files**: `Dockerfile`, `docker-compose.yml`

**What to do**:
1. Update paths if needed
2. Test Docker build

**Checklist**:
- [ ] Update Dockerfile
- [ ] Test `docker build`
- [ ] Test `docker-compose up`

---

### Task 10.4: Documentation
**Files**: `README.md`

**What to do**:
1. Update README with new structure
2. Document new architecture
3. Add API documentation

**Checklist**:
- [ ] Update README
- [ ] Add architecture diagram
- [ ] Document API endpoints

---

## 📊 Progress Tracking

### Overall Progress
```
[▓▓▓░░░░░░░] 30% Complete

Completed Tasks: 0/75
In Progress: 1/75
Remaining: 74/75
```

### Priority Breakdown
- **HIGH Priority**: 30 tasks
- **MEDIUM Priority**: 25 tasks  
- **LOW Priority**: 20 tasks

---

## 🚀 Recommended Execution Order

1. **Week 1**: Phase 1 + Phase 2 (Config, DB, Schemas)
2. **Week 2**: Phase 3 (Providers)
3. **Week 3**: Phase 4 (API Routes)
4. **Week 4**: Phase 5 + Phase 6 (Services + Repositories)
5. **Week 5**: Phase 8 (Update main.py) + Testing
6. **Week 6**: Phase 10 (Testing, Docker, Documentation)

---

## ⚠️ Important Notes

1. **Don't delete old code** until new code is tested
2. **Test after each phase** to ensure nothing breaks
3. **Keep both servers running** during migration (old on 8000, new on 8001)
4. **Update imports incrementally** as you move code
5. **Use git branches** for safety

---

## 🎯 Next Steps

**Start with Task 1.1** (Configuration Management) - this is the foundation for everything else!

Would you like me to help you implement any specific task? I can:
- Create the code for any task
- Show you examples
- Help debug issues
- Review your implementation

Just let me know which task you want to tackle first! 🚀
