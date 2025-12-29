"""
Repository for file-related database operations.

Handles storage and retrieval of file metadata, including:
- File metadata storage
- File listing and search
- File deletion
"""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from app.db.repositories.base import BaseRepository


class FileRepository(BaseRepository):
    """Repository for managing file metadata documents in MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize with files collection."""
        super().__init__(db, "files")

    async def create_file_metadata(
        self,
        user_id: str,
        filename: str,
        stored_filename: str,
        file_path: str,
        content_type: str,
        size_bytes: int,
        session_id: Optional[str] = None,
        purpose: str = "attachment"
    ) -> str:
        """
        Store file metadata.

        Args:
            user_id: User who uploaded the file
            filename: Original filename
            stored_filename: Filename as stored on disk
            file_path: Full path to the file
            content_type: MIME type
            size_bytes: File size in bytes
            session_id: Optional session identifier
            purpose: Purpose of the file

        Returns:
            ID of created file metadata document
        """
        document = {
            "user_id": user_id,
            "session_id": session_id,
            "filename": filename,
            "stored_filename": stored_filename,
            "file_path": file_path,
            "content_type": content_type,
            "size_bytes": size_bytes,
            "purpose": purpose,
            "created_at": datetime.utcnow().isoformat(),
            "timestamp": datetime.utcnow().isoformat(),
        }

        return await self.create(document)

    async def get_file_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata by ID.

        Args:
            file_id: File document ID

        Returns:
            File metadata dict or None if not found
        """
        return await self.find_by_id(file_id)

    async def list_files(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List files with optional filters.

        Args:
            user_id: Filter by user ID
            session_id: Filter by session ID
            limit: Maximum number of files to return

        Returns:
            List of file metadata documents
        """
        query = {}
        if user_id:
            query["user_id"] = user_id
        if session_id:
            query["session_id"] = session_id

        return await self.find_many(
            query=query,
            sort=[("created_at", -1)],
            limit=limit
        )

    async def delete_file_metadata(
        self,
        file_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Delete file metadata and return the deleted document.

        Args:
            file_id: File document ID
            user_id: Optional user ID for verification

        Returns:
            Deleted file document or None if not found
        """
        from bson import ObjectId

        # Build query
        try:
            query = {"_id": ObjectId(file_id)}
        except Exception:
            query = {"_id": file_id}

        if user_id:
            query["user_id"] = user_id

        # Get file metadata first
        file_doc = await self.find_one(query)

        if not file_doc:
            return None

        # Delete from database
        await self.delete_one(query)

        return file_doc

    async def count_user_files(self, user_id: str) -> int:
        """
        Count total files for a user.

        Args:
            user_id: User identifier

        Returns:
            Number of files
        """
        return await self.count({"user_id": user_id})
