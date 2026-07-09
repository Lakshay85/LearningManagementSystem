# LMS - Learning Management System

A full-stack Learning Management System built with Python/FastAPI (backend) and React + Vite (frontend).

## Project Structure

```
lms/
├── api-gateway/     # API Gateway Proxy (FastAPI)
├── lms-backend/     # FastAPI backend API
├── lms-frontend/    # React + Vite frontend
└── lmsrag/          # RAG Service (FastAPI)
```

## Features

- User authentication (signup/login) with JWT
- Student dashboard with course tracking
- Daily learning activity analytics
- Weekly status monitoring
- Responsive design with Tailwind CSS

## Tech Stack

### Backend

- Python / FastAPI
- SQLAlchemy & Alembic
- PostgreSQL & pgvector
- JWT Authentication
- RabbitMQ (Event-driven messaging)
- In-process background tasks

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
