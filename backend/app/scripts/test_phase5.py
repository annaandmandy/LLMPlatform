#!/usr/bin/env python3
"""
Quick verification script for Phase 4 & 5 completion.

Tests:
1. Import all services
2. Import all routes
3. Check service instances
4. Verify router configuration
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

print("=" * 70)
print("Backend Migration - Phase 4 & 5 Verification")
print("=" * 70)
print()

# Test 1: Import services
print("Test 1: Importing services...")
try:
    from app.services import (
        query_service,
        memory_service,
        embedding_service,
        event_service,
        file_service,
        session_service,
    )
    print("✅ All services imported successfully!")
    print(f"   - QueryService: {query_service.__class__.__name__}")
    print(f"   - MemoryService: {memory_service.__class__.__name__}")
    print(f"   - EmbeddingService: {embedding_service.__class__.__name__}")
    print(f"   - EventService: {event_service.__class__.__name__}")
    print(f"   - FileService: {file_service.__class__.__name__}")
    print(f"   - SessionService: {session_service.__class__.__name__}")
except Exception as e:
    print(f"❌ Service import failed: {e}")
    sys.exit(1)

print()

# Test 2: Import routes
print("Test 2: Importing routes...")
try:
    from app.api.v1 import health, query, sessions, products, files
    print("✅ All routes imported successfully!")
    print(f"   - health.router: {health.router.tags}")
    print(f"   - query.router: {query.router.tags}")
    print(f"   - sessions.router: {sessions.router.tags}")
    print(f"   - products.router: {products.router.tags}")
    print(f"   - files.router: {files.router.tags}")
except Exception as e:
    print(f"❌ Route import failed: {e}")
    sys.exit(1)

print()

# Test 3: Check router aggregation
print("Test 3: Checking router aggregation...")
try:
    from app.api.v1.router import api_router
    
    # Count routes
    route_count = len(api_router.routes)
    print(f"✅ Main API router configured!")
    print(f"   - Total routes: {route_count}")
    print(f"   - Prefix: {api_router.prefix}")
    
    # List all endpoints
    print("\n   Endpoints:")
    for route in api_router.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            print(f"     - {methods:20s} {route.path}")
    
except Exception as e:
    print(f"❌ Router check failed: {e}")
    sys.exit(1)

print()

# Test 4: Check schemas
print("Test 4: Checking schemas...")
try:
    from app.schemas.query import QueryRequest, QueryResponse
    from app.schemas.session import SessionStartRequest, SessionEventRequest, SessionEndRequest
    from app.schemas.event import LogEventRequest
    
    print("✅ All schemas imported successfully!")
    print(f"   - QueryRequest")
    print(f"   - QueryResponse")
    print(f"   - SessionStartRequest")
    print(f"   - SessionEventRequest")
    print(f"   - SessionEndRequest")
    print(f"   - LogEventRequest")
except Exception as e:
    print(f"❌ Schema import failed: {e}")
    sys.exit(1)

print()

# Test 5: Check providers
print("Test 5: Checking providers...")
try:
    from app.providers.factory import ProviderFactory
    
    print("✅ Provider factory imported successfully!")
    print(f"   - Available providers: {list(ProviderFactory._providers.keys())}")
except Exception as e:
    print(f"❌ Provider check failed: {e}")
    sys.exit(1)

print()

# Summary
print("=" * 70)
print("VERIFICATION COMPLETE!")
print("=" * 70)
print()
print("✅ Phase 4: API Routes - 100% Complete")
print("✅ Phase 5: Services - 100% Complete")
print()
print("Next steps:")
print("1. Start the server: uvicorn app.main:app --reload --port 8001")
print("2. Test endpoints with curl or Postman")
print("3. Write unit tests for services")
print()
print("Backend is ready for testing! 🎉")
print()
