# LLM Platform - Test Suite

Comprehensive test suite for the LLM Platform backend migration.

## 📁 Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── unit/                    # Unit tests (isolated component testing)
│   ├── test_services/       # Service layer tests
│   │   ├── test_query_service.py
│   │   ├── test_memory_service.py
│   │   ├── test_embedding_service.py
│   │   ├── test_session_service.py
│   │   ├── test_file_service.py
│   │   └── test_event_service.py
│   ├── test_providers/      # LLM provider tests (TODO)
│   └── test_agents/         # Agent tests (TODO)
├── integration/             # Integration tests (API endpoints)
│   ├── test_api/
│   │   ├── test_query_routes.py
│   │   ├── test_session_routes.py
│   │   └── test_health_routes.py
│   └── test_db/             # Database integration tests (TODO)
└── e2e/                     # End-to-end tests (TODO)
```

## 🚀 Quick Start

### Prerequisites

1. Install test dependencies:

```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

2. Ensure you're in the project root:

```bash
cd /Users/annahuang/Documents/LLMPlatform
```

### Running Tests

#### Run all tests:

```bash
# From project root
pytest backend/app/tests/ -v

# Or from backend directory
cd backend && pytest app/tests/ -v
```

#### Run specific test categories:

```bash

use uv run for quicker
uv run pytest app/tests/unit/ -v
# Unit tests only
pytest backend/app/tests/unit/ -v

# Integration tests only
pytest backend/app/tests/integration/ -v

# Specific service tests
pytest backend/app/tests/unit/test_services/test_query_service.py -v

# Specific test function
pytest backend/app/tests/unit/test_services/test_query_service.py::TestQueryService::test_process_query_with_agents -v
```

#### Run with coverage:

```bash
# Generate coverage report
pytest backend/app/tests/ --cov=backend/app --cov-report=html --cov-report=term

# View HTML coverage report
open htmlcov/index.html
```

#### Run tests in parallel (faster):

```bash
# Install pytest-xdist first
pip install pytest-xdist

# Run with multiple workers
pytest backend/app/tests/ -n auto -v
```

## 📊 Test Categories

### Unit Tests

Test individual components in isolation using mocks:

- **Service Tests**: Test business logic without database/external dependencies
- **Provider Tests**: Test LLM provider integrations (mocked)
- **Agent Tests**: Test agent behavior (mocked)

**Key characteristics:**
- Fast execution (no I/O)
- Use mocks for dependencies
- Focus on logic and behavior
- Should pass without database/API keys

### Integration Tests

Test API endpoints and component interactions:

- **API Route Tests**: Test FastAPI endpoints end-to-end
- **Database Tests**: Test actual database operations
- **Multi-component Tests**: Test how services work together

**Key characteristics:**
- Slower than unit tests
- May use test database
- Test real interactions
- Verify request/response formats

### End-to-End Tests (TODO)

Test complete user workflows:

- Full query processing pipeline
- Multi-agent coordination
- Session lifecycle with multiple queries

## 🔧 Test Fixtures

Common fixtures available in `conftest.py`:

### Clients
- `test_client`: FastAPI TestClient for API testing

### Database Mocks
- `mock_db`: Mocked MongoDB database
- `override_get_db`: Dependency override for database

### Sample Data
- `sample_query_request`: Valid QueryRequest data
- `sample_query_response`: Valid QueryResponse data
- `sample_session_start_request`: Valid SessionStartRequest
- `sample_event`: Valid Event data
- `sample_embedding`: Mock embedding vector (1536 dims)
- `sample_memory_context`: Mock memory context

### Service Mocks
- `mock_query_service`: Mocked QueryService
- `mock_memory_service`: Mocked MemoryService
- `mock_embedding_service`: Mocked EmbeddingService
- `mock_session_service`: Mocked SessionService
- `mock_file_service`: Mocked FileService
- `mock_event_service`: Mocked EventService

### Provider Mocks
- `mock_provider`: Generic LLM provider mock
- `mock_provider_factory`: Mocked ProviderFactory

### Agent Mocks
- `mock_coordinator`: Mocked coordinator agent

## 📝 Writing New Tests

### Unit Test Example

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
class TestMyService:
    async def test_my_function(self, mock_db):
        # Arrange
        with patch("app.services.my_service.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db

            # Act
            result = await my_service.do_something()

            # Assert
            assert result is not None
            mock_db.collection.insert_one.assert_called_once()
```

### Integration Test Example

```python
class TestMyRoute:
    def test_my_endpoint(self, test_client, mock_service):
        # Arrange
        request_data = {"key": "value"}
        mock_service.process.return_value = {"result": "success"}

        # Act
        response = test_client.post("/api/v1/my-endpoint", json=request_data)

        # Assert
        assert response.status_code == 200
        assert response.json()["result"] == "success"
```

## 🎯 Test Coverage Goals

| Component | Target Coverage | Current Status |
|-----------|----------------|----------------|
| Services | 90%+ | ✅ 6/6 services |
| API Routes | 85%+ | ✅ 3/6 routes |
| Providers | 80%+ | ⏳ TODO |
| Agents | 75%+ | ⏳ TODO |
| Utilities | 70%+ | ⏳ TODO |

## 🐛 Debugging Tests

### Run with verbose output:

```bash
pytest backend/app/tests/ -vv
```

### Show print statements:

```bash
pytest backend/app/tests/ -s
```

### Run specific test and stop on first failure:

```bash
pytest backend/app/tests/unit/test_services/ -x -v
```

### Run only failed tests from last run:

```bash
pytest --lf
```

### Drop into debugger on failure:

```bash
pytest --pdb
```

## 🔍 Common Issues

### Import Errors

If you get import errors, ensure you're running from the correct directory:

```bash
# Run from project root, not from tests directory
cd /Users/annahuang/Documents/LLMPlatform
pytest backend/app/tests/ -v
```

### Async Test Errors

Make sure async tests use the `@pytest.mark.asyncio` decorator:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Database Connection Issues

Unit tests should NOT require database connections. If you're seeing database errors:

1. Check that `mock_db` fixture is being used
2. Verify `get_db` is properly patched
3. Ensure test is in the correct category (unit vs integration)

### Mock Not Working

Common mock issues:

```python
# ❌ Wrong - mocking after import
from app.services.my_service import service
with patch("app.services.my_service.dependency"):
    # dependency already imported!

# ✅ Correct - mock the full path
with patch("app.services.my_service.dependency"):
    from app.services.my_service import service
```

## 📈 Next Steps

### TODO: Additional Tests Needed

1. **Provider Tests**:
   - OpenAI provider
   - Anthropic provider
   - Google provider
   - OpenRouter provider

2. **Agent Tests**:
   - Coordinator agent
   - Shopping agent
   - Writer agent
   - Memory agent

3. **Additional API Tests**:
   - Product routes
   - File upload routes
   - Event routes

4. **End-to-End Tests**:
   - Complete query flow
   - Multi-turn conversations
   - Agent orchestration

5. **Performance Tests**:
   - Load testing
   - Concurrent requests
   - Memory usage

## 🎓 Best Practices

1. **Arrange-Act-Assert Pattern**: Structure tests clearly
2. **One Assertion Per Test**: Keep tests focused
3. **Descriptive Names**: Test names should describe what they test
4. **Mock External Dependencies**: Don't hit real APIs/databases in unit tests
5. **Test Edge Cases**: Empty inputs, errors, boundary conditions
6. **Clean Up**: Use fixtures for setup/teardown
7. **Fast Tests**: Unit tests should run in milliseconds

## 📚 Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Python Mock](https://docs.python.org/3/library/unittest.mock.html)

---

**Last Updated**: 2025-12-29
**Test Suite Status**: ✅ Phase 1 Complete (Infrastructure + Core Services)
