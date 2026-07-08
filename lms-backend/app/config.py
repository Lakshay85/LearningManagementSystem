import os
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

    # RabbitMQ Configuration
    RABBITMQ_URL: str = "amqp://lms_user:lms_password@localhost:5672/lms_vhost"

    # Server Configuration
    PORT: int = 3000
    NODE_ENV: str = "development"

    # RAG Service Configuration
    RAG_API_URL: str = "http://localhost:3001"
    RAG_API_KEY: str = "lmsragsecretapikey"

    # Storage Configuration
    STORAGE_PROVIDER: str = "local"
    STORAGE_LOCAL_PATH: str = "uploads"
    STORAGE_BASE_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
