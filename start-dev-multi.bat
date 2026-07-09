@echo off
set PYTHONIOENCODING=utf-8

echo Starting LMS Databases and RabbitMQ in Docker...
docker-compose up -d lms-postgres rag-postgres rabbitmq

echo.
echo Launching services in separate terminal windows...
echo.

:: Launch LMS API
echo Launching LMS API...
start "LMS-API (Port 3000)" cmd /k "cd lms-backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 3000"

:: Launch RAG API
echo Launching RAG API...
start "RAG-API (Port 3001)" cmd /k "cd lmsrag\Backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 3001"

:: Launch Frontend
echo Launching Frontend...
start "FRONTEND (Port 5173)" cmd /k "cd lms-frontend && npm run dev"

echo All services launched!
pause
