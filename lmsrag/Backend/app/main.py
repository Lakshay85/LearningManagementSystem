import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.service import db_service
from app.queue.service import ingestion_queue_service
from app.messaging.event_consumer import event_consumer_service
from app.rag.router import router as rag_router
from app.rag.ingest_router import router as ingest_router
from app.middleware.auth import AuthMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    print("🌅 Starting up RAG backend service...")
    
    # Connect database pool
    await db_service.connect()
    
    # Connect queue pool
    await ingestion_queue_service.connect()
    
    # Connect RabbitMQ event consumer
    await event_consumer_service.connect()
    
    yield
    
    # Shutdown tasks
    print("🌇 Shutting down RAG backend service...")
    await event_consumer_service.disconnect()
    await ingestion_queue_service.disconnect()
    await db_service.close()

app = FastAPI(
    title="LMS RAG Service",
    description="RAG microservice API for document ingestion and intelligent querying in Python",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
allowed_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication middleware
app.add_middleware(AuthMiddleware)

# Include routers
app.include_router(rag_router)
app.include_router(ingest_router)

@app.get("/health", tags=["Health"])
async def root_health():
    return {
        "status": "ok",
        "service": "lmsrag-service"
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=(settings.NODE_ENV == "development"))
