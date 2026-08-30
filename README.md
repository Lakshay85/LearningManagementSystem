# LMS - Learning Management System

A full-stack Learning Management System built with Python/FastAPI (backend) and React + Vite (frontend).

## Project Structure

```
lms/
├── lms-backend/     # Unified LMS & RAG FastAPI backend API
└── lms-frontend/    # React + Vite frontend
```

## Features

- User authentication (signup/login) with JWT
- Student dashboard with course tracking
- AI Teaching Assistant with RAG, pgvector search, and SSE streaming responses
- Structure-aware document parsing & ingestion (PDF/Text)
- Daily learning activity analytics
- Responsive modern UI

## Tech Stack

### Backend

- Python / FastAPI
- SQLAlchemy (Async) & asyncpg
- PostgreSQL & pgvector (IVFFlat index)
- Groq LLMs & FastEmbed ONNX Embeddings
- In-process async event dispatching & SSE streaming

### Frontend

- React 19
- Vite
- React Router
- Tailwind CSS v4
- Lucide React Icons

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js (v18+)
- Docker & Docker Compose
- pnpm

### Running the App

To run all infrastructure (databases, rabbitmq) in Docker, and application services locally:

```bash
# Run the local start batch script
./start-dev.bat
```

## Environment Variables

Create `.env` files in both backend and frontend directories based on the provided `.env.example` files.

## Copyright and License

Copyright (c) 2026 Lakshay Rohilla

All Rights Reserved.

This source code is the proprietary property of Lakshay Rohilla.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without prior written permission.

For permission requests, please contact the author.
