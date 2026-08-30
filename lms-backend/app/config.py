import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Database Configuration
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = "root"
    DATABASE_NAME: str = "lms"

    # JWT Configuration
    JWT_ACCESS_SECRET: str = "your-access-secret-change-in-production"
    JWT_REFRESH_SECRET: str = "your-refresh-secret-change-in-production"

    # Server Configuration
    PORT: int = 3000
    NODE_ENV: str = "development"

    # Storage Configuration
    STORAGE_PROVIDER: str = "local"
    STORAGE_LOCAL_PATH: str = "uploads"
    STORAGE_BASE_URL: str = "http://localhost:3000"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost:8080,http://localhost:5174"

    # ==================== LLM Provider Configuration ====================
    LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "qwen/qwen3.8-27b"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    EMBEDDING_PROVIDER: str = "fastembed"
    NVIDIA_API_KEY: Optional[str] = None
    EMBEDDING_MODEL: str = "BAAI/bge-large-en-v1.5"

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    EMBEDDING_DIMENSIONS: int = 1024

    # ==================== RAG Configuration ====================
    CHUNKING_STRATEGY: str = "RECURSIVE"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100
    MIN_CHUNK_SIZE: int = 100
    SENTENCE_OVERLAP: int = 2
    USE_STRUCTURED_PIPELINE: bool = True

    SEARCH_MODE: str = "hybrid"
    TOP_K: int = 10
    ENABLE_RERANKING: bool = True
    RERANK_TOP_K: int = 10

    SIMILARITY_THRESHOLD: float = 0.30
    FALLBACK_SIMILARITY_THRESHOLD: float = 0.20
    MIN_CONTEXT_LENGTH: int = 50
    MIN_QUERY_WORDS_FOR_REFINEMENT: int = 4

    # ==================== Queue & Intent Configuration ====================
    INGESTION_CONCURRENCY: int = 2
    MAX_FILE_SIZE_MB: int = 50

    USE_INTENT_DETECTION: bool = True
    INTENT_CACHE_TTL_MS: int = 300000
    INTENT_CACHE_MAX_SIZE: int = 1000
    INTENT_CONFIDENCE_THRESHOLD: float = 0.7
    MAX_QUERY_LENGTH: int = 5000
    CONVERSATION_HISTORY_SIZE: int = 10

    # Logging
    LOG_LEVEL: str = "info"
    JSON_LOGS: bool = False

    @property
    def async_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
