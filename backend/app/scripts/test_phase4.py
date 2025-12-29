"""
Test script to verify Phase 4 implementation (API Routes - Partial).

Run this to test:
    python -m app.scripts.test_phase4
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def main():
    print("=" * 60)
    print("🧪 Testing Phase 4: API Routes (Partial)")
    print("=" * 60)
    
    # Test 1: Health Routes
    print("\n💚 Test 1: Health Routes")
    try:
        from app.api.v1 import health
        
        assert hasattr(health, 'router')
        print("✅ Health router exists")
        
        # Check routes
        routes = [route.path for route in health.router.routes]
        print(f"✅ Health routes: {routes}")
        assert "/" in routes
        assert "/status" in routes
        assert "/health" in routes
        
        print("✅ Health routes test PASSED")
    except Exception as e:
        print(f"❌ Health routes test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Event Routes
    print("\n📊 Test 2: Event Routes")
    try:
        from app.api.v1 import events
        
        assert hasattr(events, 'router')
        print("✅ Events router exists")
        
        # Check routes
        routes = [route.path for route in events.router.routes]
        print(f"✅ Event routes: {routes}")
        
        print("✅ Event routes test PASSED")
    except Exception as e:
        print(f"❌ Event routes test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Router Aggregator
    print("\n🔗 Test 3: Router Aggregator")
    try:
        from app.api.v1.router import api_router
        
        print("✅ API router imported")
        
        # Check that routers are included
        assert api_router.prefix == "/api/v1"
        print(f"✅ API router prefix: {api_router.prefix}")
        
        # Count routes
        total_routes = len(api_router.routes)
        print(f"✅ Total routes registered: {total_routes}")
        
        print("✅ Router aggregator test PASSED")
    except Exception as e:
        print(f"❌ Router aggregator test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Main App
    print("\n🚀 Test 4: Main Application")
    try:
        from app.main import app
        
        print("✅ New main app imported")
        
        # Check app configuration
        assert app.title == "LLM Platform"
        print(f"✅ App title: {app.title}")
        
        assert app.version == "2.0.0"
        print(f"✅ App version: {app.version}")
        
        # Check routes are registered
        app_routes = [route.path for route in app.routes]
        print(f"✅ App has {len(app_routes)} routes")
        
        # Check API routes are included
        assert any("/api/v1" in path for path in app_routes)
        print("✅ API v1 routes included in app")
        
        print("✅ Main application test PASSED")
    except Exception as e:
        print(f"❌ Main application test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Import Test
    print("\n📦 Test 5: Package Imports")
    try:
        from app.api.v1 import api_router, health, events
        
        print("✅ All modules importable from app.api.v1")
        print("✅ Package imports test PASSED")
    except Exception as e:
        print(f"❌ Package imports test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✨ ALL TESTS PASSED! Phase 4 (Partial) is working! ✨")
    print("=" * 60)
    print("\n📝 Note: This is a partial test for Phase 4.")
    print("   Full implementation requires:")
    print("   - Query routes (with services)")
    print("   - Session routes")
    print("   - Product routes")
    print("   - Memory & file routes")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
