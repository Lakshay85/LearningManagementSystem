import json
import asyncio
from typing import Any, Optional
from pydantic import BaseModel

from app.messaging.constants import Exchanges, RoutingKeys
from app.messaging.events import (
    UserCreatedEvent, UserUpdatedEvent, UserDeletedEvent,
    CourseCreatedEvent, CourseUpdatedEvent, CoursePublishedEvent,
    ContentAddedToCourseEvent, StudentEnrolledEvent, DocumentUploadedEvent,
    DocumentLinkedToCourseEvent, VideoUploadedEvent, VideoLinkedToCourseEvent,
    NotificationEvent
)
from app.notifications.consumer import notification_consumer

class MessagingService:
    """
    In-process asynchronous event dispatcher.
    Replaces external message broker with low-latency in-process async tasks.
    """
    def __init__(self):
        self.is_connected = True

    async def connect(self):
        self.is_connected = True
        print("📨 In-process event dispatcher initialized")

    async def disconnect(self):
        self.is_connected = False
        print("In-process event dispatcher stopped")

    async def publish(self, exchange_name: str, routing_key: str, message: Any) -> bool:
        try:
            if isinstance(message, BaseModel):
                event_data = message.model_dump(mode="json")
            elif isinstance(message, dict):
                event_data = message
            else:
                event_data = json.loads(json.dumps(message, default=str))

            print(f"📤 Dispatched event: {routing_key}")
            
            # Dispatch in background task to notification consumer
            asyncio.create_task(notification_consumer.process_event(routing_key, event_data))
            return True
        except Exception as e:
            print(f"Failed to dispatch event {routing_key}: {str(e)}")
            return False

    # ==================== User Events ====================
    async def publish_user_created(self, event: UserCreatedEvent):
        return await self.publish(Exchanges.USER, RoutingKeys.USER_CREATED, event)

    async def publish_user_updated(self, event: UserUpdatedEvent):
        return await self.publish(Exchanges.USER, RoutingKeys.USER_UPDATED, event)

    async def publish_user_deleted(self, event: UserDeletedEvent):
        return await self.publish(Exchanges.USER, RoutingKeys.USER_DELETED, event)

    # ==================== Course Events ====================
    async def publish_course_created(self, event: CourseCreatedEvent):
        return await self.publish(Exchanges.COURSE, RoutingKeys.COURSE_CREATED, event)

    async def publish_course_updated(self, event: CourseUpdatedEvent):
        return await self.publish(Exchanges.COURSE, RoutingKeys.COURSE_UPDATED, event)

    async def publish_course_published(self, event: CoursePublishedEvent):
        return await self.publish(Exchanges.COURSE, RoutingKeys.COURSE_PUBLISHED, event)

    # ==================== Enrollment Events ====================
    async def publish_student_enrolled(self, event: StudentEnrolledEvent):
        return await self.publish(Exchanges.COURSE, RoutingKeys.STUDENT_ENROLLED, event)

    # ==================== Document Events ====================
    async def publish_document_uploaded(self, event: DocumentUploadedEvent):
        return await self.publish(Exchanges.DOCUMENT, RoutingKeys.DOCUMENT_UPLOADED, event)

    async def publish_document_linked_to_course(self, event: DocumentLinkedToCourseEvent):
        return await self.publish(Exchanges.DOCUMENT, RoutingKeys.DOCUMENT_LINKED_TO_COURSE, event)

    # ==================== Video Events ====================
    async def publish_video_uploaded(self, event: VideoUploadedEvent):
        return await self.publish(Exchanges.COURSE, RoutingKeys.VIDEO_UPLOADED, event)

    async def publish_video_linked_to_course(self, event: VideoLinkedToCourseEvent):
        return await self.publish(Exchanges.COURSE, RoutingKeys.VIDEO_LINKED_TO_COURSE, event)

    # ==================== Content Events ====================
    async def publish_content_added_to_course(self, event: ContentAddedToCourseEvent):
        return await self.publish(Exchanges.COURSE, RoutingKeys.CONTENT_ADDED_TO_COURSE, event)

    # ==================== Notification Events ====================
    async def publish_notification(self, event: NotificationEvent):
        return await self.publish(Exchanges.NOTIFICATION, RoutingKeys.NOTIFICATION_CREATED, event)

    # ==================== Health Check ====================
    def is_healthy(self) -> bool:
        return self.is_connected

# Global messaging service instance
messaging_service = MessagingService()
