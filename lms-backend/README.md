# LMS Core Backend (Python/FastAPI)

This is the core backend API for the Learning Management System, built with **Python 3.12** and **FastAPI**.

## Features

- **Authentication**: JWT-based auth with access and refresh tokens.
- **Role-Based Access Control**: Admins, Faculty, Students, and Parents.
- **Course & Syllabus Management**: Sections, content links (videos, documents, assignments).
- **Media Uploads**: Local storage system for uploaded videos and documents.
- **Event Bus (RabbitMQ)**: Publishes resource updates to sync metadata with other services (like the RAG microservice).
- **Asynchronous Database Queries**: Powered by SQLAlchemy async engines and Asyncpg.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (SQLAlchemy + Alembic migrations)
- **Event Broker**: RabbitMQ (aio-pika client)
- **Validation**: Pydantic v2
- **Testing**: pytest & pytest-asyncio

---

## Directory Structure

```
lms-backend/
├── app/
│   ├── auth/           # Authentication routes & JWT strategies
│   ├── courses/        # Course and syllabus routers & schemas
│   ├── documents/      # Document management & file routers
│   ├── health/         # API Healthcheck endpoint
│   ├── messaging/      # RabbitMQ event publishers
│   ├── models/         # SQLAlchemy models
│   ├── notifications/  # Notification services & consumers
│   ├── users/          # Profile management
│   ├── videos/         # Video routers, streaming & uploads
│   ├── config.py       # Pydantic Settings
│   ├── database.py     # SQLAlchemy connection session helper
│   └── main.py         # Entrypoint
├── tests/              # Python test suite
├── Dockerfile          # Production Dockerfile
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## Running the Application

### 1. Prerequisites
- Python 3.12+
- PostgreSQL, RabbitMQ (usually run via the root `docker-compose.yml`)

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
RABBITMQ_URL=amqp://lms_user:lms_password@localhost:5672/lms_vhost
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
