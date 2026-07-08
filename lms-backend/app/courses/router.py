from fastapi import APIRouter, Depends, Response, status, Query, Request, UploadFile, File, Form, Body
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Union
import json
import urllib.parse

from app.database import get_db
from app.auth.dependencies import get_current_user, require_faculty
from app.courses.schemas import (
    CreateCourseSchema, UpdateCourseSchema, CreateSectionSchema,
    UpdateSectionSchema, CreateContentSchema, UploadDocumentSchema
)
from app.courses.service import CourseService

router = APIRouter(prefix="/courses", tags=["Courses"])
course_service = CourseService()

@router.get("/published", status_code=status.HTTP_200_OK)
async def get_published_courses(
    page: str = "1",
    limit: str = "12",
    search: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        page_val = int(page)
    except ValueError:
        page_val = 1
        
    try:
        limit_val = int(limit)
    except ValueError:
        limit_val = 12

    return await course_service.get_published_courses(
        db=db,
        page=page_val,
        limit=limit_val,
        search=search,
        category=category,
        level=level
    )


@router.get("/faculty/students", status_code=status.HTTP_200_OK)
async def get_faculty_students(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    return await course_service.get_faculty_students(db, current_user["userId"])


@router.get("/{id}/content-summary", status_code=status.HTTP_200_OK)
async def get_course_content_summary(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await course_service.get_course_content_summary(db, id)


@router.get("/public/{id}", status_code=status.HTTP_200_OK)
async def get_public_course(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await course_service.get_public_course_by_id(db, id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_course(
    dto: CreateCourseSchema,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    return await course_service.create_course(db, current_user["userId"], dto)


@router.get("/my-courses", status_code=status.HTTP_200_OK)
async def get_my_courses(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    return await course_service.get_my_courses(db, current_user["userId"])


@router.get("/my-recent", status_code=status.HTTP_200_OK)
async def get_my_recent_courses(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    return await course_service.get_my_recent_courses(db, current_user["userId"])


@router.get("/analytics/details", status_code=status.HTTP_200_OK)
async def get_analytics_details(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    details = await course_service.get_analytics_details(db, current_user["userId"])
    return {
        "success": True,
        "data": details
    }


@router.get("/my-stats", status_code=status.HTTP_200_OK)
async def get_my_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    return await course_service.getMyStats(db, current_user["userId"])


@router.get("/{id}", status_code=status.HTTP_200_OK)
async def get_course(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Returns course details with authorization verification
    return await course_service.get_course_by_id(db, id, current_user["userId"] if current_user["role"] == "teacher" else None)


@router.patch("/{id}", status_code=status.HTTP_200_OK)
async def update_course(
    id: str,
    dto: UpdateCourseSchema,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    return await course_service.update_course(db, id, current_user["userId"], dto)


@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_course(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    await course_service.delete_course(db, id, current_user["userId"])
    return {"message": "Course deleted successfully"}


@router.post("/{courseId}/sections", status_code=status.HTTP_201_CREATED)
async def add_section(
    courseId: str,
    dto: CreateSectionSchema,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    return await course_service.add_section(db, courseId, current_user["userId"], dto)


@router.patch("/sections/{sectionId}", status_code=status.HTTP_200_OK)
async def update_section(
    sectionId: str,
    dto: UpdateSectionSchema,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    return await course_service.update_section(db, sectionId, current_user["userId"], dto)


@router.delete("/sections/{sectionId}", status_code=status.HTTP_200_OK)
async def delete_section(
    sectionId: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    await course_service.delete_section(db, sectionId, current_user["userId"])
    return {"message": "Section deleted successfully"}


@router.post("/sections/{sectionId}/content", status_code=status.HTTP_201_CREATED)
async def add_content(
    sectionId: str,
    dto: CreateContentSchema,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    return await course_service.add_content(db, sectionId, current_user["userId"], dto)


@router.post("/sections/{sectionId}/document", status_code=status.HTTP_201_CREATED)
async def upload_document(
    sectionId: str,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    order: Optional[int] = Form(None),
    isPreview: Optional[bool] = Form(False),
    isRequired: Optional[bool] = Form(False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    # Form-data fields map to DTO
    class TempUploadDto:
        pass
    dto = TempUploadDto()
    dto.title = title
    dto.description = description
    # Check string or int safely
    dto.order = int(order) if order is not None else None
    dto.isPreview = isPreview
    dto.isRequired = isRequired

    file_buffer = await file.read()

    return await course_service.upload_document(
        db=db,
        section_id=sectionId,
        instructor_id=current_user["userId"],
        file_name=file.filename or "file",
        file_size=file.size or len(file_buffer),
        file_content_type=file.content_type or "application/octet-stream",
        file_buffer=file_buffer,
        dto=dto
    )


@router.post("/sections/{sectionId}/documents", status_code=status.HTTP_201_CREATED)
async def upload_multiple_documents(
    sectionId: str,
    files: List[UploadFile] = File(...),
    titles: Union[str, List[str]] = Form(""),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    # Titles can be list of strings, or a single string if only one/none provided
    titles_list = []
    if isinstance(titles, str):
        if titles:
            titles_list = [titles]
    else:
        titles_list = titles

    return await course_service.upload_multiple_documents(
        db=db,
        section_id=sectionId,
        instructor_id=current_user["userId"],
        files=files,
        titles=titles_list
    )


@router.delete("/content/{contentId}", status_code=status.HTTP_200_OK)
async def delete_content(
    contentId: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    await course_service.delete_content(db, contentId, current_user["userId"])
    return {"message": "Content deleted successfully"}


@router.get("/documents/{documentId}/download", status_code=status.HTTP_200_OK)
async def download_document(
    documentId: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    document, file_path = await course_service.get_document_for_download(db, documentId, current_user["userId"])
    
    encoded_filename = urllib.parse.quote(document.originalFilename)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
    }
    return FileResponse(
        path=file_path,
        media_type=document.mimeType,
        headers=headers
    )


@router.get("/documents/{documentId}/preview", status_code=status.HTTP_200_OK)
async def preview_document(
    documentId: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    document, file_path = await course_service.get_document_for_download(db, documentId, current_user["userId"])
    
    encoded_filename = urllib.parse.quote(document.originalFilename)
    headers = {
        "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}",
        "Cache-Control": "private, max-age=3600"
    }
    return FileResponse(
        path=file_path,
        media_type=document.mimeType,
        headers=headers
    )


@router.post("/{courseId}/enroll", status_code=status.HTTP_201_CREATED)
async def enroll_in_course(
    courseId: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await course_service.enroll_in_course(db, courseId, current_user["userId"])


@router.get("/enrolled/my-courses", status_code=status.HTTP_200_OK)
async def get_my_enrolled_courses(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await course_service.get_enrolled_courses(db, current_user["userId"])


@router.get("/{courseId}/enrolled-content", status_code=status.HTTP_200_OK)
async def get_enrolled_course_content(
    courseId: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await course_service.get_enrolled_course_content(db, courseId, current_user["userId"])


@router.get("/{courseId}/enrollment-status", status_code=status.HTTP_200_OK)
async def check_enrollment_status(
    courseId: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    is_enrolled = await course_service.is_enrolled(db, courseId, current_user["userId"])
    enrollment = await course_service.get_enrollment(db, courseId, current_user["userId"])
    return {
        "isEnrolled": is_enrolled,
        "enrollment": enrollment
    }


@router.patch("/{courseId}/progress", status_code=status.HTTP_200_OK)
async def update_progress(
    courseId: str,
    progress: float = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await course_service.update_progress(db, courseId, current_user["userId"], progress)
