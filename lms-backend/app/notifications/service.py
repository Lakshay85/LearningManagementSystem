import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import select, update, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.models import Notification, NotificationPreference
from app.models.enums import NotificationType, NotificationReferenceType
from app.notifications.schemas import CreateNotificationSchema, NotificationQuerySchema

class NotificationService:
    def __init__(self):
        # Map of userId -> list of active asyncio.Queue objects for real-time SSE streaming
        self.sse_queues: Dict[str, List[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def register_queue(self, user_id: str) -> asyncio.Queue:
        async with self._lock:
            queue = asyncio.Queue()
            if user_id not in self.sse_queues:
                self.sse_queues[user_id] = []
            self.sse_queues[user_id].append(queue)
            print(f"Registered SSE queue for user: {user_id}")
            return queue

    async def unregister_queue(self, user_id: str, queue: asyncio.Queue):
        async with self._lock:
            if user_id in self.sse_queues:
                if queue in self.sse_queues[user_id]:
                    self.sse_queues[user_id].remove(queue)
                if not self.sse_queues[user_id]:
                    del self.sse_queues[user_id]
            print(f"Unregistered SSE queue for user: {user_id}")

    async def emit_to_user(self, user_id: str, event_data: Dict[str, Any]):
        queues = self.sse_queues.get(user_id, [])
        for q in queues:
            await q.put(event_data)

    async def create(self, db: AsyncSession, dto: CreateNotificationSchema) -> Notification:
        # Check preferences first
        should_notify = await self.should_notify(db, dto.userId, dto.type)
        if not should_notify:
            # Still save but maybe don't trigger push or SSE? 
            # In NestJS it is: "Create a new notification... and emit SSE event if user is connected."
            # So it always saves to DB and triggers SSE, but checks preferences for emails/push channels. Let's match.
            pass

        notification = Notification(
            userId=UUID(dto.userId),
            type=dto.type,
            title=dto.title,
            message=dto.message,
            referenceType=dto.referenceType,
            referenceId=dto.referenceId,
            metadata_json=dto.metadata,
            isRead=False
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        print(f"Created notification for user {dto.userId}: {dto.title}")

        # Emit SSE event
        unread_count = await self.get_unread_count(db, dto.userId)
        
        # Serialize notification manually for SSE
        notification_data = {
            "id": str(notification.id),
            "userId": str(notification.userId),
            "type": notification.type,
            "title": notification.title,
            "message": notification.message,
            "isRead": notification.isRead,
            "readAt": notification.readAt.isoformat() if notification.readAt else None,
            "referenceType": notification.referenceType,
            "referenceId": notification.referenceId,
            "metadata": notification.metadata_json,
            "createdAt": notification.createdAt.isoformat() if notification.createdAt else None
        }

        await self.emit_to_user(dto.userId, {
            "type": "new_notification",
            "notification": notification_data,
            "unreadCount": unread_count
        })

        return notification

    async def create_for_multiple_users(
        self,
        db: AsyncSession,
        user_ids: List[str],
        dto: Any # Omit userId from schema
    ) -> List[Notification]:
        notifications = []
        for user_id in user_ids:
            # We construct schema for each user
            user_schema = CreateNotificationSchema(
                userId=user_id,
                type=dto.type,
                title=dto.title,
                message=dto.message,
                referenceType=dto.referenceType,
                referenceId=dto.referenceId,
                metadata=dto.metadata
            )
            n = await self.create(db, user_schema)
            notifications.append(n)
        return notifications

    async def find_all(self, db: AsyncSession, user_id: str, query: NotificationQuerySchema) -> Dict[str, Any]:
        page = query.page
        limit = query.limit
        skip = (page - 1) * limit

        filters = [
            Notification.userId == UUID(user_id)
        ]

        if query.type:
            filters.append(Notification.type == query.type)

        if query.unreadOnly:
            filters.append(Notification.isRead == False)

        # Count total
        count_stmt = select(func.count()).select_from(Notification).where(and_(*filters))
        count_res = await db.execute(count_stmt)
        total = count_res.scalar() or 0

        stmt = (
            select(Notification)
            .where(and_(*filters))
            .order_by(desc(Notification.createdAt))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        notifications = result.scalars().all()

        unread_count = await self.get_unread_count(db, user_id)

        return {
            "data": list(notifications),
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": (total + limit - 1) // limit if limit > 0 else 1,
            "unreadCount": unread_count
        }

    async def find_one(self, db: AsyncSession, id: str, user_id: str) -> Notification:
        try:
            notif_uuid = UUID(id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Notification not found")

        stmt = select(Notification).where(
            and_(
                Notification.id == notif_uuid,
                Notification.userId == UUID(user_id)
            )
        )
        result = await db.execute(stmt)
        notification = result.scalar_one_or_none()

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        return notification

    async def get_unread_count(self, db: AsyncSession, user_id: str) -> int:
        stmt = select(func.count()).select_from(Notification).where(
            and_(
                Notification.userId == UUID(user_id),
                Notification.isRead == False
            )
        )
        res = await db.execute(stmt)
        return res.scalar() or 0

    async def mark_as_read(self, db: AsyncSession, id: str, user_id: str) -> Notification:
        notification = await self.find_one(db, id, user_id)

        if not notification.isRead:
            notification.isRead = True
            notification.readAt = datetime.now()
            await db.commit()

            # Emit SSE event
            unread_count = await self.get_unread_count(db, user_id)
            notification_data = {
                "id": str(notification.id),
                "userId": str(notification.userId),
                "isRead": notification.isRead,
                "readAt": notification.readAt.isoformat()
            }
            await self.emit_to_user(user_id, {
                "type": "notification_read",
                "notification": notification_data,
                "unreadCount": unread_count
            })

        return notification

    async def mark_all_as_read(self, db: AsyncSession, user_id: str) -> Dict[str, int]:
        user_uuid = UUID(user_id)
        stmt = (
            update(Notification)
            .where(
                and_(
                    Notification.userId == user_uuid,
                    Notification.isRead == False
                )
            )
            .values(isRead=True, readAt=datetime.now())
        )
        result = await db.execute(stmt)
        await db.commit()

        # Emit SSE event
        await self.emit_to_user(user_id, {
            "type": "all_read",
            "unreadCount": 0
        })

        return {"updated": result.rowcount}

    async def delete(self, db: AsyncSession, id: str, user_id: str):
        notification = await self.find_one(db, id, user_id)
        await db.delete(notification)
        await db.commit()
        print(f"Deleted notification {id} for user {user_id}")

    async def delete_all(self, db: AsyncSession, user_id: str) -> Dict[str, int]:
        stmt = select(Notification).where(Notification.userId == UUID(user_id))
        result = await db.execute(stmt)
        notifications = result.scalars().all()
        
        count = len(notifications)
        for n in notifications:
            await db.delete(n)
        await db.commit()

        return {"deleted": count}

    async def get_preferences(self, db: AsyncSession, user_id: str) -> NotificationPreference:
        user_uuid = UUID(user_id)
        stmt = select(NotificationPreference).where(NotificationPreference.userId == user_uuid)
        res = await db.execute(stmt)
        pref = res.scalar_one_or_none()

        if not pref:
            pref = NotificationPreference(
                userId=user_uuid,
                emailNotifications=True,
                pushNotifications=True,
                inAppNotifications=True,
                courseUpdates=True,
                enrollmentAlerts=True,
                newContentAlerts=True,
                systemAnnouncements=True,
                reminderNotifications=True
            )
            db.add(pref)
            await db.commit()
            await db.refresh(pref)

        return pref

    async def update_preferences(
        self,
        db: AsyncSession,
        user_id: str,
        updates: Dict[str, Any]
    ) -> NotificationPreference:
        pref = await self.get_preferences(db, user_id)

        # Filter fields
        allowed_keys = [
            "emailNotifications", "pushNotifications", "inAppNotifications",
            "courseUpdates", "enrollmentAlerts", "newContentAlerts",
            "systemAnnouncements", "reminderNotifications"
        ]

        for key in allowed_keys:
            if key in updates:
                setattr(pref, key, updates[key])

        await db.commit()
        await db.refresh(pref)
        return pref

    async def should_notify(self, db: AsyncSession, user_id: str, type: NotificationType) -> bool:
        pref = await self.get_preferences(db, user_id)

        if not pref.inAppNotifications:
            return False

        if type in (NotificationType.COURSE_PUBLISHED, NotificationType.COURSE_UPDATED, NotificationType.CONTENT_ADDED):
            return pref.courseUpdates
        elif type in (NotificationType.ENROLLMENT_SUCCESS, NotificationType.NEW_ENROLLMENT):
            return pref.enrollmentAlerts
        elif type in (NotificationType.VIDEO_UPLOADED, NotificationType.VIDEO_PROCESSED, NotificationType.DOCUMENT_UPLOADED):
            return pref.newContentAlerts
        elif type == NotificationType.SYSTEM_ANNOUNCEMENT:
            return pref.systemAnnouncements
        elif type == NotificationType.REMINDER:
            return pref.reminderNotifications

        return True

# Global notification service instance
notification_service = NotificationService()
