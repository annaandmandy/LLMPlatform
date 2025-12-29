"""
Product search endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime

from app.schemas.product import ProductSearchRequest, Product, ProductSearchResponse
from app.db.mongodb import get_db

router = APIRouter(prefix="/search/products", tags=["products"])


@router.post("/", response_model=ProductSearchResponse)
async def search_products(request: ProductSearchRequest):
    """
    Search for products.
    
    This endpoint searches the products collection for matching items.
    Can be enhanced with external API calls (Amazon, etc.) in the future.
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    products_collection = db["products"]
    
    # Build search query
    search_query = {}
    
    # Text search on title and description if query provided
    if request.query:
        search_query["$text"] = {"$search": request.query}
    
    # Category filter if provided
    if request.category:
        search_query["category"] = request.category
    
    # Price range filter
    if request.min_price is not None or request.max_price is not None:
        price_filter = {}
        if request.min_price is not None:
            price_filter["$gte"] = request.min_price
        if request.max_price is not None:
            price_filter["$lte"] = request.max_price
        search_query["price_numeric"] = price_filter
    
    # Execute search with limit
    cursor = products_collection.find(search_query).limit(request.limit or 10)
    product_docs = await cursor.to_list(length=request.limit or 10)
    
    # Convert to Product models
    products = []
    for doc in product_docs:
        products.append(Product(
            title=doc.get("title", ""),
            description=doc.get("description", ""),
            price=doc.get("price", ""),
            url=doc.get("url", ""),
            image_url=doc.get("image_url"),
            rating=doc.get("rating"),
            category=doc.get("category"),
            availability=doc.get("availability")
        ))
    
    return ProductSearchResponse(
        query=request.query,
        products=products,
        count=len(products)
    )


@router.get("/{product_id}")
async def get_product(product_id: str):
    """
    Get a specific product by ID.
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    products_collection = db["products"]
    
    # Find product
    product = await products_collection.find_one({"_id": product_id})
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Remove MongoDB _id
    product.pop("_id", None)
    
    return product
