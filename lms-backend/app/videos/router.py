from fastapi import APIRouter, Depends, HTTPException, Response, status, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import os
import aiofiles
import mimetypes

from app.database import get_db
from app.auth.dependencies import get_current_user, get_current_user_optional, require_faculty
from app.videos.schemas import UpdateVideoSchema, UpdateVisibilitySchema, VideoQuerySchema
from app.videos.service import VideoService

router = APIRouter(prefix="/videos", tags=["Videos"])
video_service = VideoService()

# Generator for byte-range streaming
async def range_generator(file_path: str, start: int, chunk_size: int):
    async with aiofiles.open(file_path, mode="rb") as f:
        await f.seek(start)
        remaining = chunk_size
        while remaining > 0:
            to_read = min(remaining, 1024 * 1024)  # 1MB chunk size
            data = await f.read(to_read)
            if not data:
                break
            remaining -= len(data)
            yield data


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    visibility: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    upload_file = file or video
    if not upload_file:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Video file is required (send as 'video' or 'file')"
        )

    class TempDto:
        pass
    dto = TempDto()
    dto.title = title
    dto.description = description
    dto.category = category
    dto.visibility = visibility

    file_buffer = await upload_file.read()
    guessed_type, _ = mimetypes.guess_type(upload_file.filename or "")
    mime_type = upload_file.content_type or guessed_type or "video/mp4"
    if mime_type == "application/octet-stream" and guessed_type:
        mime_type = guessed_type

    video_record = await video_service.upload_video(
        db=db,
        file_buffer=file_buffer,
        file_name=upload_file.filename or "video.mp4",
        file_size=upload_file.size or len(file_buffer),
        file_mime_type=mime_type,
        dto=dto,
        uploader_id=current_user["userId"]
    )

    return {
        "success": True,
        "message": "Video uploaded successfully",
        "data": {
            "id": str(video_record.id),
            "title": video_record.title,
            "filename": video_record.storedFilename,
            "size": float(video_record.fileSize),
            "streamUrl": f"/videos/stream/{video_record.id}"
        }
    }


@router.get("", status_code=status.HTTP_200_OK)
async def get_videos(
    page: int = 1,
    limit: int = 10,
    category: Optional[str] = None,
    visibility: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    sortBy: str = "createdAt",
    sortOrder: str = "DESC",
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    query = VideoQuerySchema(
        page=page,
        limit=limit,
        category=category,
        visibility=visibility,
        status=status,
        search=search,
        sortBy=sortBy,
        sortOrder=sortOrder
    )
    user_id = current_user["userId"] if current_user else None
    result = await video_service.get_videos(db, query, user_id)
    return {
        "success": True,
        **result
    }


@router.get("/public", status_code=status.HTTP_200_OK)
async def get_public_videos(
    page: int = 1,
    limit: int = 20,
    category: Optional[str] = None,
    search: Optional[str] = None,
    sortBy: str = "createdAt",
    sortOrder: str = "DESC",
    db: AsyncSession = Depends(get_db)
):
    query = VideoQuerySchema(
        page=page,
        limit=limit,
        category=category,
        search=search,
        sortBy=sortBy,
        sortOrder=sortOrder
    )
    result = await video_service.get_public_videos(db, query)
    return {
        "success": True,
        **result
    }


@router.get("/my-videos", status_code=status.HTTP_200_OK)
async def get_my_videos(
    page: int = 1,
    limit: int = 10,
    category: Optional[str] = None,
    visibility: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    sortBy: str = "createdAt",
    sortOrder: str = "DESC",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = VideoQuerySchema(
        page=page,
        limit=limit,
        category=category,
        visibility=visibility,
        status=status,
        search=search,
        sortBy=sortBy,
        sortOrder=sortOrder
    )
    result = await video_service.get_videos_by_uploader(db, current_user["userId"], query)
    return {
        "success": True,
        **result
    }


@router.get("/my-recent", status_code=status.HTTP_200_OK)
async def get_my_recent_videos(
    limit: str = "5",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        limit_val = int(limit)
    except ValueError:
        limit_val = 5

    videos = await video_service.get_recent_videos_by_uploader(
        db=db,
        uploader_id=current_user["userId"],
        limit=limit_val
    )
    return {
        "success": True,
        "data": videos
    }


@router.get("/my-stats", status_code=status.HTTP_200_OK)
async def get_my_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    stats = await video_service.get_faculty_video_stats(db, current_user["userId"])
    return {
        "success": True,
        "data": stats
    }


@router.get("/analytics/details", status_code=status.HTTP_200_OK)
async def get_analytics_details(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    details = await video_service.get_analytics_details(db, current_user["userId"])
    return {
        "success": True,
        "data": details
    }


@router.get("/stream/{id}")
async def stream_video(
    id: str,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    from fastapi.responses import RedirectResponse
    import asyncio

    user_id = current_user["userId"] if current_user else None

    # Get the video record to check for CDN URL
    video = await video_service.get_video_by_id(db, id, user_id)

    # Increment view count in background
    asyncio.create_task(video_service.increment_view_count(db, id))

    # If the video has a CDN URL (ImageKit), redirect to it
    if video.cdnUrl:
        return RedirectResponse(url=video.cdnUrl, status_code=302)

    # Otherwise, stream from local storage
    relative_path = video.storagePath
    uploads_dir = os.path.join(os.getcwd(), "uploads")
    file_path = os.path.join(uploads_dir, relative_path)

    if not os.path.exists(file_path):
        from fastapi import HTTPException as HTTPExc
        raise HTTPExc(status_code=404, detail="Video file not found")

    file_size = os.path.getsize(file_path)
    guessed_type, _ = mimetypes.guess_type(file_path)
    mime_type = guessed_type or "video/mp4"

    range_header = request.headers.get("range")

    if range_header:
        # Range header format: bytes=start-end
        range_str = range_header.replace("bytes=", "")
        parts = range_str.split("-")
        start = int(parts[0])
        end = int(parts[1]) if parts[1] else file_size - 1
        
        # Guard limits
        start = max(0, min(start, file_size - 1))
        end = max(start, min(end, file_size - 1))
        
        chunk_size = end - start + 1

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Content-Type": mime_type
        }
        
        return StreamingResponse(
            range_generator(file_path, start, chunk_size),
            status_code=status.HTTP_206_PARTIAL_CONTENT,
            headers=headers
        )
    else:
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": mime_type
        }
        
        async def full_file_generator():
            async with aiofiles.open(file_path, mode="rb") as f:
                while chunk := await f.read(1024 * 1024):
                    yield chunk

        return StreamingResponse(
            full_file_generator(),
            status_code=status.HTTP_200_OK,
            headers=headers
        )


@router.get("/{id}", status_code=status.HTTP_200_OK)
async def get_video(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    user_id = current_user["userId"] if current_user else None
    video = await video_service.get_video_by_id(db, id, user_id)
    return {
        "success": True,
        "data": video
    }


@router.patch("/{id}", status_code=status.HTTP_200_OK)
async def update_video(
    id: str,
    dto: UpdateVideoSchema,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    video = await video_service.update_video(db, id, dto, current_user["userId"])
    return {
        "success": True,
        "message": "Video updated successfully",
        "data": video
    }


@router.put("/{id}", status_code=status.HTTP_200_OK)
async def put_update_video(
    id: str,
    dto: UpdateVideoSchema,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    video = await video_service.update_video(db, id, dto, current_user["userId"])
    return {
        "success": True,
        "message": "Video updated successfully",
        "data": video
    }


@router.patch("/{id}/visibility", status_code=status.HTTP_200_OK)
async def update_video_visibility(
    id: str,
    dto: UpdateVisibilitySchema,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    video = await video_service.update_video(
        db, id, UpdateVideoSchema(visibility=dto.visibility), current_user["userId"]
    )
    return {
        "success": True,
        "message": "Video visibility updated successfully",
        "data": video
    }


@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_video(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    await video_service.delete_video(db, id, current_user["userId"])
    return {
        "success": True,
        "message": "Video deleted successfully"
    }
