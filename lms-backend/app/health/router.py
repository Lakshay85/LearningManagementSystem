from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.messaging.service import messaging_service

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = "unhealthy"
    try:
        # Simple query check
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        print(f"Health check database failure: {str(e)}")

    mq_status = "healthy" if messaging_service.is_healthy() else "unhealthy"

    overall_status = "healthy"
    if db_status == "unhealthy":
        overall_status = "unhealthy"

    return {
        "status": overall_status,
        "timestamp": datetime_to_iso(),
        "services": {
            "database": db_status,
            "rabbitmq": mq_status
        }
    }

def datetime_to_iso():
    from datetime import datetime
    return datetime.now().isoformat()
