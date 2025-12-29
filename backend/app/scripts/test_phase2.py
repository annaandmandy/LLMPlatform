"""
Test script to verify Phase 2 implementation (Schemas).

Run this to test:
    python -m app.scripts.test_phase2
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def main():
    print("=" * 60)
    print("🧪 Testing Phase 2: Schemas")
    print("=" * 60)
    
    # Test 1: Base Schemas
    print("\n📋 Test 1: Base Schemas")
    try:
        from app.schemas.base import AppBaseModel, TimestampMixin, UserIdentifiableMixin
        print("✅ AppBaseModel imported")
        print("✅ TimestampMixin imported")
        print("✅ UserIdentifiableMixin imported")
        print("✅ Base schemas test PASSED")
    except Exception as e:
        print(f"❌ Base schemas test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Query Schemas
    print("\n🔍 Test 2: Query Schemas")
    try:
        from app.schemas.query import (
            LocationInfo, MessageHistory, QueryRequest,
            QueryResponse, Citation, ProductCard
        )
        
        # Test creating instances
        location = LocationInfo(latitude=40.7128, longitude=-74.0060, city="New York")
        print(f"✅ LocationInfo created: {location.city}")
        
        message = MessageHistory(role="user", content="Hello")
        print(f"✅ MessageHistory created: {message.role}")
        
        request = QueryRequest(
            user_id="test123",
            session_id="sess456",
            query="What is AI?",
            model_provider="openai"
        )
        print(f"✅ QueryRequest created: {request.query}")
        
        response = QueryResponse(response="AI is...")
        print(f"✅ QueryResponse created")
        
        citation = Citation(title="Test", url="https://example.com")
        print(f"✅ Citation created: {citation.title}")
        
        product = ProductCard(
            title="Product",
            description="Test",
            url="https://example.com"
        )
        print(f"✅ ProductCard created: {product.title}")
        
        print("✅ Query schemas test PASSED")
    except Exception as e:
        print(f"❌ Query schemas test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Session Schemas
    print("\n📊 Test 3: Session Schemas")
    try:
        from app.schemas.session import (
            Environment, EventData, Event,
            SessionStartRequest, SessionEventRequest, SessionEndRequest
        )
        
        env = Environment(
            device="Desktop",
            browser="Chrome 120",
            os="macOS",
            viewport={"width": 1920, "height": 1080}
        )
        print(f"✅ Environment created: {env.device}")
        
        event_data = EventData(text="test", scrollY=100.0)
        print(f"✅ EventData created")
        
        event = Event(t=1700000000000, type="scroll", data=event_data)
        print(f"✅ Event created: {event.type}")
        
        sess_start = SessionStartRequest(
            session_id="sess123",
            user_id="user456",
            environment=env
        )
        print(f"✅ SessionStartRequest created")
        
        print("✅ Session schemas test PASSED")
    except Exception as e:
        print(f"❌ Session schemas test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Other Schemas
    print("\n📦 Test 4: Other Schemas (Event, Memory, Product)")
    try:
        from app.schemas.event import LogEventRequest, EventResponse
        from app.schemas.memory import MemoryPayload, MemoryResponse
        from app.schemas.product import ProductSearchRequest, Product, ProductSearchResponse
        
        log_event = LogEventRequest(
            user_id="user123",
            session_id="sess456",
            event_type="click"
        )
        print(f"✅ LogEventRequest created: {log_event.event_type}")
        
        memory = MemoryPayload(user_id="user123", key="name", value="John")
        print(f"✅ MemoryPayload created: {memory.key}={memory.value}")
        
        product_search = ProductSearchRequest(query="laptop")
        print(f"✅ ProductSearchRequest created: {product_search.query}")
        
        product = Product(
            title="Laptop",
            description="Gaming laptop",
            url="https://example.com",
            price="$1000"
        )
        print(f"✅ Product created: {product.title}")
        
        print("✅ Other schemas test PASSED")
    except Exception as e:
        print(f"❌ Other schemas test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Package Import
    print("\n📦 Test 5: Package-level Import")
    try:
        from app.schemas import (
            QueryRequest, QueryResponse, SessionStartRequest,
            LogEventRequest, MemoryPayload, ProductSearchRequest
        )
        print("✅ All schemas importable from app.schemas")
        print("✅ Package import test PASSED")
    except Exception as e:
        print(f"❌ Package import test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 6: Model Dumps (JSON serialization)
    print("\n🔄 Test 6: JSON Serialization")
    try:
        from app.schemas import QueryRequest, Event, EventData
        
        request = QueryRequest(
            user_id="test",
            session_id="sess",
            query="Hello",
            model_provider="openai",
            history=[
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello!"}
            ]
        )
        request_dict = request.model_dump()
        print(f"✅ QueryRequest serialized: {len(request_dict)} fields")
        
        event_data = EventData(text="test", scrollY=100.0)
        event = Event(t=1700000000000, type="scroll", data=event_data)
        event_dict = event.model_dump()
        print(f"✅ Event serialized: {len(event_dict)} fields")
        
        # Check exclude_none works
        assert None not in event_dict.get('data', {}).values()
        print("✅ None values excluded correctly")
        
        print("✅ JSON serialization test PASSED")
    except Exception as e:
        print(f"❌ JSON serialization test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✨ ALL TESTS PASSED! Phase 2 is working correctly! ✨")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
