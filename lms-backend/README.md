# LMS Core Backend (Python/FastAPI)

This is the core backend API for the Learning Management System, built with **Python 3.12** and **FastAPI**.

## Features

- **Authentication**: JWT-based auth with access and refresh tokens.
- **Role-Based Access Control**: Admins, Faculty, Students, and Parents.
- **Course & Syllabus Management**: Sections, content links (videos, documents, assignments).
- **Media Uploads**: Local storage system for uploaded videos and documents.
- **AI Teaching Assistant & RAG Engine**: Structure-aware parsing, pgvector cosine search, intent classification, and SSE streaming token generation.
- **In-Process Event Dispatcher**: Asynchronous event dispatching for notifications and SSE client streams without external broker dependencies.
- **Asynchronous Database Queries**: Powered by SQLAlchemy async engines and Asyncpg with pgvector extension.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL 16 + pgvector (SQLAlchemy async)
- **AI & RAG**: Groq (`qwen/qwen3.8-27b`), FastEmbed (`BAAI/bge-large-en-v1.5`), LangChain
- **Validation**: Pydantic v2
- **Testing**: pytest & pytest-asyncio

---

## Directory Structure

```
lms-backend/
├── app/
│   ├── auth/           # Authentication routes & JWT strategies
│   ├── chat/           # Chat session & message persistence
│   ├── courses/        # Course and syllabus routers & schemas
│   ├── documents/      # Document management & file routers
│   ├── health/         # API Healthcheck endpoint
│   ├── ingestion/      # Ingestion queue & background jobs
│   ├── intent/         # LLM intent detector & response generator
│   ├── llm/            # LLM & embedding provider adapters
│   ├── messaging/      # In-process asynchronous event dispatcher
│   ├── models/         # SQLAlchemy models (LMS & RAG)
│   ├── notifications/  # Notification services, consumers & SSE
│   ├── rag/            # Full RAG pipeline, structure parser, vector retrieval
│   ├── storage/        # File storage provider
│   ├── users/          # Profile management
│   ├── videos/         # Video routers, streaming & uploads
│   ├── config.py       # Pydantic Settings
│   ├── database.py     # SQLAlchemy connection session helper
│   ├── database_init.py# Automatic pgvector & index initializer
│   └── main.py         # Application entrypoint & lifespan
├── tests/              # Python test suite
├── Dockerfile          # Production Dockerfile
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## Running the Application

### 1. Prerequisites
- Python 3.11+
- PostgreSQL with pgvector (run via the root `docker-compose.yml`)

### 2. Configure Environment
Create a `.env` file in the root of `lms-backend/` based on `.env.example`:
```env
PORT=3000
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=root
DATABASE_NAME=lms
JWT_ACCESS_SECRET=your-jwt-access-secret
JWT_REFRESH_SECRET=your-jwt-refresh-secret
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=qwen/qwen3.8-27b
EMBEDDING_PROVIDER=fastembed
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
EMBEDDING_DIMENSIONS=1024
```

### 3. Run Locally (Dev)
```bash
# Install dependencies
pip install -r requirements.txt

# Start FastAPI development server
python -m uvicorn app.main:app --port 3000 --reload
```

---

## Testing

Run tests with `pytest` inside the `lms-backend` directory:
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=app
```
