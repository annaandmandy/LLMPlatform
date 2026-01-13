"""
File Search Tool.

Handles parsing, chunking, and searching of uploaded files (RAG).
"""

import logging
import io
from typing import Dict, Any, List
from datetime import datetime

# Optional imports
try:
    import pypdf
except ImportError:
    pypdf = None

from app.db.mongodb import get_db
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

class FileSearchTool:
    """Tool for RAG over files."""
    
    def __init__(self, db=None):
        self.db = db

    async def ingest_file(self, file_id: str, file_path: str, mime_type: str):
        """
        Parse and index a file.
        """
        if not self.db:
             raise RuntimeError("DB connection required for ingestion")
             
        collection = self.db["file_chunks"]
        
        # 1. Parse Text
        text = self._parse_file(file_path, mime_type)
        if not text:
            logger.warning(f"No text extracted from {file_id}")
            return
            
        # 2. Chunk Text
        chunks = self._chunk_text(text)
        
        # 3. Embed and Store
        for i, chunk in enumerate(chunks):
            embedding = await embedding_service.generate_embedding(chunk)
            
            doc = {
                "file_id": file_id,
                "chunk_index": i,
                "text": chunk,
                "embedding": embedding,
                "created_at": datetime.utcnow().isoformat()
            }
            await collection.insert_one(doc)
            
        # Update file status
        await self.db["files"].update_one(
            {"_id": file_id}, # Note: ensure ID type (ObjectId vs str) matches. Files.py casted to str, but update needs logic.
            {"$set": {"processed": True}}
        )
        
        logger.info(f"Ingested file {file_id}: {len(chunks)} chunks")

    def _parse_file(self, path: str, mime_type: str) -> str:
        """Extract text based on file type."""
        try:
            with open(path, "rb") as f:
                if "pdf" in mime_type and pypdf:
                    reader = pypdf.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text
                else:
                    # Fallback to plain text decoding
                    return f.read().decode("utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Parsing failed for {path}: {e}")
            return ""

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Simple overlap chunking."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - overlap
        return chunks

    async def search(self, query: str, limit: int = 4) -> List[str]:
        """
        Vector search over file chunks.
        Note: Requires Atlas Vector Search Index on 'file_chunks'.
        """
        if not self.db:
            return []
            
        embedding = await embedding_service.generate_embedding(query)
        collection = self.db["file_chunks"]
        
        # Atlas Vector Search Pipeline
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index", # User needs to create this
                    "path": "embedding",
                    "queryVector": embedding,
                    "numCandidates": limit * 10,
                    "limit": limit
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "text": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        
        try:
            results = await collection.aggregate(pipeline).to_list(length=limit)
            return [r["text"] for r in results]
        except Exception as e:
            logger.error(f"Vector search failed (Index might be missing): {e}")
            # Fallback: regex search (slow, bad) or empty
            return []

# Wrapper
async def search_files(query: str) -> str:
    from app.db.mongodb import get_db
    db = get_db()
    tool = FileSearchTool(db=db)
    results = await tool.search(query)
    
    if not results:
        return "No relevant information found in files."
        
    return "\n\n".join(results)
