import re
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID

from sqlalchemy import select, update, and_, or_, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.models import Course, CourseSection, CourseContent, CourseEnrollment, Document, User, Video
from app.models.enums import ContentType, DocumentType, CourseStatus, CourseVisibility, EnrollmentStatus
from app.storage.service import storage_service
from app.messaging.service import messaging_service
from app.messaging.events import (
    CoursePublishedEvent, CourseCreatedEvent, CourseUpdatedEvent,
    ContentAddedToCourseEvent, StudentEnrolledEvent, DocumentUploadedEvent,
    VideoLinkedToCourseEvent
)
from app.rag.service import rag_service
from app.rag.dto import IngestFileDto
from app.payments.pricing import is_paid_course
from app.payments.service import has_paid_order

class CourseService:
    def generate_slug(self, title: str) -> str:
        t = int(time.time() * 1000)
        # Convert timestamp to base 36
        chars = "0123456789abcdefghijklmnopqrstuvwxyz"
        base36 = ""
        while t:
            t, remainder = divmod(t, 36)
            base36 = chars[remainder] + base36
        
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        # If title has no alphanumeric characters
        if not slug:
            slug = "course"
        return f"{slug}-{base36}"

    async def create_course(
        self,
        db: AsyncSession,
        instructor_id: str,
        dto: Any
    ) -> Course:
        slug = self.generate_slug(dto.title)
        tags_str = ",".join(dto.tags) if dto.tags else None

        course = Course(
            title=dto.title,
            subtitle=dto.subtitle,
            description=dto.description,
            category=dto.category,
            subcategory=dto.subcategory,
            tags=tags_str,
            language=dto.language or "en",
            level=dto.level,
            prerequisites=dto.prerequisites,
            learningObjectives=dto.learningObjectives,
            targetAudience=dto.targetAudience,
            visibility=dto.visibility,
            isFree=dto.isFree if dto.isFree is not None else True,
            price=dto.price,
            discountPrice=dto.discountPrice,
            currency=dto.currency or "INR",
            slug=slug,
            instructorId=UUID(instructor_id)
        )

        db.add(course)
        await db.commit()
        await db.refresh(course)

        # Publish course created event
        try:
            await messaging_service.publish_course_created(
                CourseCreatedEvent(
                    courseId=str(course.id),
                    title=course.title,
                    description=course.description,
                    instructorId=str(course.instructorId),
                    category=course.category,
                    createdAt=course.createdAt or datetime.now()
                )
            )
        except Exception as e:
            print(f"Failed to publish course created event: {str(e)}")

        return course

    async def get_my_courses(self, db: AsyncSession, instructor_id: str) -> List[Course]:
        # Eager load sections and contents
        stmt = (
            select(Course)
            .where(Course.instructorId == UUID(instructor_id))
            .options(
                selectinload(Course.sections).selectinload(CourseSection.contents)
            )
            .order_by(desc(Course.createdAt))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_my_recent_courses(self, db: AsyncSession, instructor_id: str, limit: int = 5) -> List[Course]:
        stmt = (
            select(Course)
            .where(Course.instructorId == UUID(instructor_id))
            .order_by(desc(Course.createdAt))
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_my_stats(self, db: AsyncSession, instructor_id: str) -> Dict[str, int]:
        stmt = select(Course).where(Course.instructorId == UUID(instructor_id))
        result = await db.execute(stmt)
        courses = result.scalars().all()

        total_courses = len(courses)
        published_courses = sum(1 for c in courses if c.status == CourseStatus.PUBLISHED)
        draft_courses = sum(1 for c in courses if c.status == CourseStatus.DRAFT)
        total_documents = sum(c.totalDocuments or 0 for c in courses)

        return {
            "totalCourses": total_courses,
            "publishedCourses": published_courses,
            "draftCourses": draft_courses,
            "totalDocuments": total_documents,
        }

    async def get_analytics_details(self, db: AsyncSession, instructor_id: str) -> Dict[str, Any]:
        stmt = (
            select(Course)
            .where(Course.instructorId == UUID(instructor_id))
            .order_by(desc(Course.createdAt))
        )
        result = await db.execute(stmt)
        courses = result.scalars().all()

        total_courses = len(courses)
        published = []
        draft = []
        for c in courses:
            data = {
                "id": str(c.id),
                "title": c.title,
                "createdAt": c.createdAt,
                "updatedAt": c.updatedAt,
                "status": c.status,
                "enrollmentCount": c.enrollmentCount
            }
            if c.status == CourseStatus.PUBLISHED:
                published.append(data)
            elif c.status == CourseStatus.DRAFT:
                draft.append(data)

        return {
            "totalCourses": total_courses,
            "publishedCourses": published,
            "draftCourses": draft,
        }

    async def get_course_by_id(self, db: AsyncSession, id: str, instructor_id: Optional[str] = None) -> Course:
        try:
            course_uuid = UUID(id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Course not found")

        stmt = (
            select(Course)
            .where(Course.id == course_uuid)
            .options(
                selectinload(Course.sections).selectinload(CourseSection.contents),
                selectinload(Course.instructor)
            )
        )
        result = await db.execute(stmt)
        course = result.scalar_one_or_none()

        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        if instructor_id and str(course.instructorId) != instructor_id:
            raise HTTPException(status_code=403, detail="You do not have access to this course")

        return course

    async def update_course(
        self,
        db: AsyncSession,
        id: str,
        instructor_id: str,
        dto: Any
    ) -> Course:
        course = await self.get_course_by_id(db, id, instructor_id)

        update_data = dto.model_dump(exclude_unset=True)
        if "tags" in update_data and update_data["tags"] is not None:
            update_data["tags"] = ",".join(update_data["tags"])

        # Check if course is being published
        old_status = course.status
        new_status = update_data.get("status")

        for key, value in update_data.items():
            setattr(course, key, value)

        if new_status == CourseStatus.PUBLISHED and old_status != CourseStatus.PUBLISHED:
            course.publishedAt = datetime.now()

        await db.commit()
        await db.refresh(course)

        # If published, fire event
        if new_status == CourseStatus.PUBLISHED and old_status != CourseStatus.PUBLISHED:
            try:
                await messaging_service.publish_course_published(
                    CoursePublishedEvent(
                        courseId=str(course.id),
                        title=course.title,
                        instructorId=str(course.instructorId),
                        publishedAt=course.publishedAt or datetime.now()
                    )
                )
            except Exception as e:
                print(f"Failed to publish course published event: {str(e)}")

        # Publish course updated event
        try:
            await messaging_service.publish_course_updated(
                CourseUpdatedEvent(
                    courseId=str(course.id),
                    title=course.title,
                    description=course.description,
                    status=course.status,
                    updatedAt=course.updatedAt or datetime.now()
                )
            )
        except Exception as e:
            print(f"Failed to publish course updated event: {str(e)}")

        return course

    async def delete_course(self, db: AsyncSession, id: str, instructor_id: str):
        course = await self.get_course_by_id(db, id, instructor_id)
        await db.delete(course)
        await db.commit()

    async def get_published_courses(
        self,
        db: AsyncSession,
        page: int = 1,
        limit: int = 12,
        search: Optional[str] = None,
        category: Optional[str] = None,
        level: Optional[str] = None
    ) -> Dict[str, Any]:
        filters = [
            Course.status == CourseStatus.PUBLISHED,
            Course.visibility == CourseVisibility.PUBLIC
        ]

        if search:
            filters.append(or_(
                Course.title.ilike(f"%{search}%"),
                Course.description.ilike(f"%{search}%")
            ))

        if category:
            filters.append(Course.category == category)

        if level:
            filters.append(Course.level == level)

        # Count total
        count_stmt = select(func.count()).select_from(Course).where(and_(*filters))
        count_res = await db.execute(count_stmt)
        total = count_res.scalar() or 0

        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        skip = (page - 1) * limit

        stmt = (
            select(Course)
            .where(and_(*filters))
            .options(selectinload(Course.instructor))
            .order_by(desc(Course.publishedAt))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        courses = result.scalars().all()

        return {
            "courses": courses,
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": total_pages,
            "hasMore": page < total_pages
        }

    async def get_course_content_summary(self, db: AsyncSession, course_id: str) -> Dict[str, Any]:
        try:
            course_uuid = UUID(course_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Course not found")

        course = await db.get(Course, course_uuid)
        if not course or course.status != CourseStatus.PUBLISHED:
            raise HTTPException(status_code=404, detail="Course not found or not published")

        stmt = (
            select(CourseSection)
            .where(CourseSection.courseId == course_uuid)
            .options(
                selectinload(CourseSection.contents).selectinload(CourseContent.video),
                selectinload(CourseSection.contents).selectinload(CourseContent.document)
            )
            .order_by(asc(CourseSection.order))
        )
        result = await db.execute(stmt)
        sections = result.scalars().all()

        total_videos = 0
        total_documents = 0
        total_estimated_minutes = 0
        sections_summary = []

        for section in sections:
            contents_summary = []
            # Sort contents by order
            contents = sorted(section.contents, key=lambda c: c.order)
            for content in contents:
                if content.contentType == ContentType.VIDEO:
                    total_videos += 1
                elif content.contentType == ContentType.DOCUMENT:
                    total_documents += 1
                
                if content.estimatedMinutes:
                    total_estimated_minutes += content.estimatedMinutes

                contents_summary.append({
                    "id": str(content.id),
                    "title": content.title,
                    "contentType": content.contentType,
                    "estimatedMinutes": content.estimatedMinutes,
                    "isPreview": content.isPreview
                })

            sections_summary.append({
                "id": str(section.id),
                "title": section.title,
                "order": section.order,
                "contents": contents_summary
            })

        return {
            "courseId": course_id,
            "totalSections": len(sections),
            "totalVideos": total_videos,
            "totalDocuments": total_documents,
            "totalEstimatedMinutes": total_estimated_minutes,
            "sections": sections_summary
        }

    async def get_public_course_by_id(self, db: AsyncSession, course_id: str) -> Course:
        try:
            course_uuid = UUID(course_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Course not found")

        stmt = (
            select(Course)
            .where(and_(Course.id == course_uuid, Course.status == CourseStatus.PUBLISHED))
            .options(
                selectinload(Course.sections).selectinload(CourseSection.contents),
                selectinload(Course.instructor)
            )
        )
        result = await db.execute(stmt)
        course = result.scalar_one_or_none()

        if not course:
            raise HTTPException(status_code=404, detail="Course not found or not published")

        # Sort sections and contents by order
        course.sections.sort(key=lambda s: s.order)
        for section in course.sections:
            section.contents.sort(key=lambda c: c.order)

        return course

    async def add_section(
        self,
        db: AsyncSession,
        course_id: str,
        instructor_id: str,
        dto: Any
    ) -> CourseSection:
        course = await self.get_course_by_id(db, course_id, instructor_id)

        # Get max order
        stmt = select(func.max(CourseSection.order)).where(CourseSection.courseId == course.id)
        max_order_res = await db.execute(stmt)
        max_order = max_order_res.scalar() or 0

        section = CourseSection(
            title=dto.title,
            description=dto.description,
            courseId=course.id,
            order=dto.order if dto.order is not None else max_order + 1,
            isPreview=dto.isPreview if dto.isPreview is not None else False
        )

        db.add(section)
        await db.commit()
        await db.refresh(section)
        return section

    async def update_section(
        self,
        db: AsyncSession,
        section_id: str,
        instructor_id: str,
        dto: Any
    ) -> CourseSection:
        try:
            section_uuid = UUID(section_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Section not found")

        stmt = (
            select(CourseSection)
            .where(CourseSection.id == section_uuid)
            .options(selectinload(CourseSection.course))
        )
        result = await db.execute(stmt)
        section = result.scalar_one_or_none()

        if not section:
            raise HTTPException(status_code=404, detail="Section not found")

        if str(section.course.instructorId) != instructor_id:
            raise HTTPException(status_code=403, detail="You do not have access to this section")

        update_data = dto.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(section, key, value)

        await db.commit()
        await db.refresh(section)
        return section

    async def delete_section(self, db: AsyncSession, section_id: str, instructor_id: str):
        try:
            section_uuid = UUID(section_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Section not found")

        stmt = (
            select(CourseSection)
            .where(CourseSection.id == section_uuid)
            .options(selectinload(CourseSection.course))
        )
        result = await db.execute(stmt)
        section = result.scalar_one_or_none()

        if not section:
            raise HTTPException(status_code=404, detail="Section not found")

        if str(section.course.instructorId) != instructor_id:
            raise HTTPException(status_code=403, detail="You do not have access to this section")

        await db.delete(section)
        await db.commit()

    async def add_content(
        self,
        db: AsyncSession,
        section_id: str,
        instructor_id: str,
        dto: Any
    ) -> CourseContent:
        try:
            section_uuid = UUID(section_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Section not found")

        stmt = (
            select(CourseSection)
            .where(CourseSection.id == section_uuid)
            .options(selectinload(CourseSection.course))
        )
        result = await db.execute(stmt)
        section = result.scalar_one_or_none()

        if not section:
            raise HTTPException(status_code=404, detail="Section not found")

        if str(section.course.instructorId) != instructor_id:
            raise HTTPException(status_code=403, detail="You do not have access to this section")

        # Get max order
        order_stmt = select(func.max(CourseContent.order)).where(CourseContent.sectionId == section.id)
        max_order_res = await db.execute(order_stmt)
        max_order = max_order_res.scalar() or 0

        if getattr(dto, 'quizId', None):
            content_type = ContentType.QUIZ
        elif dto.videoId:
            content_type = ContentType.VIDEO
        else:
            content_type = ContentType.TEXT

        content = CourseContent(
            title=dto.title,
            description=dto.description,
            sectionId=section.id,
            courseId=section.courseId,
            contentType=content_type,
            order=dto.order if dto.order is not None else max_order + 1,
            isPreview=dto.isPreview if dto.isPreview is not None else False,
            isRequired=dto.isRequired if dto.isRequired is not None else False,
            estimatedMinutes=dto.estimatedMinutes,
            videoId=UUID(dto.videoId) if dto.videoId else None,
            quizId=UUID(dto.quizId) if getattr(dto, 'quizId', None) else None,
            textContent=dto.textContent
        )

        db.add(content)
        await db.commit()
        await db.refresh(content)

        # Update course video count if a video was added
        if dto.videoId:
            course = section.course
            course.totalVideos = (course.totalVideos or 0) + 1
            await db.commit()

            # Publish messaging event for video linked to course
            try:
                await messaging_service.publish_video_linked_to_course(
                    VideoLinkedToCourseEvent(
                        videoId=dto.videoId,
                        courseId=str(section.courseId),
                        linkedAt=datetime.now()
                    )
                )
            except Exception as e:
                print(f"Failed to publish video linked to course event: {str(e)}")

        return content

    async def upload_document(
        self,
        db: AsyncSession,
        section_id: str,
        instructor_id: str,
        file_name: str,
        file_size: int,
        file_content_type: str,
        file_buffer: bytes,
        dto: Any
    ) -> CourseContent:
        try:
            section_uuid = UUID(section_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Section not found")

        stmt = (
            select(CourseSection)
            .where(CourseSection.id == section_uuid)
            .options(selectinload(CourseSection.course))
        )
        result = await db.execute(stmt)
        section = result.scalar_one_or_none()

        if not section:
            raise HTTPException(status_code=404, detail="Section not found")

        if str(section.course.instructorId) != instructor_id:
            raise HTTPException(status_code=403, detail="You do not have access to this section")

        # Check file size (max 5MB)
        if file_size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")

        # Determine document type
        document_type = DocumentType.OTHER
        if file_content_type == "application/pdf":
            document_type = DocumentType.PDF
        elif file_content_type in (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword"
        ):
            document_type = DocumentType.WORD
        elif file_content_type in (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.ms-powerpoint"
        ):
            document_type = DocumentType.POWERPOINT
        elif file_content_type in (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel"
        ):
            document_type = DocumentType.EXCEL

        # Save file to storage
        stored_filename = f"{int(time.time() * 1000)}-{file_name}"
        upload_result = await storage_service.save_document(file_buffer, stored_filename)

        # Extract storage path and ImageKit metadata
        if isinstance(upload_result, dict):
            storage_path = upload_result.get("path", f"documents/{datetime.now().year}/{stored_filename}")
            imagekit_file_id = upload_result.get("fileId")
            cdn_url = upload_result.get("cdnUrl")
        else:
            storage_path = upload_result
            imagekit_file_id = None
            cdn_url = None

        # Create Document record
        document = Document(
            title=dto.title,
            description=dto.description,
            originalFilename=file_name,
            storedFilename=stored_filename,
            storagePath=storage_path,
            mimeType=file_content_type,
            fileSize=file_size,
            documentType=document_type,
            imagekitFileId=imagekit_file_id,
            cdnUrl=cdn_url,
            uploaderId=UUID(instructor_id)
        )
        db.add(document)
        await db.flush()  # To populate document.id

        # Update course documents count
        course = section.course
        course.totalDocuments = (course.totalDocuments or 0) + 1

        # Create Content record
        order_stmt = select(func.max(CourseContent.order)).where(CourseContent.sectionId == section.id)
        max_order_res = await db.execute(order_stmt)
        max_order = max_order_res.scalar() or 0

        content = CourseContent(
            title=dto.title,
            description=dto.description,
            sectionId=section.id,
            courseId=section.courseId,
            contentType=ContentType.DOCUMENT,
            documentId=document.id,
            order=dto.order if dto.order is not None else max_order + 1,
            isPreview=dto.isPreview if dto.isPreview is not None else False,
            isRequired=dto.isRequired if dto.isRequired is not None else False
        )
        db.add(content)
        await db.commit()
        await db.refresh(content)

        # Ingest document into RAG system asynchronously in-process
        try:
            metadata = {
                "courseId": str(section.courseId),
                "lmsDocumentId": str(document.id),
                "documentType": document_type,
                "uploaderId": instructor_id
            }
            doc_type_str = "pdf" if "pdf" in (file_content_type or "").lower() else "text"
            await rag_service.ingest_file(
                IngestFileDto(
                    fileBuffer=file_buffer,
                    fileName=file_name,
                    docType=doc_type_str,
                    metadata=metadata
                )
            )
            print(f"Document ingested into RAG: {document.id}")
        except Exception as e:
            print(f"Failed to ingest document into RAG: {str(e)}")

        # Publish document uploaded event for RAG ingestion/sync in other modules
        try:
            await messaging_service.publish_document_uploaded(
                DocumentUploadedEvent(
                    documentId=str(document.id),
                    userId=instructor_id,
                    courseId=str(section.courseId),
                    fileName=file_name,
                    fileType=file_content_type,
                    fileSize=file_size,
                    uploadedAt=datetime.now()
                )
            )
        except Exception as e:
            print(f"Failed to publish document upload event: {str(e)}")

        return content

    async def upload_multiple_documents(
        self,
        db: AsyncSession,
        section_id: str,
        instructor_id: str,
        files: List[Any],  # UploadFile objects
        titles: List[str]
    ) -> List[CourseContent]:
        results = []
        for i, file in enumerate(files):
            title = titles[i] if i < len(titles) else file.filename
            
            # Create a simple mock DTO
            class TempDto:
                title = file.filename
                description = None
                order = None
                isPreview = False
                isRequired = False
            
            temp_dto = TempDto()
            temp_dto.title = title

            content = await self.upload_document(
                db=db,
                section_id=section_id,
                instructor_id=instructor_id,
                file_name=file.filename or "file",
                file_size=file.size or 0,
                file_content_type=file.content_type or "application/octet-stream",
                file_buffer=await file.read(),
                dto=temp_dto
            )
            results.append(content)
        return results

    async def delete_content(self, db: AsyncSession, content_id: str, instructor_id: str):
        try:
            content_uuid = UUID(content_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Content not found")

        stmt = (
            select(CourseContent)
            .where(CourseContent.id == content_uuid)
            .options(
                selectinload(CourseContent.course),
                selectinload(CourseContent.document)
            )
        )
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()

        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        if str(content.course.instructorId) != instructor_id:
            raise HTTPException(status_code=403, detail="You do not have access to this content")

        course = content.course

        if content.document:
            # Delete from physical storage
            if content.document.imagekitFileId:
                await storage_service.delete_by_file_id(content.document.imagekitFileId)
            else:
                await storage_service.delete_file(content.document.storagePath)
            await db.delete(content.document)
            course.totalDocuments = max(0, (course.totalDocuments or 0) - 1)

        if content.videoId:
            course.totalVideos = max(0, (course.totalVideos or 0) - 1)

        await db.delete(content)
        await db.commit()

    async def get_document_for_download(
        self,
        db: AsyncSession,
        document_id: str,
        user_id: str
    ) -> Tuple[Document, str]:
        try:
            doc_uuid = UUID(document_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Document not found")

        document = await db.get(Document, doc_uuid)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get local file path from storage service
        file_path = await storage_service.download(document.storagePath)
        return document, file_path

    async def enroll_in_course(self, db: AsyncSession, course_id: str, student_id: str,
                               payment_verified: bool = False) -> CourseEnrollment:
        try:
            course_uuid = UUID(course_id)
            student_uuid = UUID(student_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Course not found")

        course = await db.get(Course, course_uuid)
        if not course or course.status != CourseStatus.PUBLISHED:
            raise HTTPException(status_code=404, detail="Course not found or not available for enrollment")

        # Paid courses require a verified payment (set by the payments flow) or a prior paid order
        if is_paid_course(course) and not payment_verified:
            if not await has_paid_order(db, student_id, course_id):
                raise HTTPException(status_code=402, detail="Payment required to enroll in this course")

        # Check existing enrollment
        stmt = select(CourseEnrollment).where(
            and_(
                CourseEnrollment.courseId == course_uuid,
                CourseEnrollment.studentId == student_uuid
            )
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing:
            if existing.status == EnrollmentStatus.ACTIVE:
                raise HTTPException(status_code=409, detail="You are already enrolled in this course")
            
            existing.status = EnrollmentStatus.ACTIVE
            existing.lastAccessedAt = datetime.now()
            await db.commit()
            return existing

        enrollment = CourseEnrollment(
            courseId=course_uuid,
            studentId=student_uuid,
            status=EnrollmentStatus.ACTIVE,
            progress=0.0,
            lastAccessedAt=datetime.now(),
            enrolledAt=datetime.now()
        )
        db.add(enrollment)
        
        # Increment course enrollments count
        course.enrollmentCount = (course.enrollmentCount or 0) + 1
        await db.commit()
        await db.refresh(enrollment)

        # Publish student enrolled event for notification alerts
        try:
            student = await db.get(User, student_uuid)
            await messaging_service.publish_student_enrolled(
                StudentEnrolledEvent(
                    enrollmentId=str(enrollment.id),
                    userId=student_id,
                    courseId=course_id,
                    courseTitle=course.title,
                    instructorId=str(course.instructorId),
                    studentName=f"{student.firstName} {student.lastName}" if student else "A student",
                    enrolledAt=enrollment.enrolledAt or datetime.now()
                )
            )
        except Exception as e:
            print(f"Failed to publish student enrolled event: {str(e)}")

        return enrollment

    async def get_enrolled_courses(self, db: AsyncSession, student_id: str) -> List[CourseEnrollment]:
        stmt = (
            select(CourseEnrollment)
            .where(
                and_(
                    CourseEnrollment.studentId == UUID(student_id),
                    CourseEnrollment.status == EnrollmentStatus.ACTIVE
                )
            )
            .options(
                selectinload(CourseEnrollment.course).selectinload(Course.instructor)
            )
            .order_by(desc(CourseEnrollment.lastAccessedAt))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def is_enrolled(self, db: AsyncSession, course_id: str, student_id: str) -> bool:
        try:
            course_uuid = UUID(course_id)
            student_uuid = UUID(student_id)
        except ValueError:
            return False

        stmt = select(CourseEnrollment).where(
            and_(
                CourseEnrollment.courseId == course_uuid,
                CourseEnrollment.studentId == student_uuid,
                CourseEnrollment.status == EnrollmentStatus.ACTIVE
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_enrolled_course_content(self, db: AsyncSession, course_id: str, student_id: str) -> Course:
        is_enrolled = await self.is_enrolled(db, course_id, student_id)
        if not is_enrolled:
            raise HTTPException(status_code=403, detail="You are not enrolled in this course")

        # Update last accessed
        await db.execute(
            update(CourseEnrollment)
            .where(
                and_(
                    CourseEnrollment.courseId == UUID(course_id),
                    CourseEnrollment.studentId == UUID(student_id)
                )
            )
            .values(lastAccessedAt=datetime.now())
        )

        stmt = (
            select(Course)
            .where(Course.id == UUID(course_id))
            .options(
                selectinload(Course.instructor),
                selectinload(Course.sections).selectinload(CourseSection.contents).selectinload(CourseContent.video),
                selectinload(Course.sections).selectinload(CourseSection.contents).selectinload(CourseContent.document),
                selectinload(Course.sections).selectinload(CourseSection.contents).selectinload(CourseContent.quiz)
            )
        )
        result = await db.execute(stmt)
        course = result.scalar_one_or_none()

        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # Sort sections and contents by order
        course.sections.sort(key=lambda s: s.order)
        for section in course.sections:
            section.contents.sort(key=lambda c: c.order)

        return course

    async def get_enrollment(self, db: AsyncSession, course_id: str, student_id: str) -> Optional[CourseEnrollment]:
        try:
            course_uuid = UUID(course_id)
            student_uuid = UUID(student_id)
        except ValueError:
            return None

        stmt = (
            select(CourseEnrollment)
            .where(
                and_(
                    CourseEnrollment.courseId == course_uuid,
                    CourseEnrollment.studentId == student_uuid
                )
            )
            .options(selectinload(CourseEnrollment.course))
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def update_progress(self, db: AsyncSession, course_id: str, student_id: str, progress: float) -> CourseEnrollment:
        try:
            course_uuid = UUID(course_id)
            student_uuid = UUID(student_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Enrollment not found")

        stmt = select(CourseEnrollment).where(
            and_(
                CourseEnrollment.courseId == course_uuid,
                CourseEnrollment.studentId == student_uuid,
                CourseEnrollment.status == EnrollmentStatus.ACTIVE
            )
        )
        res = await db.execute(stmt)
        enrollment = res.scalar_one_or_none()

        if not enrollment:
            raise HTTPException(status_code=404, detail="Enrollment not found")

        enrollment.progress = min(100.0, max(0.0, progress))
        enrollment.lastAccessedAt = datetime.now()

        if enrollment.progress >= 100.0 and not enrollment.completedAt:
            enrollment.completedAt = datetime.now()
            enrollment.status = EnrollmentStatus.COMPLETED

        await db.commit()
        await db.refresh(enrollment)
        return enrollment

    async def get_faculty_students(self, db: AsyncSession, faculty_id: str) -> List[Dict[str, Any]]:
        stmt = (
            select(CourseEnrollment)
            .join(CourseEnrollment.course)
            .where(Course.instructorId == UUID(faculty_id))
            .options(
                selectinload(CourseEnrollment.course),
                selectinload(CourseEnrollment.student)
            )
            .order_by(desc(CourseEnrollment.enrolledAt))
        )
        result = await db.execute(stmt)
        enrollments = result.scalars().all()

        return [{
            "id": str(e.student.id),
            "firstName": e.student.firstName,
            "lastName": e.student.lastName,
            "email": e.student.email,
            "profilePicture": e.student.profilePicture,
            "enrolledAt": e.enrolledAt,
            "course": {
                "id": str(e.course.id),
                "title": e.course.title,
                "totalVideos": e.course.totalVideos,
                "totalDocuments": e.course.totalDocuments,
            },
            "progress": float(e.progress) if e.progress is not None else 0.0,
            "status": e.status
        } for e in enrollments]
