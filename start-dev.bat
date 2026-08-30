@echo off
set PYTHONIOENCODING=utf-8

echo Starting LMS Unified Database (PostgreSQL + pgvector) in Docker...
docker-compose up -d lms-postgres

echo.
echo Starting Unified LMS Python/FastAPI Backend and Frontend...
echo Press Ctrl+C to stop all services.
echo.

npx concurrently ^
  --kill-others ^
  --names "LMS-API,FRONTEND" ^
  --prefix-colors "blue,cyan" ^
  "cd lms-backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 3000" ^
  "cd lms-frontend && npm run dev"
