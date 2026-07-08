import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.auth.router import router as auth_router
from app.users.router import users_router, faculty_router
from app.courses.router import router as courses_router
from app.videos.router import router as videos_router
from app.documents.router import router as documents_router
from app.notifications.router import router as notifications_router
from app.notifications.consumer import notification_consumer
from app.health.router import router as health_router
from app.messaging.service import messaging_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    print("🚀 Starting LMS Python Backend...")
    
    # Initialize RabbitMQ connections
    await messaging_service.connect()
    await notification_consumer.connect()
    
    yield
    
    # Shutdown tasks
    print("🛑 Shutting down LMS Python Backend...")
    await notification_consumer.disconnect()
    await messaging_service.disconnect()

app = FastAPI(
    title="LMS Backend API",
    description="LMS Core Backend API in Python/FastAPI",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Range"],
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

@app.get("/")
def read_root():
    return {
        "message": "LMS Backend API is running",
        "tech": "FastAPI/Python"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True if settings.NODE_ENV == "development" else False
    )
