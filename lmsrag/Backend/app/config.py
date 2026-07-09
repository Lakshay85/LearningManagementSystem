import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # App
    PORT: int = 3001
    NODE_ENV: str = "development"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5434/lmsrag"

    # Security
    RAG_API_KEY: str = "lmsragsecretapikey"
    JWT_ACCESS_SECRET: str = "your-access-secret-change-in-production" # to verify LMS tokens

    # LLM Config
    LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    EMBEDDING_PROVIDER: str = "nvidia"
    NVIDIA_API_KEY: Optional[str] = None
    EMBEDDING_MODEL: str = "baai/bge-m3"

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    EMBEDDING_DIMENSIONS: int = 3072

    # RAG Config
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

    # Queue Config
    INGESTION_CONCURRENCY: int = 2
    MAX_FILE_SIZE_MB: int = 50

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3001,http://localhost:8080"

    # Infrastructure
    RABBITMQ_URL: str = "amqp://lms_user:lms_password@localhost:5672/lms_vhost"

    # Intent Detection
    USE_INTENT_DETECTION: bool = True
    INTENT_CACHE_TTL_MS: int = 300000
    INTENT_CACHE_MAX_SIZE: int = 1000
    INTENT_CONFIDENCE_THRESHOLD: float = 0.7
    MAX_QUERY_LENGTH: int = 5000
    CONVERSATION_HISTORY_SIZE: int = 10

    # Logging
    LOG_LEVEL: str = "info"
    JSON_LOGS: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
