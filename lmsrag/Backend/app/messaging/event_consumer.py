import json
import asyncio
import aio_pika
from typing import Optional

from app.config import settings
from app.database.service import db_service

EXCHANGES = {
    'USER': 'lms.user.events',
    'COURSE': 'lms.course.events',
    'DOCUMENT': 'lms.document.events',
    'RAG': 'lms.rag.events',
}

ROUTING_KEYS = {
    'USER_DELETED': 'user.deleted',
    'COURSE_CREATED': 'course.created',
    'COURSE_DELETED': 'course.deleted',
    'DOCUMENT_UPLOADED': 'document.uploaded',
    'DOCUMENT_PROCESSED': 'document.processed',
    'DOCUMENT_LINKED_TO_COURSE': 'document.linked',
    'VIDEO_LINKED_TO_COURSE': 'video.linked',
}

QUEUES = {
    'RAG_USER_EVENTS': 'rag.user.events',
    'RAG_COURSE_EVENTS': 'rag.course.events',
    'RAG_DOCUMENT_EVENTS': 'rag.document.events',
}

class EventConsumerService:
    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.RobustChannel] = None
        self.is_connected = False
        self.db = db_service

    async def connect(self):
        rabbit_url = settings.RABBITMQ_URL
        if not rabbit_url:
            print("⚠️ RABBITMQ_URL not configured, event consumer disabled")
            return

        try:
            self.connection = await aio_pika.connect_robust(rabbit_url)
            self.channel = await self.connection.channel()

            await self.setup_queues()
            await self.start_consumers()

            self.is_connected = True
            print("🐰 RAG Event Consumer connected to RabbitMQ")
        except Exception as e:
            print(f"Failed to connect to RabbitMQ: {str(e)}")
            self.is_connected = False

    async def disconnect(self):
        try:
            if self.channel:
                await self.channel.close()
            if self.connection:
                await self.connection.close()
            print("Disconnected from RabbitMQ")
        except Exception as e:
            print(f"Error disconnecting from RabbitMQ: {str(e)}")

    async def setup_queues(self):
        if not self.channel:
            return

        # Assert exchanges
        for name, ex_name in EXCHANGES.items():
            await self.channel.declare_exchange(ex_name, aio_pika.ExchangeType.TOPIC, durable=True)

        # Assert queues and bind them
        # 1. User events queue
        user_q = await self.channel.declare_queue(QUEUES['RAG_USER_EVENTS'], durable=True)
        await user_q.bind(EXCHANGES['USER'], routing_key='user.#')

        # 2. Course events queue
        course_q = await self.channel.declare_queue(QUEUES['RAG_COURSE_EVENTS'], durable=True)
        await course_q.bind(EXCHANGES['COURSE'], routing_key='course.#')

        # 3. Document events queue
        doc_q = await self.channel.declare_queue(QUEUES['RAG_DOCUMENT_EVENTS'], durable=True)
        await doc_q.bind(EXCHANGES['DOCUMENT'], routing_key='document.#')

    async def start_consumers(self):
        if not self.channel:
            return

        # Start consuming
        user_q = await self.channel.get_queue(QUEUES['RAG_USER_EVENTS'])
        course_q = await self.channel.get_queue(QUEUES['RAG_COURSE_EVENTS'])
        doc_q = await self.channel.get_queue(QUEUES['RAG_DOCUMENT_EVENTS'])

        asyncio.create_task(self.consume_queue(user_q, self.handle_user_event))
        asyncio.create_task(self.consume_queue(course_q, self.handle_course_event))
        asyncio.create_task(self.consume_queue(doc_q, self.handle_document_event))
        print("📥 Started consuming events from all queues")

    async def consume_queue(self, queue: aio_pika.RobustQueue, handler):
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        await handler(message)
                    except Exception as e:
                        print(f"Error handling message on {queue.name}: {str(e)}")

    async def handle_user_event(self, message: aio_pika.IncomingMessage):
        routing_key = message.routing_key
        data = json.loads(message.body.decode())
        print(f"📬 Received user event: {routing_key}")

        if routing_key == ROUTING_KEYS['USER_DELETED']:
            await self.handle_user_deleted(data)

    async def handle_course_event(self, message: aio_pika.IncomingMessage):
        routing_key = message.routing_key
        data = json.loads(message.body.decode())
        print(f"📬 Received course event: {routing_key}")

        if routing_key == ROUTING_KEYS['COURSE_CREATED']:
            await self.handle_course_created(data)
        elif routing_key == ROUTING_KEYS['COURSE_DELETED']:
            await self.handle_course_deleted(data)
        elif routing_key == ROUTING_KEYS['VIDEO_LINKED_TO_COURSE']:
            await self.handle_video_linked_to_course(data)

    async def handle_document_event(self, message: aio_pika.IncomingMessage):
        routing_key = message.routing_key
        data = json.loads(message.body.decode())
        print(f"📬 Received document event: {routing_key}")

        if routing_key == ROUTING_KEYS['DOCUMENT_UPLOADED']:
            await self.handle_document_uploaded(data)
        elif routing_key == ROUTING_KEYS['DOCUMENT_LINKED_TO_COURSE']:
            await self.handle_document_linked_to_course(data)

    # ==================== Event Handlers ====================

    async def handle_user_deleted(self, data: dict):
        user_id = data.get("userId")
        print(f"🗑️ User deleted, cleaning up RAG data for user: {user_id}")
        try:
            await self.db.execute(
                'UPDATE chat_sessions SET is_active = false WHERE user_id = $1',
                user_id
            )
            print(f"✅ Cleaned up RAG data for deleted user: {user_id}")
        except Exception as e:
            print(f"Failed to clean up user data: {user_id}, error: {str(e)}")
            raise e

    async def handle_course_created(self, data: dict):
        print(f"📚 Course created: {data.get('courseId')} - {data.get('title')}")

    async def handle_course_deleted(self, data: dict):
        course_id = data.get("courseId")
        print(f"🗑️ Course deleted, cleaning up associations: {course_id}")
        try:
            await self.db.execute(
                'UPDATE chat_sessions SET course_id = NULL WHERE course_id = $1',
                course_id
            )
            await self.db.execute(
                "UPDATE documents SET metadata = metadata - 'courseId' WHERE metadata->>'courseId' = $1",
                course_id
            )
            print(f"✅ Cleaned up associations for deleted course: {course_id}")
        except Exception as e:
            print(f"Failed to clean up course data: {course_id}, error: {str(e)}")
            raise e

    async def handle_document_uploaded(self, data: dict):
        doc_id = data.get("documentId")
        course_id = data.get("courseId")
        print(f"Document uploaded: {doc_id} for course: {course_id or 'N/A'}")

        if course_id:
            try:
                await self.db.execute(
                    "UPDATE documents SET metadata = metadata || $1::jsonb WHERE metadata->>'lmsDocumentId' = $2 OR metadata->>'documentId' = $2",
                    json.dumps({"courseId": course_id}),
                    doc_id
                )
                print(f"✅ Updated document metadata with courseId: {doc_id} -> {course_id}")
            except Exception as e:
                print(f"Failed to update document metadata: {str(e)}")

    async def handle_document_linked_to_course(self, data: dict):
        doc_id = data.get("documentId")
        rag_doc_id = data.get("ragDocId")
        course_id = data.get("courseId")
        print(f"🔗 Linking document {rag_doc_id} to course {course_id}")

        try:
            await self.db.execute(
                "UPDATE documents SET metadata = metadata || $1::jsonb WHERE doc_id = $2",
                json.dumps({"courseId": course_id, "lmsDocumentId": doc_id}),
                rag_doc_id
            )
            print(f"✅ Document linked to course: {rag_doc_id} -> {course_id}")
        except Exception as e:
            print(f"Failed to link document to course: {str(e)}")
            raise e

    async def handle_video_linked_to_course(self, data: dict):
        video_id = data.get("videoId")
        course_id = data.get("courseId")
        print(f"🎥 Linking video {video_id} to course {course_id}")

        try:
            await self.db.execute(
                "UPDATE documents SET metadata = metadata || $1::jsonb WHERE metadata->>'videoId' = $2 OR metadata->>'lmsVideoId' = $2",
                json.dumps({"courseId": course_id}),
                video_id
            )
            print(f"✅ Updated video metadata with courseId: {video_id} -> {course_id}")
        except Exception as e:
            print(f"Failed to update video metadata: {str(e)}")

    def is_healthy(self) -> bool:
        return self.is_connected

# Global singleton
event_consumer_service = EventConsumerService()
