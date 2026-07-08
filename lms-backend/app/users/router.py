from fastapi import APIRouter, Depends, Response, status, UploadFile, File, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.auth.dependencies import get_current_user, require_faculty
from app.users.service import UserService

users_router = APIRouter(prefix="/users", tags=["Users"])
faculty_router = APIRouter(prefix="/faculty", tags=["Faculty"])

user_service = UserService()

# ============ USER ENDPOINTS ============

@users_router.get("", status_code=status.HTTP_200_OK)
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await user_service.get_all_users(db)


@users_router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_user(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await user_service.delete_user(db, id)


@users_router.delete("", status_code=status.HTTP_200_OK)
async def delete_all_users(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await user_service.delete_all_users(db)


@users_router.post("/upload-profile-picture", status_code=status.HTTP_200_OK)
async def upload_profile_picture(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    file_buffer = await file.read()
    return await user_service.upload_profile_picture(
        db=db,
        user_id=current_user["userId"],
        file_buffer=file_buffer,
        original_filename=file.filename or "profile.jpg",
        mime_type=file.content_type or "image/jpeg"
    )


# ============ FACULTY ENDPOINTS ============

@faculty_router.get("/all-content", status_code=status.HTTP_200_OK)
async def get_all_content(
    request: Request,
    page: str = "1",
    limit: str = "12",
    search: Optional[str] = None,
    fileType: Optional[str] = None,
    timeRange: Optional[str] = None,
    sizeRange: Optional[str] = None,
    sortBy: str = "newest",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    # Parse numbers safely (similar to parseInt(page, 10) || 1)
    try:
        page_val = int(page)
    except ValueError:
        page_val = 1
        
    try:
        limit_val = int(limit)
    except ValueError:
        limit_val = 12

    return await user_service.get_all_content(
        db=db,
        user_id=current_user["userId"],
        page=page_val,
        limit=limit_val,
        search=search,
        file_type=fileType,
        time_range=timeRange,
        size_range=sizeRange,
        sort_by=sortBy
    )
