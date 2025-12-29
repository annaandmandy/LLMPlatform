"""
Base repository providing common database operations.

All repository classes inherit from this to get standard CRUD operations
with consistent error handling and logging.
"""

from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class BaseRepository:
    """
    Base repository class with common database operations.

    Provides standard CRUD methods that all repositories can use,
    ensuring consistent patterns across the codebase.
    """

    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str):
        """
        Initialize repository with database and collection.

        Args:
            db: MongoDB database instance
            collection_name: Name of the collection to work with
        """
        self.db = db
        self.collection_name = collection_name
        self._collection: Optional[AsyncIOMotorCollection] = None

    @property
    def collection(self) -> AsyncIOMotorCollection:
        """Get the MongoDB collection."""
        if self._collection is None:
            self._collection = self.db[self.collection_name]
        return self._collection

    async def create(self, document: Dict[str, Any]) -> str:
        """
        Create a new document.

        Args:
            document: Document data to insert

        Returns:
            str: ID of created document
        """
        result = await self.collection.insert_one(document)
        logger.debug(f"Created document in {self.collection_name}: {result.inserted_id}")
        return str(result.inserted_id)

    async def find_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Find document by ID.

        Args:
            doc_id: Document ID (ObjectId string or custom ID)

        Returns:
            Document dict or None if not found
        """
        try:
            # Try as ObjectId first
            query = {"_id": ObjectId(doc_id)}
        except Exception:
            # Fall back to string ID
            query = {"_id": doc_id}

        doc = await self.collection.find_one(query)
        return doc

    async def find_one(
        self,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find single document matching query.

        Args:
            query: MongoDB query filter
            projection: Optional field projection

        Returns:
            Document dict or None if not found
        """
        return await self.collection.find_one(query, projection)

    async def find_many(
        self,
        query: Dict[str, Any],
        sort: Optional[List[tuple]] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
        projection: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents matching query.

        Args:
            query: MongoDB query filter
            sort: Optional list of (field, direction) tuples
            limit: Maximum number of documents to return
            skip: Number of documents to skip
            projection: Optional field projection

        Returns:
            List of document dicts
        """
        cursor = self.collection.find(query, projection)

        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)

        return await cursor.to_list(length=limit)

    async def update_one(
        self,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """
        Update single document.

        Args:
            query: MongoDB query filter
            update: Update operations (must include $set, $push, etc.)

        Returns:
            Number of documents modified (0 or 1)
        """
        result = await self.collection.update_one(query, update)
        logger.debug(f"Updated {result.modified_count} document(s) in {self.collection_name}")
        return result.modified_count

    async def update_many(
        self,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """
        Update multiple documents.

        Args:
            query: MongoDB query filter
            update: Update operations

        Returns:
            Number of documents modified
        """
        result = await self.collection.update_many(query, update)
        logger.debug(f"Updated {result.modified_count} document(s) in {self.collection_name}")
        return result.modified_count

    async def delete_one(self, query: Dict[str, Any]) -> int:
        """
        Delete single document.

        Args:
            query: MongoDB query filter

        Returns:
            Number of documents deleted (0 or 1)
        """
        result = await self.collection.delete_one(query)
        logger.debug(f"Deleted {result.deleted_count} document(s) from {self.collection_name}")
        return result.deleted_count

    async def delete_many(self, query: Dict[str, Any]) -> int:
        """
        Delete multiple documents.

        Args:
            query: MongoDB query filter

        Returns:
            Number of documents deleted
        """
        result = await self.collection.delete_many(query)
        logger.debug(f"Deleted {result.deleted_count} document(s) from {self.collection_name}")
        return result.deleted_count

    async def count(self, query: Dict[str, Any]) -> int:
        """
        Count documents matching query.

        Args:
            query: MongoDB query filter

        Returns:
            Number of matching documents
        """
        return await self.collection.count_documents(query)

    async def exists(self, query: Dict[str, Any]) -> bool:
        """
        Check if any document matches query.

        Args:
            query: MongoDB query filter

        Returns:
            True if at least one document matches
        """
        count = await self.collection.count_documents(query, limit=1)
        return count > 0
