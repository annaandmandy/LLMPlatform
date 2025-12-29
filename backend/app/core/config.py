"""
Core configuration management using Pydantic Settings.

This module centralizes all environment variables and application settings.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ==================== Application ====================
    APP_NAME: str = "LLM Platform"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # ==================== Server ====================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    # ==================== Database ====================
    MONGODB_URI: str
    MONGO_DB: str = "llm_experiment"
    
    @field_validator("MONGODB_URI")
    @classmethod
    def validate_mongodb_uri(cls, v: str) -> str:
        if not v:
            raise ValueError("MONGODB_URI is required")
        if not v.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("MONGODB_URI must start with mongodb:// or mongodb+srv://")
        return v
    
    # ==================== LLM API Keys ====================
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    
    # ==================== External Services ====================
    SERPAPI_KEY: Optional[str] = None  # For product search
    
    # ==================== File Upload ====================
    UPLOAD_DIR: Path = Path("uploads")
    MAX_FILE_SIZE_MB: float = 10.0
    ALLOWED_MIME_TYPES: str = ""  # Comma-separated, empty = use prefixes
    
    @field_validator("UPLOAD_DIR")
    @classmethod
    def create_upload_dir(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    # ==================== RAG / Embeddings ====================
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 128
    MAX_RETRIEVAL_RESULTS: int = 8
    
    # ==================== Security ====================
    CORS_ORIGINS: list[str] = ["*"]
    ALLOWED_HOSTS: list[str] = ["*"]
    SECRET_KEY: str = "change-me-in-production"  # For JWT, sessions, etc.
    
    # ==================== Rate Limiting ====================
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # ==================== Streaming ====================
    ENABLE_SSE_STREAMING: bool = True
    ENABLE_WEBSOCKET: bool = False
    SSE_RETRY_TIMEOUT: int = 3000  # milliseconds
    
    # ==================== Logging ====================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"  # "text" or "json"
    LOG_FILE: Optional[Path] = Path("logs/app.log")
    
    @field_validator("LOG_FILE")
    @classmethod
    def create_log_dir(cls, v: Optional[Path]) -> Optional[Path]:
        if v:
            v.parent.mkdir(parents=True, exist_ok=True)
        return v
    
    # ==================== Monitoring ====================
    ENABLE_METRICS: bool = False
    METRICS_PORT: int = 9090
    
    # ==================== Agent Configuration ====================
    MEMORY_SUMMARY_INTERVAL: int = 4  # Summarize every N message pairs
    PRODUCT_SEARCH_MAX_RESULTS: int = 1
    
    # ==================== Model Defaults ====================
    DEFAULT_MODEL_PROVIDER: str = "openai"
    DEFAULT_MODEL_NAME: str = "gpt-4o-mini"
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 1024
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env


# Singleton instance
settings = Settings()


# Helper functions
def get_llm_api_key(provider: str) -> Optional[str]:
    """Get API key for a specific LLM provider."""
    key_mapping = {
        "openai": settings.OPENAI_API_KEY,
        "anthropic": settings.ANTHROPIC_API_KEY,
        "google": settings.GOOGLE_API_KEY,
        "openrouter": settings.OPENROUTER_API_KEY,
    }
    return key_mapping.get(provider.lower())


def is_provider_available(provider: str) -> bool:
    """Check if a provider has an API key configured."""
    return get_llm_api_key(provider) is not None


def get_available_providers() -> list[str]:
    """Get list of providers with configured API keys."""
    providers = ["openai", "anthropic", "google", "openrouter"]
    return [p for p in providers if is_provider_available(p)]
