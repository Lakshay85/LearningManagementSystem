import json
import asyncio
import aio_pika
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import AsyncSessionLocal
from app.models.models import CourseEnrollment, User
from app.models.enums import EnrollmentStatus, NotificationType, NotificationReferenceType
from app.notifications.service import notification_service
from app.notifications.schemas import CreateNotificationSchema
from app.messaging.constants import Exchanges, Queues
from sqlalchemy import and_


class NotificationConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.is_connected = False
        self._consumer_task = None

    async def connect(self):
        if self.is_connected:
            return

        if not settings.RABBITMQ_URL:
            print("⚠️ RABBITMQ_URL not configured, notification consumer disabled")
            return

        try:
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            self.channel = await self.connection.channel()

            # Declare queue
            queue = await self.channel.declare_queue(
                name=Queues.NOTIFICATION_EVENTS,
                durable=True
            )

            # Bind to course events exchange with specific routing keys
            await queue.bind(exchange=Exchanges.COURSE, routing_key="course.published")
            await queue.bind(exchange=Exchanges.COURSE, routing_key="course.content.added")
            await queue.bind(exchange=Exchanges.COURSE, routing_key="enrollment.created")
            await queue.bind(exchange=Exchanges.COURSE, routing_key="video.uploaded")

            self.is_connected = True
            print("🔔 Notification consumer connected to RabbitMQ")
            
            # Start consuming in background task
            self._consumer_task = asyncio.create_task(self.start_consuming(queue))
        except Exception as e:
            print(f"Failed to start notification consumer: {str(e)}")
            self.is_connected = False

    async def start_consuming(self, queue):
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        routing_key = message.routing_key
                        body = json.loads(message.body.decode('utf-8'))
                        print(f"📥 Consumer received event: {routing_key}")
                        
                        await self.process_event(routing_key, body)
                    except Exception as e:
                        print(f"Error processing message: {str(e)}")

    async def process_event(self, routing_key: str, content: dict):
        # We handle DB session locally since we are in background task context
        async with AsyncSessionLocal() as db:
            try:
                if routing_key == "course.published":
                    await self.handle_course_published(db, content)
                elif routing_key == "course.content.added":
                    await self.handle_content_added(db, content)
                elif routing_key == "enrollment.created":
                    await self.handle_student_enrolled(db, content)
                elif routing_key == "video.uploaded":
                    await self.handle_video_uploaded(db, content)
                else:
                    print(f"Unknown routing key: {routing_key}")
            except Exception as e:
                print(f"Failed to handle event {routing_key}: {str(e)}")

    async def handle_course_published(self, db: AsyncSession, event: dict):
        course_id = event["courseId"]
        title = event["title"]
        instructor_id = event["instructorId"]

        # Fetch active enrollments
        stmt = select(CourseEnrollment.studentId).where(
            and_(
                CourseEnrollment.courseId == UUID(course_id),
                CourseEnrollment.status == EnrollmentStatus.ACTIVE
            )
        )
        res = await db.execute(stmt)
        student_ids = [str(sid) for sid in res.scalars().all()]

        if not student_ids:
            return

        # Create notifications for all students
        await notification_service.create_for_multiple_users(
            db=db,
            user_ids=student_ids,
            dto=CreateNotificationSchema(
                userId="", # will be set per user
                type=NotificationType.COURSE_PUBLISHED,
                title="Course Published",
                message=f'The course "{title}" is now published and available for learning!',
                referenceType=NotificationReferenceType.COURSE,
                referenceId=course_id,
                metadata={
                    "courseTitle": title,
                    "instructorId": instructor_id
                }
            )
        )

    async def handle_content_added(self, db: AsyncSession, event: dict):
        course_id = event["courseId"]
        course_title = event["courseTitle"]
        instructor_id = event["instructorId"]
        content_type = event["contentType"]
        content_id = event["contentId"]
        content_title = event["contentTitle"]

        # Fetch active enrollments
        stmt = select(CourseEnrollment.studentId).where(
            and_(
                CourseEnrollment.courseId == UUID(course_id),
                CourseEnrollment.status == EnrollmentStatus.ACTIVE
            )
        )
        res = await db.execute(stmt)
        student_ids = [str(sid) for sid in res.scalars().all()]

        if not student_ids:
            return

        content_type_label = "video" if content_type == "video" else "document"
        ref_type = (
            NotificationReferenceType.VIDEO if content_type == "video"
            else NotificationReferenceType.DOCUMENT
        )

        await notification_service.create_for_multiple_users(
            db=db,
            user_ids=student_ids,
            dto=CreateNotificationSchema(
                userId="",
                type=NotificationType.CONTENT_ADDED,
                title="New Content Available",
                message=f'New {content_type_label} "{content_title}" has been added to "{course_title}"',
                referenceType=ref_type,
                referenceId=content_id,
                metadata={
                    "courseId": course_id,
                    "courseTitle": course_title,
                    "contentType": content_type,
                    "contentTitle": content_title
                }
            )
        )

    async def handle_student_enrolled(self, db: AsyncSession, event: dict):
        enrollment_id = event["enrollmentId"]
        user_id = event["userId"]
        course_id = event["courseId"]
        course_title = event["courseTitle"]
        instructor_id = event["instructorId"]
        student_name = event.get("studentName", "A student")

        # Notify Student
        await notification_service.create(
            db=db,
            dto=CreateNotificationSchema(
                userId=user_id,
                type=NotificationType.ENROLLMENT_SUCCESS,
                title="Enrollment Successful",
                message=f'You have successfully enrolled in "{course_title}"',
                referenceType=NotificationReferenceType.COURSE,
                referenceId=course_id,
                metadata={"courseTitle": course_title}
            )
        )

        # Notify Instructor
        if instructor_id:
            await notification_service.create(
                db=db,
                dto=CreateNotificationSchema(
                    userId=instructor_id,
                    type=NotificationType.NEW_ENROLLMENT,
                    title="New Student Enrolled",
                    message=f'{student_name} has enrolled in your course "{course_title}"',
                    referenceType=NotificationReferenceType.ENROLLMENT,
                    referenceId=enrollment_id,
                    metadata={
                        "courseId": course_id,
                        "courseTitle": course_title,
                        "studentId": user_id,
                        "studentName": student_name
                    }
                )
            )

    async def handle_video_uploaded(self, db: AsyncSession, event: dict):
        video_id = event["videoId"]
        user_id = event["userId"]
        title = event["title"]

        await notification_service.create(
            db=db,
            dto=CreateNotificationSchema(
                userId=user_id,
                type=NotificationType.VIDEO_UPLOADED,
                title="Video Upload Complete",
                message=f'Your video "{title}" has been successfully uploaded',
                referenceType=NotificationReferenceType.VIDEO,
                referenceId=video_id,
                metadata={"videoTitle": title}
            )
        )

    async def disconnect(self):
        try:
            if self._consumer_task:
                self._consumer_task.cancel()
            if self.channel:
                await self.channel.close()
            if self.connection:
                await self.connection.close()
        except Exception as e:
            print(f"Error closing consumer: {str(e)}")

# Global notification consumer instance
notification_consumer = NotificationConsumer()
