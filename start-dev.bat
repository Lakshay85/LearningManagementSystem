@echo off
set PYTHONIOENCODING=utf-8

echo Starting LMS Databases and RabbitMQ in Docker...
docker-compose up -d lms-postgres rag-postgres rabbitmq

echo.
echo Starting LMS Python/FastAPI Services and Vite Frontend...
echo Press Ctrl+C to stop all services.
echo.

npx concurrently ^
  --kill-others ^
  --names "LMS-API,RAG-API,FRONTEND" ^
  --prefix-colors "blue,magenta,cyan" ^
  "cd lms-backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 3000" ^
  "cd lmsrag\Backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 3001" ^
  "cd lms-frontend && npm run dev"

