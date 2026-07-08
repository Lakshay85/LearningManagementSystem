import json
import asyncio
import aio_pika
from typing import Any
from pydantic import BaseModel

from app.config import settings
from app.messaging.constants import Exchanges, RoutingKeys
from app.messaging.events import (
    UserCreatedEvent, UserUpdatedEvent, UserDeletedEvent,
    CourseCreatedEvent, CourseUpdatedEvent, CoursePublishedEvent,
    ContentAddedToCourseEvent, StudentEnrolledEvent, DocumentUploadedEvent,
    DocumentLinkedToCourseEvent, VideoUploadedEvent, VideoLinkedToCourseEvent,
    NotificationEvent
)

class MessagingService:
    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.RobustChannel] = None
        self.is_connected = False
        self._lock = asyncio.Lock()

    async def connect(self):
        if self.is_connected:
            return
        
        async with self._lock:
            if self.is_connected:
                return

            if not settings.RABBITMQ_URL:
                print("⚠️ RABBITMQ_URL not configured, messaging disabled")
                return

            try:
                # Use robust connection for automatic reconnects
                self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
                self.channel = await self.connection.channel()

                # Setup exchanges
                await self.setup_exchanges()

                self.is_connected = True
                print("🐰 Connected to RabbitMQ")
            except Exception as e:
                print(f"Failed to connect to RabbitMQ: {str(e)}")
                self.is_connected = False

    async def setup_exchanges(self):
        if not self.channel:
            return

        exchanges = [
            Exchanges.USER,
            Exchanges.COURSE,
            Exchanges.DOCUMENT,
            Exchanges.RAG,
            Exchanges.NOTIFICATION
        ]

        for exchange in exchanges:
            await self.channel.declare_exchange(
                name=exchange,
                type=aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            print(f"Exchange declared: {exchange}")

    async def disconnect(self):
        try:
            if self.channel:
                await self.channel.close()
            if self.connection:
                await self.connection.close()
            self.is_connected = False
            print("Disconnected from RabbitMQ")
        except Exception as e:
            print(f"Error disconnecting from RabbitMQ: {str(e)}")

    async def publish(self, exchange_name: str, routing_key: str, message: Any) -> bool:
        if not self.is_connected or not self.channel:
            # Try to connect once in case of temporary disconnect
            try:
                await self.connect()
            except Exception:
                pass
            
            if not self.is_connected or not self.channel:
                print(f"Cannot publish message, RabbitMQ not connected: {routing_key}")
                return False

        try:
            exchange = await self.channel.get_exchange(exchange_name)
            
            if isinstance(message, BaseModel):
                body = message.model_dump_json().encode('utf-8')
            else:
                body = json.dumps(message, default=str).encode('utf-8')

            await exchange.publish(
                aio_pika.Message(
                    body=body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    content_type='application/json'
                ),
                routing_key=routing_key
            )
            print(f"📤 Published event: {routing_key}")
            return True
        except Exception as e:
            print(f"Failed to publish event {routing_key}: {str(e)}")
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
        return self.is_connected and self.connection and not self.connection.is_closed

# Global messaging service instance
messaging_service = MessagingService()
