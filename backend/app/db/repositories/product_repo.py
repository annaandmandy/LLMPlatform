"""
Repository for product-related database operations.

Handles storage and retrieval of product data, including:
- Product search and filtering
- Product metadata management
- Product indexing for search
"""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from app.db.repositories.base import BaseRepository


class ProductRepository(BaseRepository):
    """Repository for managing product documents in MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize with products collection."""
        super().__init__(db, "products")

    async def create_product(
        self,
        product_id: str,
        name: str,
        description: str,
        price: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new product.

        Args:
            product_id: Unique product identifier
            name: Product name
            description: Product description
            price: Product price
            metadata: Optional additional product metadata

        Returns:
            ID of created product document
        """
        document = {
            "product_id": product_id,
            "name": name,
            "description": description,
            "price": price,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        if metadata:
            document.update(metadata)

        return await self.create(document)

    async def search_products(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search products by text query.

        Args:
            query: Search query string
            limit: Maximum number of results
            filters: Optional additional filters (price range, category, etc.)

        Returns:
            List of matching product documents
        """
        # Build search query
        search_query = {}

        # Add text search if available
        if query:
            search_query["$text"] = {"$search": query}

        # Add additional filters
        if filters:
            search_query.update(filters)

        return await self.find_many(
            query=search_query,
            limit=limit,
            sort=[("_id", -1)]  # Most recent first
        )

    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get product by ID.

        Args:
            product_id: Product identifier

        Returns:
            Product document or None if not found
        """
        return await self.find_one({"product_id": product_id})

    async def update_product(
        self,
        product_id: str,
        updates: Dict[str, Any]
    ) -> int:
        """
        Update product information.

        Args:
            product_id: Product identifier
            updates: Fields to update

        Returns:
            Number of documents modified
        """
        updates["updated_at"] = datetime.utcnow().isoformat()

        return await self.update_one(
            query={"product_id": product_id},
            update={"$set": updates}
        )

    async def delete_product(self, product_id: str) -> int:
        """
        Delete a product.

        Args:
            product_id: Product identifier

        Returns:
            Number of documents deleted
        """
        return await self.delete_one({"product_id": product_id})

    async def get_products_by_category(
        self,
        category: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get products in a specific category.

        Args:
            category: Product category
            limit: Maximum number of products to return

        Returns:
            List of product documents
        """
        return await self.find_many(
            query={"category": category},
            limit=limit,
            sort=[("name", 1)]  # Alphabetical
        )
