"""
Repository layer for data access.

Provides a clean abstraction over MongoDB operations, making it easier to:
- Test services in isolation
- Switch databases if needed
- Maintain consistent data access patterns
- Share common query logic across services
"""

from app.db.repositories.base import BaseRepository
from app.db.repositories.query_repo import QueryRepository
from app.db.repositories.session_repo import SessionRepository
from app.db.repositories.product_repo import ProductRepository
from app.db.repositories.file_repo import FileRepository
from app.db.repositories.summary_repo import SummaryRepository

__all__ = [
    "BaseRepository",
    "QueryRepository",
    "SessionRepository",
    "ProductRepository",
    "FileRepository",
    "SummaryRepository",
]
