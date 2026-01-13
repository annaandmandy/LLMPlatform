"""
Web Scraper Tool.

Uses Firecrawl to scrape web pages and stores content for RAG.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Try/Except import to avoid hard crash if dependency missing
try:
    from firecrawl import FirecrawlApp
except ImportError:
    FirecrawlApp = None

from app.core.config import settings
from app.db.mongodb import get_db

logger = logging.getLogger(__name__)

class WebScraperTool:
    """Tool for scraping web pages."""
    
    def __init__(self, db=None):
        self.db = db
        self.api_key = settings.FIRECRAWL_API_KEY
        self.app = FirecrawlApp(api_key=self.api_key) if (self.api_key and FirecrawlApp) else None

    async def scrape(self, url: str) -> Dict[str, Any]:
        """
        Scrape a URL and return markdown content.
        Persists result to 'scraped_contents' collection.
        """
        if not self.app:
            return {"error": "Firecrawl API key not configured or library missing."}
            
        logger.info(f"🕸️ Scraping URL: {url}")
        
        try:
            # Firecrawl synchronous sync_scrape_url (wrapper might need async handling or run_in_executor)
            # Assuming library is blocking, we might want to offload. 
            # For prototype, calling directly.
            result = self.app.scrape_url(url, params={"pageOptions": {"onlyMainContent": True}})
            
            if not result or 'markdown' not in result:
                return {"error": "Failed to retrieve content"}
                
            markdown_content = result.get('markdown', '')
            metadata = result.get('metadata', {})
            
            # Save to MongoDB
            if self.db:
                collection = self.db["scraped_contents"]
                doc = {
                    "url": url,
                    "content": markdown_content,
                    "title": metadata.get('title'),
                    "scraped_at": datetime.utcnow().isoformat(),
                    "metadata": metadata
                }
                await collection.insert_one(doc)
            
            return {
                "content": markdown_content[:5000], # Truncate for context window if needed, or return all
                "title": metadata.get('title'),
                "url": url
            }
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            return {"error": str(e)}

# Wrapper for LangGraph tool usage
async def scrape_web(url: str) -> str:
    """
    Scrape a website and return its content.
    """
    from app.db.mongodb import get_db
    db = get_db()
    
    scraper = WebScraperTool(db=db)
    result = await scraper.scrape(url)
    
    if "error" in result:
        return f"Error scraping {url}: {result['error']}"
        
    return f"Source: {result.get('title', url)}\nURL: {result.get('url')}\n\n{result.get('content')}"
