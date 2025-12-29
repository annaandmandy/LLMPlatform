"""
File upload and management endpoints.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
from datetime import datetime
import os
from pathlib import Path

from app.db.mongodb import get_db
from app.core.config import settings

router = APIRouter(prefix="/files", tags=["files"])

# Upload directory
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = None
):
    """
    Upload a file for processing.
    
    Saves file to disk and creates metadata record in database.
    Can be used for RAG, image processing, etc.
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    files_collection = db["files"]
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename
    
    try:
        # Save file to disk
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Create metadata record
        file_doc = {
            "user_id": user_id,
            "filename": file.filename,
            "stored_filename": safe_filename,
            "path": str(file_path),
            "size": len(contents),
            "mime_type": file.content_type,
            "uploaded_at": datetime.utcnow().isoformat(),
            "processed": False
        }
        
        result = await files_collection.insert_one(file_doc)
        file_id = str(result.inserted_id)
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "size": len(contents),
            "mime_type": file.content_type,
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        # Clean up file if database insert fails
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/")
async def list_files(user_id: str = None, limit: int = 50):
    """
    List uploaded files.
    
    Args:
        user_id: Optional user filter
        limit: Maximum files to return
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    files_collection = db["files"]
    
    # Build query
    query = {}
    if user_id:
        query["user_id"] = user_id
    
    # Get files
    cursor = files_collection.find(query).sort("uploaded_at", -1).limit(limit)
    files = await cursor.to_list(length=limit)
    
    # Format response
    result = []
    for file_doc in files:
        result.append({
            "file_id": str(file_doc["_id"]),
            "filename": file_doc.get("filename"),
            "size": file_doc.get("size"),
            "mime_type": file_doc.get("mime_type"),
            "uploaded_at": file_doc.get("uploaded_at"),
            "processed": file_doc.get("processed", False)
        })
    
    return {
        "files": result,
        "count": len(result)
    }


@router.get("/{file_id}")
async def get_file_metadata(file_id: str):
    """
    Get file metadata.
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    files_collection = db["files"]
    
    # Find file
    file_doc = await files_collection.find_one({"_id": file_id})
    
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "file_id": str(file_doc["_id"]),
        "filename": file_doc.get("filename"),
        "stored_filename": file_doc.get("stored_filename"),
        "size": file_doc.get("size"),
        "mime_type": file_doc.get("mime_type"),
        "uploaded_at": file_doc.get("uploaded_at"),
        "processed": file_doc.get("processed", False),
        "path": file_doc.get("path")
    }


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """
    Delete a file and its metadata.
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    files_collection = db["files"]
    
    # Find file
    file_doc = await files_collection.find_one({"_id": file_id})
    
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete from disk  
    file_path = Path(file_doc.get("path", ""))
    if file_path.exists():
        os.remove(file_path)
    
    # Delete from database
    await files_collection.delete_one({"_id": file_id})
    
    return {
        "message": "File deleted successfully",
        "file_id": file_id
    }
