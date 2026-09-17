import sys
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure UTF-8 stdout/stderr on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app.config import settings
from app.database_init import init_database
from app.auth.router import router as auth_router
from app.users.router import users_router, faculty_router
from app.courses.router import router as courses_router
from app.videos.router import router as videos_router
from app.documents.router import router as documents_router
from app.notifications.router import router as notifications_router
from app.health.router import router as health_router
from app.messaging.service import messaging_service
from app.rag import rag_router, ingest_router, rag_service
from app.quiz.router import router as quiz_router
from app.admin.router import router as admin_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    print("🚀 Starting Unified LMS & RAG Python Backend...")
    
    # Initialize Database schemas, tables, and pgvector extensions
    await init_database()

    # Initialize in-process event messaging
    await messaging_service.connect()
    
    yield
    
    # Shutdown tasks
    print("🛑 Shutting down LMS Backend...")
    await rag_service.close()
    await messaging_service.disconnect()

app = FastAPI(
    title="LMS & RAG Unified Backend API",
    description="Unified Learning Management System & RAG Backend API in Python/FastAPI",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Range", "Accept-Ranges", "Content-Length"]
)

# Register routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(faculty_router)
app.include_router(courses_router)
app.include_router(videos_router)
app.include_router(documents_router)
app.include_router(notifications_router)
app.include_router(health_router)
app.include_router(rag_router)
app.include_router(ingest_router)
app.include_router(quiz_router)
app.include_router(admin_router)

@app.get("/")
def read_root():
    return {
        "message": "Unified LMS & RAG Backend API is running",
        "tech": "FastAPI/Python/pgvector",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True if settings.NODE_ENV == "development" else False
    )
