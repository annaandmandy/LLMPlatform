"""
Unit tests for FileService.

Tests file management including:
- File uploads
- Metadata storage
- File retrieval
- File deletion
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile
from io import BytesIO

from app.services.file_service import FileService, file_service


@pytest.mark.asyncio
class TestFileService:
    """Test suite for FileService."""

    async def test_upload_file_success(
        self,
        mock_db
    ):
        """Test successful file upload."""
        # Arrange
        file_content = b"Test file content"
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(return_value=file_content)

        user_id = "test_user_123"
        session_id = "test_session_456"

        with patch("app.services.file_service.get_db") as mock_get_db, \
             patch("aiofiles.open") as mock_aio_open, \
             patch("app.services.file_service.settings") as mock_settings:

            mock_settings.UPLOAD_DIR = Path("/tmp/test_uploads")
            mock_get_db.return_value = mock_db

            # Mock async file context manager
            mock_file_handle = AsyncMock()
            mock_file_handle.write = AsyncMock()
            mock_async_ctx = AsyncMock()
            mock_async_ctx.__aenter__.return_value = mock_file_handle
            mock_async_ctx.__aexit__.return_value = None
            mock_aio_open.return_value = mock_async_ctx

            # Mock database insert - already AsyncMock from conftest
            mock_db.files.insert_one.return_value = MagicMock(inserted_id="mock_file_id")

            # Act
            service = FileService()
            result = await service.upload_file(
                file=mock_file,
                user_id=user_id,
                session_id=session_id,
                purpose="attachment"
            )

            # Assert
            assert result["file_id"] == "mock_file_id"
            assert result["filename"] == "test.txt"
            assert result["size_bytes"] == len(file_content)
            assert result["content_type"] == "text/plain"

            # Verify file was written
            mock_file_handle.write.assert_called_once_with(file_content)

            # Verify metadata was saved
            mock_db.files.insert_one.assert_called_once()
            call_args = mock_db.files.insert_one.call_args[0][0]
            assert call_args["user_id"] == user_id
            assert call_args["session_id"] == session_id
            assert call_args["filename"] == "test.txt"
            assert call_args["purpose"] == "attachment"

    async def test_upload_file_without_database(self):
        """Test file upload fails without database."""
        # Arrange
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.txt"

        with patch("app.services.file_service.get_db") as mock_get_db:
            mock_get_db.return_value = None

            # Act & Assert
            service = FileService()
            with pytest.raises(RuntimeError, match="Database not initialized"):
                await service.upload_file(
                    file=mock_file,
                    user_id="test_user",
                    purpose="attachment"
                )

    async def test_get_file_metadata_success(
        self,
        mock_db
    ):
        """Test retrieving file metadata."""
        # Arrange
        file_id = "507f1f77bcf86cd799439011"  # Valid ObjectId format
        file_metadata = {
            "_id": file_id,
            "user_id": "test_user_123",
            "filename": "test.txt",
            "size_bytes": 1024,
            "created_at": "2025-12-29T10:00:00"
        }

        with patch("app.services.file_service.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db
            mock_db.files.find_one.return_value = file_metadata

            # Act
            service = FileService()
            result = await service.get_file_metadata(file_id)

            # Assert
            assert result is not None
            assert result["_id"] == file_id
            assert result["filename"] == "test.txt"

    async def test_get_file_metadata_not_found(
        self,
        mock_db
    ):
        """Test retrieving non-existent file metadata."""
        # Arrange
        with patch("app.services.file_service.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db
            mock_db.files.find_one.return_value = None

            # Act
            service = FileService()
            result = await service.get_file_metadata("507f1f77bcf86cd799439011")

            # Assert
            assert result is None

    async def test_list_files_with_user_filter(
        self,
        mock_db
    ):
        """Test listing files filtered by user_id."""
        # Arrange
        user_id = "test_user_123"
        files_data = [
            {"_id": "id1", "filename": "file1.txt", "user_id": user_id},
            {"_id": "id2", "filename": "file2.txt", "user_id": user_id}
        ]

        with patch("app.services.file_service.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db

            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.limit.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=files_data)
            mock_db.files.find.return_value = mock_cursor

            # Act
            service = FileService()
            result = await service.list_files(user_id=user_id)

            # Assert
            assert len(result) == 2
            assert all(f["user_id"] == user_id for f in result)

            # Verify query
            mock_db.files.find.assert_called_once_with({"user_id": user_id})

    async def test_list_files_with_session_filter(
        self,
        mock_db
    ):
        """Test listing files filtered by session_id."""
        # Arrange
        session_id = "test_session_456"

        with patch("app.services.file_service.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db

            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.limit.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=[])
            mock_db.files.find.return_value = mock_cursor

            # Act
            service = FileService()
            await service.list_files(session_id=session_id)

            # Assert
            call_args = mock_db.files.find.call_args[0][0]
            assert call_args["session_id"] == session_id

    async def test_list_files_with_multiple_filters(
        self,
        mock_db
    ):
        """Test listing files with both user_id and session_id filters."""
        # Arrange
        user_id = "test_user_123"
        session_id = "test_session_456"

        with patch("app.services.file_service.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db

            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.limit.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=[])
            mock_db.files.find.return_value = mock_cursor

            # Act
            service = FileService()
            await service.list_files(user_id=user_id, session_id=session_id)

            # Assert
            call_args = mock_db.files.find.call_args[0][0]
            assert call_args["user_id"] == user_id
            assert call_args["session_id"] == session_id

    async def test_delete_file_success(
        self,
        mock_db
    ):
        """Test successful file deletion."""
        # Arrange
        file_id = "507f1f77bcf86cd799439011"
        file_metadata = {
            "_id": file_id,
            "filename": "test.txt",
            "file_path": "/tmp/test_uploads/test.txt",
            "user_id": "test_user_123"
        }

        with patch("app.services.file_service.get_db") as mock_get_db, \
             patch("pathlib.Path.exists") as mock_exists, \
             patch("pathlib.Path.unlink") as mock_unlink:

            mock_get_db.return_value = mock_db
            mock_db.files.find_one.return_value = file_metadata
            mock_db.files.delete_one.return_value = MagicMock(deleted_count=1)
            mock_exists.return_value = True

            # Act
            service = FileService()
            result = await service.delete_file(file_id)

            # Assert
            assert result is True
            mock_db.files.delete_one.assert_called_once()
            mock_unlink.assert_called_once()

    async def test_delete_file_with_user_verification(
        self,
        mock_db
    ):
        """Test file deletion with user_id verification."""
        # Arrange
        file_id = "507f1f77bcf86cd799439011"
        user_id = "test_user_123"

        with patch("app.services.file_service.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db
            mock_db.files.find_one.return_value = None

            # Act
            service = FileService()
            result = await service.delete_file(file_id, user_id=user_id)

            # Assert
            assert result is False

            # Verify query included user_id
            from bson import ObjectId
            call_args = mock_db.files.find_one.call_args[0][0]
            assert call_args["user_id"] == user_id

    async def test_delete_file_not_found(
        self,
        mock_db
    ):
        """Test deleting non-existent file."""
        # Arrange
        with patch("app.services.file_service.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db
            mock_db.files.find_one.return_value = None

            # Act
            service = FileService()
            result = await service.delete_file("507f1f77bcf86cd799439011")

            # Assert
            assert result is False

    async def test_delete_file_missing_from_disk(
        self,
        mock_db
    ):
        """Test deleting file that's missing from disk."""
        # Arrange
        file_id = "507f1f77bcf86cd799439011"
        file_metadata = {
            "_id": file_id,
            "filename": "test.txt",
            "file_path": "/tmp/test_uploads/nonexistent.txt",
            "user_id": "test_user_123"
        }

        with patch("app.services.file_service.get_db") as mock_get_db, \
             patch("pathlib.Path.exists") as mock_exists:

            mock_get_db.return_value = mock_db
            mock_db.files.find_one.return_value = file_metadata
            mock_db.files.delete_one.return_value = MagicMock(deleted_count=1)
            mock_exists.return_value = False

            # Act
            service = FileService()
            result = await service.delete_file(file_id)

            # Assert
            assert result is True  # Should still return True (metadata deleted)
            mock_db.files.delete_one.assert_called_once()

    def test_get_file_path(self):
        """Test getting file path."""
        # Arrange
        with patch("app.services.file_service.settings") as mock_settings:
            mock_settings.UPLOAD_DIR = Path("/tmp/uploads")
            service = FileService()

            # Act
            path = service.get_file_path("test_file.txt")

            # Assert
            assert isinstance(path, Path)
            assert path.name == "test_file.txt"
