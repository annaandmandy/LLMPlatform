"""
Product-related schemas.

Contains schemas for product search and recommendations.
"""

from pydantic import Field
from typing import Optional, List
from app.schemas.base import AppBaseModel


class ProductSearchRequest(AppBaseModel):
    """Request for product search."""
    query: str = Field(..., description="Search query")
    max_results: int = Field(10, description="Maximum number of results")
    user_id: Optional[str] = Field(None, description="User identifier for personalization")


class Product(AppBaseModel):
    """Individual product information."""
    title: str = Field(..., description="Product title")
    description: str = Field(..., description="Product description")
    image_url: Optional[str] = Field(None, description="Product image URL")
    price: Optional[str] = Field(None, description="Product price")
    rating: Optional[float] = Field(None, description="Product rating")
    url: str = Field(..., description="Product page URL")
    source: Optional[str] = Field(None, description="Data source")


class ProductSearchResponse(AppBaseModel):
    """Response for product search."""
    products: List[Product] = Field(default_factory=list, description="List of products")
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original query")
