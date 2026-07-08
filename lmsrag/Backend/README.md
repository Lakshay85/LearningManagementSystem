# LMS RAG Service (Python/FastAPI)

This is the Retrieval-Augmented Generation (RAG) microservice for the Learning Management System, built with **Python 3.12** and **FastAPI**.

## Features

- **Document Ingestion**: Supports parsing, chunking, and embedding PDFs, text documents, and video transcripts.
- **Asynchronous Processing**: Ingestion jobs are processed out-of-band by an `arq` background worker using Redis as the job store.
- **Structure-Aware Processing**: Uses a custom document structure pipeline that parses documents into structural elements before chunking.
- **pgvector Vector Store**: Leverages PostgreSQL `pgvector` for HNSW/IVF similarity searches.
- **Dynamic Intent Classifier**: Classifies incoming queries (greeting, gratitude, farewell, out-of-scope, question, follow-up) using LLMs to direct the processing pipeline.
- **Streaming Generation**: Streams responses back to the client in real-time using Server-Sent Events (SSE) via the Groq LLM API.
- **Conversational Memory**: Persists user and assistant messages, and automatically builds summaries for long sessions.

## Tech Stack

- **Framework**: FastAPI
- **LLM Engine**: Groq Cloud API (Llama 3.3 70B model)
- **Embeddings**: default NVIDIA `baai/bge-m3` or Gemini/OpenAI embedding APIs
- **Orchestration**: LangChain (Python)
- **Database**: PostgreSQL with `pgvector` extension
- **Background Worker**: `arq` (async queue) & Redis
- **Testing**: pytest

---

## Directory Structure

```
lmsrag/Backend/
├── app/
│   ├── chat_memory/       # Chat session & message storage services
│   ├── database/          # pgvector connection pool & queries
│   ├── intent_detection/  # Classifier & LLM response generator
│   ├── llm/               # LLM and embedding API providers
│   ├── middleware/        # Authentication & core middlewares
│   ├── queue/             # Arq queue publisher & progress tracker
│   ├── rag/               # Document loaders, splitters, retrievers & SSE services
│   ├── config.py          # Configuration options
│   ├── main.py            # FastAPI main router entrypoint
│   └── worker.py          # Arq job processor entrypoint
├── tests/                 # Python unit tests
├── Dockerfile             # Production Docker container
├── init.sql               # DB schema (tables, vector extensions, HNSW indexes)
└── requirements.txt       # Dependencies
```

---

## Getting Started

### 1. Prerequisites
- Python 3.12+
- Redis (running on port `6379`)
- PostgreSQL with pgvector (running on port `5434`)
- Groq Cloud API Key
- NVIDIA/Gemini/OpenAI API key (for embeddings)

### 2. Configure Environment
Create a `.env` file in `lmsrag/Backend/` based on `.env.example`:
```env
PORT=3001
DATABASE_URL=postgresql://postgres:postgres@localhost:5434/lmsrag
REDIS_URL=redis://localhost:6379
GROQ_API_KEY=your-groq-api-key
NVIDIA_API_KEY=your-nvidia-api-key
EMBEDDING_PROVIDER=nvidia
EMBEDDING_MODEL=baai/bge-m3
```

### 3. Run the Services
You need to run both the API server and the background arq worker:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API Server
python -m uvicorn app.main:app --port 3001 --reload

# In a separate terminal, run the Background Worker
arq app.worker.WorkerSettings
```

---

## Testing

Run unit and integration tests using `pytest`:
```bash
pytest
```
