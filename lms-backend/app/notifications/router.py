from fastapi import APIRouter, Depends, Response, status, Query, Request, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse
from datetime import datetime
from typing import Optional
import asyncio
import json

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.notifications.schemas import NotificationQuerySchema
from app.notifications.service import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", status_code=status.HTTP_200_OK)
async def get_notifications(
    page: int = 1,
    limit: int = 20,
    type: Optional[str] = None,
    unreadOnly: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = NotificationQuerySchema(
        page=page,
        limit=limit,
        type=type,
        unreadOnly=unreadOnly
    )
    return await notification_service.find_all(db, current_user["userId"], query)


@router.get("/unread-count", status_code=status.HTTP_200_OK)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    count = await notification_service.get_unread_count(db, current_user["userId"])
    return {"unreadCount": count}


@router.get("/preferences", status_code=status.HTTP_200_OK)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await notification_service.get_preferences(db, current_user["userId"])


@router.patch("/preferences", status_code=status.HTTP_200_OK)
async def update_preferences(
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await notification_service.update_preferences(db, current_user["userId"], body)


@router.get("/sse")
async def sse_notifications(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["userId"]

    async def event_generator():
        # Register real-time event queue
        queue = await notification_service.register_queue(user_id)
        
        try:
            while True:
                # Check for client disconnect
                if await request.is_disconnected():
                    break
                
                try:
                    # Timeout after 30 seconds for heartbeat
                    event_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": "notification",
                        "data": json.dumps(event_data)
                    }
                except asyncio.TimeoutError:
                    # Send keep-alive heartbeat
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps({
                            "type": "heartbeat",
                            "timestamp": datetime.now().isoformat()
                        })
                    }
        finally:
            await notification_service.unregister_queue(user_id, queue)

    return EventSourceResponse(event_generator())


@router.patch("/{id}/read", status_code=status.HTTP_200_OK)
async def mark_as_read(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await notification_service.mark_as_read(db, id, current_user["userId"])


@router.patch("/read-all", status_code=status.HTTP_200_OK)
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await notification_service.mark_all_as_read(db, current_user["userId"])


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    await notification_service.delete(db, id, current_user["userId"])
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("", status_code=status.HTTP_200_OK)
async def delete_all_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await notification_service.delete_all(db, current_user["userId"])
