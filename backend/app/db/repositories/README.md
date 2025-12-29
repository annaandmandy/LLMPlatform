# Repository Layer

Clean data access abstraction for MongoDB operations.

## Overview

Repositories provide a consistent interface for database operations, making the codebase more:
- **Testable**: Mock at the repository level instead of MongoDB
- **Maintainable**: Centralized query logic
- **Team-friendly**: Clear contracts for data access

## Architecture

```
Services → Repositories → MongoDB
```

Services use repositories instead of accessing the database directly. This separates business logic from data access.

## Available Repositories

### BaseRepository
Generic CRUD operations inherited by all repositories:

```python
# Create
doc_id = await repo.create({"key": "value"})

# Read
doc = await repo.find_one({"key": "value"})
docs = await repo.find_many({"user_id": "123"}, limit=10)

# Update
count = await repo.update_one({"_id": doc_id}, {"$set": {"new_field": "value"}})

# Delete
count = await repo.delete_one({"_id": doc_id})

# Utilities
exists = await repo.exists({"key": "value"})
total = await repo.count({"user_id": "123"})
```

### QueryRepository
Manages query logs and history:

```python
from app.db.repositories import QueryRepository

query_repo = QueryRepository(db)

# Log a query
await query_repo.create_query_log(
    user_id="user_123",
    session_id="session_456",
    query="What is Python?",
    response="Python is...",
    embedding=[0.1, 0.2, ...],
    metadata={"model": "gpt-4", "tokens": 150}
)

# Get user history
queries = await query_repo.get_user_query_history(
    user_id="user_123",
    limit=50
)

# Get session queries
session_queries = await query_repo.get_session_queries(
    session_id="session_456"
)
```

### SessionRepository
Manages user sessions:

```python
from app.db.repositories import SessionRepository

session_repo = SessionRepository(db)

# Create session
await session_repo.create_session(
    session_id="session_123",
    user_id="user_456",
    environment={"device": "mobile"}
)

# Add event to session
await session_repo.add_event(
    session_id="session_123",
    event={"type": "click", "data": {...}}
)

# End session
await session_repo.end_session(session_id="session_123")

# Get session
session = await session_repo.get_session(
    session_id="session_123",
    include_events=True
)

# Get user's sessions
sessions = await session_repo.get_user_sessions(
    user_id="user_456",
    limit=20
)
```

### SummaryRepository
Manages session summaries:

```python
from app.db.repositories import SummaryRepository

summary_repo = SummaryRepository(db)

# Create or update summary
await summary_repo.create_or_update_summary(
    session_id="session_123",
    summary_text="User asked about Python basics...",
    message_count=10,
    model_used="gpt-4o-mini",
    user_id="user_456"
)

# Get summaries by session
summaries = await summary_repo.get_summaries_by_session(
    session_id="session_123",
    limit=5
)

# Get summaries by user
user_summaries = await summary_repo.get_summaries_by_user(
    user_id="user_456",
    limit=3
)
```

### ProductRepository
Manages product catalog:

```python
from app.db.repositories import ProductRepository

product_repo = ProductRepository(db)

# Create product
await product_repo.create_product(
    product_id="prod_123",
    name="Laptop",
    description="High-performance laptop",
    price=999.99,
    metadata={"category": "electronics"}
)

# Search products
products = await product_repo.search_products(
    query="laptop",
    limit=10,
    filters={"price": {"$lt": 1000}}
)

# Get product
product = await product_repo.get_product("prod_123")
```

## Usage in Services

Instead of accessing MongoDB directly, services use repositories:

**Before (Direct DB access):**
```python
class MyService:
    async def get_user_queries(self, user_id: str):
        db = get_db()
        queries = await db["queries"].find({"user_id": user_id}).to_list()
        return queries
```

**After (Repository pattern):**
```python
class MyService:
    def __init__(self):
        self.query_repo = QueryRepository(get_db())
    
    async def get_user_queries(self, user_id: str):
        return await self.query_repo.get_user_query_history(user_id)
```

## Benefits for Teams

1. **Consistent Patterns**: All data access follows the same patterns
2. **Easier Testing**: Mock repositories instead of MongoDB
3. **Clear Ownership**: Each repository owns its collection's logic
4. **Reusable Logic**: Common queries in one place
5. **Type Safety**: Clear method signatures

## Testing

Mock repositories in tests:

```python
from unittest.mock import AsyncMock

# Mock repository
mock_repo = AsyncMock(spec=QueryRepository)
mock_repo.get_user_query_history.return_value = [...]

# Use in service tests
service = MyService()
service.query_repo = mock_repo  # Inject mock
```

## Best Practices

1. **Use repositories in services**, not in routes
2. **Keep complex queries in repositories**, not scattered across services
3. **Document repository methods** with clear docstrings
4. **Return domain objects** when appropriate (not raw dicts)
5. **Handle errors at service layer**, not in repositories

## Future Enhancements

- Add type hints for return values (Pydantic models)
- Implement repository caching layer
- Add support for transactions
- Implement advanced vector similarity search features
