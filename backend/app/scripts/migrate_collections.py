"""
Database Migration Script: Consolidate Collections

This script:
1. Migrates vectors into queries collection (adds embedding field)
2. Drops events collection (data is in sessions)
3. Drops agent_logs collection (too large, not needed)
4. Drops vectors collection (consolidated into queries)

Run with: python -m app.scripts.migrate_collections
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db.mongodb import connect_db, close_db, get_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_vectors_to_queries():
    """Migrate vector embeddings into queries collection."""
    db = get_db()
    
    queries_collection = db["queries"]
    vectors_collection = db["vectors"]
    
    # Get all vectors
    vectors_cursor = vectors_collection.find({})
    vectors = await vectors_cursor.to_list(length=None)
    
    logger.info(f"Found {len(vectors)} vectors to migrate")
    
    migrated = 0
    skipped = 0
    
    for vector_doc in vectors:
        # Match vector to query by content or query_id
        query_id = vector_doc.get("query_id")
        content = vector_doc.get("content", "")
        embedding = vector_doc.get("embedding", [])
        
        if not embedding:
            skipped += 1
            continue
        
        # Find matching query
        if query_id:
            query_filter = {"_id": query_id}
        else:
            # Try to match by content
            query_filter = {"query": content}
        
        # Update query with embedding
        result = await queries_collection.update_one(
            query_filter,
            {"$set": {"embedding": embedding}}
        )
        
        if result.modified_count > 0:
            migrated += 1
        else:
            skipped += 1
    
    logger.info(f"✅ Migrated {migrated} embeddings")
    logger.info(f"⚠️  Skipped {skipped} vectors (no matching query)")
    
    return migrated, skipped


async def drop_collections():
    """Drop deprecated collections."""
    db = get_db()
    
    collections_to_drop = ["events", "agent_logs", "vectors"]
    
    for collection_name in collections_to_drop:
        try:
            # Get count before dropping
            collection = db[collection_name]
            count = await collection.count_documents({})
            
            # Drop collection
            await db.drop_collection(collection_name)
            logger.info(f"✅ Dropped collection '{collection_name}' ({count} documents)")
            
        except Exception as e:
            logger.error(f"❌ Error dropping {collection_name}: {e}")


async def create_vector_index_instructions():
    """Print instructions for creating vector index in Atlas UI."""
    
    instructions = """
    
    ╔══════════════════════════════════════════════════════════════╗
    ║  📝 MongoDB Atlas Vector Search Index Setup Instructions     ║
    ╚══════════════════════════════════════════════════════════════╝
    
    1. Go to MongoDB Atlas UI (cloud.mongodb.com)
    2. Navigate to your cluster → Browse Collections
    3. Select database: LLMPlatform
    4. Select collection: queries
    5. Go to "Search Indexes" tab
    6. Click "Create Search Index"
    7. Choose "Atlas Vector Search"
    8. Use this configuration:
    
    Index Name: vector_index
    
    JSON Configuration:
    {
      "fields": [
        {
          "type": "vector",
          "path": "embedding",
          "numDimensions": 1536,
          "similarity": "cosine"
        }
      ]
    }
    
    9. Click "Create Search Index"
    10. Wait for index to build (usually 1-2 minutes)
    
    ✅ After setup, vector search will work automatically!
    
    Test with:
        python -m app.scripts.test_vector_search
    
    ════════════════════════════════════════════════════════════════
    """
    
    print(instructions)


async def main():
    """Run migration."""
    
    print("=" * 60)
    print("🔄 Database Collection Migration")
    print("=" * 60)
    
    # Connect to database
    await connect_db()
    
    # Step 1: Migrate vectors
    print("\n📦 Step 1: Migrating vectors to queries...")
    try:
        migrated, skipped = await migrate_vectors_to_queries()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False
    
    # Step 2: Drop old collections
    print("\n🗑️  Step 2: Dropping deprecated collections...")
    await drop_collections()
    
    # Step 3: Print Vector Search setup instructions
    print("\n🔍 Step 3: Vector Search Setup")
    await create_vector_index_instructions()
    
    # Close connection
    await close_db()
    
    print("\n" + "=" * 60)
    print("✨ Migration Complete!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - Migrated {migrated} embeddings to queries")
    print(f"  - Dropped 3 collections (events, agent_logs, vectors)")
    print(f"  - Next: Set up vector index in Atlas UI (see above)")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
