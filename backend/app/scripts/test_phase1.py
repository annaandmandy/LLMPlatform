"""
Test script to verify Phase 1 implementation (Config + DB).

Run this to test:
    python -m app.scripts.test_phase1
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def main():
    print("=" * 60)
    print("🧪 Testing Phase 1: Configuration & Database")
    print("=" * 60)
    
    # Test 1: Configuration
    print("\n📋 Test 1: Configuration Loading")
    try:
        from app.core.config import settings, get_available_providers
        
        print(f"✅ App Name: {settings.APP_NAME}")
        print(f"✅ Version: {settings.APP_VERSION}")
        print(f"✅ Environment: {settings.ENVIRONMENT}")
        print(f"✅ Database: {settings.MONGO_DB}")
        print(f"✅ Upload Dir: {settings.UPLOAD_DIR}")
        print(f"✅ Max Retrieval: {settings.MAX_RETRIEVAL_RESULTS}")
        
        providers = get_available_providers()
        print(f"✅ Available Providers: {providers}")
        
        print("✅ Configuration test PASSED")
    except Exception as e:
        print(f"❌ Configuration test FAILED: {e}")
        return False
    
    # Test 2: Database Connection
    print("\n💾 Test 2: Database Connection")
    try:
        from app.db.mongodb import connect_db, check_connection, get_db_stats, close_db
        
        # Connect
        print("Connecting to MongoDB...")
        db = await connect_db()
        print(f"✅ Connected to database: {db.name}")
        
        # Check connection
        is_connected = await check_connection()
        print(f"✅ Connection healthy: {is_connected}")
        
        # Get stats
        stats = await get_db_stats()
        print(f"✅ Database stats:")
        for coll, count in stats.get("collections", {}).items():
            print(f"   - {coll}: {count} documents")
        
        # Close
        await close_db()
        print("✅ Connection closed")
        
        print("✅ Database test PASSED")
    except Exception as e:
        print(f"❌ Database test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Startup Event
    print("\n🚀 Test 3: Startup Event")
    try:
        from app.core.events import startup_event, shutdown_event
        
        print("Running startup event...")
        await startup_event()
        print("✅ Startup event completed")
        
        print("Running shutdown event...")
        await shutdown_event()
        print("✅ Shutdown event completed")
        
        print("✅ Events test PASSED")
    except Exception as e:
        print(f"❌ Events test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Health Check
    print("\n🏥 Test 4: Health Check")
    try:
        from app.core.events import health_check
        from app.db.mongodb import connect_db
        
        # Reconnect for health check
        await connect_db()
        
        health = await health_check()
        print(f"✅ Health Status: {health['status']}")
        print(f"✅ DB Connected: {health['database']['connected']}")
        print(f"✅ Providers Available: {health['providers']['count']}")
        print(f"✅ Agents Initialized: {health['agents']['initialized']}")
        
        from app.db.mongodb import close_db
        await close_db()
        
        print("✅ Health check test PASSED")
    except Exception as e:
        print(f"❌ Health check test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✨ ALL TESTS PASSED! Phase 1 is working correctly! ✨")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
