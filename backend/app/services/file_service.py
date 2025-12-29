"""
File Service - Business logic for file management.

Handles file uploads, storage, and metadata management.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import logging
import os
import aiofiles

from fastapi import UploadFile
from app.db.mongodb import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)


class FileService:
    """
    Service for managing file uploads and metadata.
    
    Handles:
    - File upload to disk
    - Metadata storage in MongoDB
    - File retrieval and deletion
    """
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(
        self,
        file: UploadFile,
        user_id: str,
        session_id: Optional[str] = None,
        purpose: str = "attachment"
    ) -> Dict[str, Any]:
        """
        Upload a file and store metadata.
        
        Args:
            file: UploadFile from FastAPI
            user_id: User who uploaded the file
            session_id: Optional session ID
            purpose: Purpose of the file (e.g., "attachment", "profile_picture")
            
        Returns:
            Dict with file metadata including file_id and path
        """
        db = get_db()
        if db is None:
            raise RuntimeError("Database not initialized")
        
        files_collection = db["files"]
        
        try:
            # Generate unique filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{user_id}_{timestamp}_{file.filename}"
            file_path = self.upload_dir / filename
            
            # Save file to disk
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            file_size = len(content)
            
            # Store metadata in database
            file_metadata = {
                "user_id": user_id,
                "session_id": session_id,
                "filename": file.filename,
                "stored_filename": filename,
                "file_path": str(file_path),
                "content_type": file.content_type,
                "size_bytes": file_size,
                "purpose": purpose,
                "created_at": datetime.utcnow().isoformat(),
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            result = await files_collection.insert_one(file_metadata)
            file_id = str(result.inserted_id)
            
            logger.info(f"File uploaded: {filename} ({file_size} bytes) for {user_id}")
            
            return {
                "file_id": file_id,
                "filename": file.filename,
                "size_bytes": file_size,
                "content_type": file.content_type,
                "path": str(file_path),
                "created_at": file_metadata["created_at"]
            }
            
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            # Cleanup file if metadata save failed
            if file_path.exists():
                file_path.unlink()
            raise
    
    async def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata by ID.
        
        Args:
            file_id: MongoDB ObjectId of the file
            
        Returns:
            File metadata dict or None if not found
        """
        from bson import ObjectId
        
        db = get_db()
        if db is None:
            raise RuntimeError("Database not initialized")
        
        files_collection = db["files"]
        
        try:
            file_doc = await files_collection.find_one({"_id": ObjectId(file_id)})
            
            if file_doc:
                file_doc["_id"] = str(file_doc["_id"])
                return file_doc
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get file metadata: {e}")
            return None
    
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
            List of file metadata dicts
        """
        db = get_db()
        if db is None:
            raise RuntimeError("Database not initialized")
        
        files_collection = db["files"]
        
        # Build query
        query = {}
        if user_id:
            query["user_id"] = user_id
        if session_id:
            query["session_id"] = session_id
        
        # Fetch files
        cursor = files_collection.find(query).sort("created_at", -1).limit(limit)
        files = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for file_doc in files:
            file_doc["_id"] = str(file_doc["_id"])
        
        return files
    
    async def delete_file(self, file_id: str, user_id: Optional[str] = None) -> bool:
        """
        Delete a file and its metadata.
        
        Args:
            file_id: MongoDB ObjectId of the file
            user_id: Optional user ID for verification
            
        Returns:
            True if deleted, False if not found
        """
        from bson import ObjectId
        
        db = get_db()
        if db is None:
            raise RuntimeError("Database not initialized")
        
        files_collection = db["files"]
        
        try:
            # Build query
            query = {"_id": ObjectId(file_id)}
            if user_id:
                query["user_id"] = user_id
            
            # Get file metadata first
            file_doc = await files_collection.find_one(query)
            
            if not file_doc:
                logger.warning(f"File not found: {file_id}")
                return False
            
            # Delete from database
            await files_collection.delete_one(query)
            
            # Delete from disk
            file_path = Path(file_doc["file_path"])
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted: {file_doc['filename']}")
            else:
                logger.warning(f"File not found on disk: {file_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            raise
    
    def get_file_path(self, stored_filename: str) -> Path:
        """
        Get the full path to a stored file.
        
        Args:
            stored_filename: The stored filename
            
        Returns:
            Path object to the file
        """
        return self.upload_dir / stored_filename


# Global instance
file_service = FileService()
