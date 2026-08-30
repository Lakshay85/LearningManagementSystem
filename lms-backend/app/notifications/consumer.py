import json
import asyncio
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.models import CourseEnrollment, User
from app.models.enums import EnrollmentStatus, NotificationType, NotificationReferenceType
from app.notifications.service import notification_service
from app.notifications.schemas import CreateNotificationSchema

class NotificationConsumer:
    """
    In-process notification handler that processes domain events
    and creates database notifications + emits real-time SSE updates.
    """
    async def process_event(self, routing_key: str, content: dict):
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
                    pass
            except Exception as e:
                print(f"Failed to handle event {routing_key}: {str(e)}")

    async def handle_course_published(self, db: AsyncSession, event: dict):
        course_id = event["courseId"]
        title = event["title"]
        instructor_id = event["instructorId"]

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

        await notification_service.create_for_multiple_users(
            db=db,
            user_ids=student_ids,
            dto=CreateNotificationSchema(
                userId="",
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

# Global notification consumer instance
notification_consumer = NotificationConsumer()
