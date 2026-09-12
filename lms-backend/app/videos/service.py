from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID
from sqlalchemy import select, update, and_, or_, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.models import Video, CourseContent, CourseEnrollment, User
from app.models.enums import VideoStatus, VideoVisibility, VideoCategory, EnrollmentStatus
from app.storage.service import storage_service
from app.messaging.service import messaging_service
from app.messaging.events import VideoUploadedEvent
from app.videos.utils import (
    validate_video_file, sanitize_filename,
    generate_unique_filename, get_video_storage_path
)

class VideoService:
    async def upload_video(
        self,
        db: AsyncSession,
        file_buffer: bytes,
        file_name: str,
        file_size: int,
        file_mime_type: str,
        dto: Any,
        uploader_id: str
    ) -> Video:
        # Validate
        is_valid, err = validate_video_file(file_name, file_mime_type, file_size)
        if not is_valid:
            raise HTTPException(status_code=400, detail=err)

        sanitized = sanitize_filename(file_name)
        unique_name = generate_unique_filename(sanitized)
        storage_path = get_video_storage_path(unique_name)

        # Parse category and visibility enums safely
        category_val = VideoCategory.OTHER
        if getattr(dto, "category", None):
            try:
                category_val = VideoCategory(str(dto.category).lower().strip())
            except (ValueError, AttributeError):
                category_val = VideoCategory.OTHER

        visibility_val = VideoVisibility.PRIVATE
        if getattr(dto, "visibility", None):
            try:
                visibility_val = VideoVisibility(str(dto.visibility).lower().strip())
            except (ValueError, AttributeError):
                visibility_val = VideoVisibility.PRIVATE

        imagekit_file_id = None
        try:
            # Upload
            upload_result = await storage_service.upload(file_buffer, storage_path, file_mime_type)

            # Extract ImageKit metadata if available
            if isinstance(upload_result, dict):
                imagekit_file_id = upload_result.get("fileId")
                cdn_url = upload_result.get("cdnUrl")
            else:
                imagekit_file_id = None
                cdn_url = None

            # Save in database
            video = Video(
                title=dto.title,
                description=dto.description,
                category=category_val,
                visibility=visibility_val,
                status=VideoStatus.READY,
                originalFilename=sanitized,
                storedFilename=unique_name,
                mimeType=file_mime_type,
                fileSize=file_size,
                storagePath=storage_path,
                imagekitFileId=imagekit_file_id,
                cdnUrl=cdn_url,
                uploaderId=UUID(uploader_id)
            )

            db.add(video)
            await db.commit()
            await db.refresh(video)

            # Publish event
            try:
                await messaging_service.publish_video_uploaded(
                    VideoUploadedEvent(
                        videoId=str(video.id),
                        userId=uploader_id,
                        title=video.title,
                        uploadedAt=video.createdAt or datetime.now()
                    )
                )
            except Exception as e:
                print(f"Failed to publish video upload event: {str(e)}")

            return video
        except Exception as e:
            # Clean up if save fails
            try:
                if imagekit_file_id:
                    await storage_service.delete_by_file_id(imagekit_file_id)
                elif await storage_service.exists(storage_path):
                    await storage_service.delete(storage_path)
            except Exception as cleanup_err:
                print(f"Cleanup failed: {str(cleanup_err)}")
            
            raise HTTPException(status_code=400, detail=f"Failed to upload video: {str(e)}")

    async def get_video_by_id(self, db: AsyncSession, id: str, user_id: Optional[str] = None) -> Video:
        try:
            video_uuid = UUID(id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Video not found")

        stmt = select(Video).where(Video.id == video_uuid).options(selectinload(Video.uploader))
        result = await db.execute(stmt)
        video = result.scalar_one_or_none()

        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        is_owner = str(video.uploaderId) == user_id
        is_public = video.visibility == VideoVisibility.PUBLIC

        if is_owner or is_public:
            return video

        # Check enrollment for private videos
        if video.visibility == VideoVisibility.PRIVATE and user_id:
            # Check if this video is part of any course content
            content_stmt = select(CourseContent).where(CourseContent.videoId == video_uuid).limit(1)
            content_res = await db.execute(content_stmt)
            content = content_res.scalar_one_or_none()

            if content:
                # Check active student enrollment
                enroll_stmt = select(CourseEnrollment).where(
                    and_(
                        CourseEnrollment.courseId == content.courseId,
                        CourseEnrollment.studentId == UUID(user_id),
                        CourseEnrollment.status == EnrollmentStatus.ACTIVE
                    )
                ).limit(1)
                enroll_res = await db.execute(enroll_stmt)
                if enroll_res.scalar_one_or_none():
                    return video

        raise HTTPException(status_code=403, detail="You do not have access to this video")

    async def get_videos(self, db: AsyncSession, query: Any, user_id: Optional[str] = None) -> Dict[str, Any]:
        page = query.page
        limit = query.limit
        skip = (page - 1) * limit

        filters = []

        if query.category:
            filters.append(Video.category == query.category)

        if query.visibility:
            filters.append(Video.visibility == query.visibility)

        # Status filter
        if query.status:
            filters.append(Video.status == query.status)
        else:
            filters.append(Video.status == VideoStatus.READY)

        # Visibility filters: public or owner if logged in
        if not user_id:
            filters.append(Video.visibility == VideoVisibility.PUBLIC)
        else:
            filters.append(or_(
                Video.visibility == VideoVisibility.PUBLIC,
                Video.uploaderId == UUID(user_id)
            ))

        if query.search:
            filters.append(or_(
                Video.title.ilike(f"%{query.search}%"),
                Video.description.ilike(f"%{query.search}%")
            ))

        # Count total
        count_stmt = select(func.count()).select_from(Video).where(and_(*filters))
        count_res = await db.execute(count_stmt)
        total = count_res.scalar() or 0

        # Build query
        stmt = select(Video).where(and_(*filters)).options(selectinload(Video.uploader)).offset(skip).limit(limit)

        # Ordering
        order_field = getattr(Video, query.sortBy, Video.createdAt)
        if query.sortOrder == "ASC":
            stmt = stmt.order_by(asc(order_field))
        else:
            stmt = stmt.order_by(desc(order_field))

        result = await db.execute(stmt)
        videos = result.scalars().all()

        return {
            "data": list(videos),
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": (total + limit - 1) // limit if limit > 0 else 1
        }

    async def get_public_videos(self, db: AsyncSession, query: Any) -> Dict[str, Any]:
        page = query.page
        limit = query.limit
        skip = (page - 1) * limit

        filters = [
            Video.visibility == VideoVisibility.PUBLIC,
            Video.status == VideoStatus.READY
        ]

        if query.category:
            filters.append(Video.category == query.category)

        if query.search:
            filters.append(or_(
                Video.title.ilike(f"%{query.search}%"),
                Video.description.ilike(f"%{query.search}%")
            ))

        # Count total
        count_stmt = select(func.count()).select_from(Video).where(and_(*filters))
        count_res = await db.execute(count_stmt)
        total = count_res.scalar() or 0

        stmt = select(Video).where(and_(*filters)).options(selectinload(Video.uploader)).offset(skip).limit(limit)

        order_field = getattr(Video, query.sortBy, Video.createdAt)
        if query.sortOrder == "ASC":
            stmt = stmt.order_by(asc(order_field))
        else:
            stmt = stmt.order_by(desc(order_field))

        result = await db.execute(stmt)
        videos = result.scalars().all()

        return {
            "data": list(videos),
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": (total + limit - 1) // limit if limit > 0 else 1
        }

    async def get_videos_by_uploader(self, db: AsyncSession, uploader_id: str, query: Any) -> Dict[str, Any]:
        page = query.page
        limit = query.limit
        skip = (page - 1) * limit

        filters = [
            Video.uploaderId == UUID(uploader_id)
        ]

        if query.category:
            filters.append(Video.category == query.category)

        if query.visibility:
            filters.append(Video.visibility == query.visibility)

        if query.status:
            filters.append(Video.status == query.status)

        if query.search:
            filters.append(or_(
                Video.title.ilike(f"%{query.search}%"),
                Video.description.ilike(f"%{query.search}%")
            ))

        count_stmt = select(func.count()).select_from(Video).where(and_(*filters))
        count_res = await db.execute(count_stmt)
        total = count_res.scalar() or 0

        stmt = select(Video).where(and_(*filters)).offset(skip).limit(limit)

        order_field = getattr(Video, query.sortBy, Video.createdAt)
        if query.sortOrder == "ASC":
            stmt = stmt.order_by(asc(order_field))
        else:
            stmt = stmt.order_by(desc(order_field))

        result = await db.execute(stmt)
        videos = result.scalars().all()

        return {
            "data": list(videos),
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": (total + limit - 1) // limit if limit > 0 else 1
        }

    async def update_video(self, db: AsyncSession, id: str, dto: Any, user_id: str) -> Video:
        try:
            video_uuid = UUID(id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Video not found")

        video = await db.get(Video, video_uuid)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        if str(video.uploaderId) != user_id:
            raise HTTPException(status_code=403, detail="You can only update your own videos")

        update_data = dto.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(video, key, value)

        await db.commit()
        await db.refresh(video)
        return video

    async def delete_video(self, db: AsyncSession, id: str, user_id: str):
        try:
            video_uuid = UUID(id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Video not found")

        video = await db.get(Video, video_uuid)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        if str(video.uploaderId) != user_id:
            raise HTTPException(status_code=403, detail="You can only delete your own videos")

        # Delete physical files
        try:
            if video.imagekitFileId:
                await storage_service.delete_by_file_id(video.imagekitFileId)
            elif video.storagePath:
                await storage_service.delete(video.storagePath)
            if video.thumbnailPath:
                await storage_service.delete(video.thumbnailPath)
        except Exception as e:
            print(f"Failed to delete video files: {str(e)}")

        await db.delete(video)
        await db.commit()

    async def increment_view_count(self, db: AsyncSession, id: str):
        try:
            video_uuid = UUID(id)
            await db.execute(
                update(Video)
                .where(Video.id == video_uuid)
                .values(viewCount=Video.viewCount + 1)
            )
            await db.commit()
        except Exception as e:
            print(f"Failed to increment view count: {str(e)}")

    async def get_video_stream_path(self, db: AsyncSession, id: str, user_id: Optional[str] = None) -> str:
        video = await self.get_video_by_id(db, id, user_id)
        return video.storagePath

    async def get_recent_videos_by_uploader(self, db: AsyncSession, uploader_id: str, limit: int = 5) -> List[Video]:
        stmt = (
            select(Video)
            .where(Video.uploaderId == UUID(uploader_id))
            .order_by(desc(Video.createdAt))
            .limit(min(limit, 10))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_faculty_video_stats(self, db: AsyncSession, uploader_id: str) -> Dict[str, int]:
        uploader_uuid = UUID(uploader_id)

        # Total count
        total_videos = await db.scalar(
            select(func.count()).select_from(Video).where(Video.uploaderId == uploader_uuid)
        ) or 0

        # Total views
        total_views_res = await db.execute(
            select(func.sum(Video.viewCount)).where(Video.uploaderId == uploader_uuid)
        )
        total_views = int(total_views_res.scalar() or 0)

        # Videos this month
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        videos_this_month = await db.scalar(
            select(func.count())
            .select_from(Video)
            .where(
                and_(
                    Video.uploaderId == uploader_uuid,
                    Video.createdAt >= start_of_month
                )
            )
        ) or 0

        # Calculate views growth (compare this month to last month)
        start_of_last_month = start_of_month - timedelta(days=30)  # rough approximation of last month
        
        last_month_views_res = await db.execute(
            select(func.sum(Video.viewCount))
            .where(
                and_(
                    Video.uploaderId == uploader_uuid,
                    Video.createdAt >= start_of_last_month,
                    Video.createdAt < start_of_month
                )
            )
        )
        last_month_views = int(last_month_views_res.scalar() or 0)
        
        views_growth = 0
        if last_month_views > 0:
            views_growth = round(((total_views - last_month_views) / last_month_views) * 100)

        return {
            "totalVideos": total_videos,
            "totalViews": total_views,
            "videosThisMonth": videos_this_month,
            "viewsGrowth": views_growth,
        }

    async def get_analytics_details(self, db: AsyncSession, uploader_id: str) -> Dict[str, Any]:
        stmt = (
            select(Video)
            .where(Video.uploaderId == UUID(uploader_id))
            .order_by(desc(Video.createdAt))
        )
        result = await db.execute(stmt)
        videos = result.scalars().all()

        published = []
        draft = []
        for v in videos:
            data = {
                "id": str(v.id),
                "title": v.title,
                "createdAt": v.createdAt,
                "updatedAt": v.updatedAt,
                "visibility": v.visibility,
                "status": v.status
            }
            if v.visibility == VideoVisibility.PUBLIC:
                published.append(data)
            else:
                draft.append(data)

        return {
            "totalVideos": len(videos),
            "publishedVideos": published,
            "draftVideos": draft,
        }
