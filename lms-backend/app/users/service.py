from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy import select, delete, and_, or_, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.models import User, Student, Video, Document
from app.models.enums import VideoStatus
from app.storage.service import storage_service

class UserService:
    async def get_all_users(self, db: AsyncSession) -> Dict[str, Any]:
        result = await db.execute(
            select(User)
            .order_by(desc(User.createdAt))
        )
        users = result.scalars().all()
        
        users_list = []
        for u in users:
            users_list.append({
                "id": str(u.id),
                "email": u.email,
                "firstName": u.firstName,
                "lastName": u.lastName,
                "role": u.role,
                "phoneNumber": u.phoneNumber,
                "isActive": u.isActive,
                "status": u.status,
                "subscriptionType": u.subscriptionType,
                "subscriptionStatus": u.subscriptionStatus,
                "createdAt": u.createdAt
            })
            
        return {
            "message": "Users fetched successfully",
            "count": len(users_list),
            "users": users_list
        }

    async def upload_profile_picture(
        self, 
        db: AsyncSession, 
        user_id: str, 
        file_buffer: bytes, 
        original_filename: str,
        mime_type: str
    ) -> Dict[str, str]:
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID")

        user = await db.get(User, user_uuid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        file_ext = original_filename.split(".")[-1] if "." in original_filename else "jpg"
        filename = f"profiles/{user_id}-{int(datetime.now().timestamp())}.{file_ext}"

        # Upload file to storage
        upload_result = await storage_service.upload(file_buffer, filename, mime_type)
        
        # Use CDN URL if available (ImageKit), otherwise construct local URL
        if isinstance(upload_result, dict) and upload_result.get("cdnUrl"):
            public_url = upload_result["cdnUrl"]
        else:
            public_url = storage_service.get_public_url(filename)
        
        # Update user's profilePicture
        user.profilePicture = public_url
        await db.commit()

        return {
            "message": "Profile picture updated successfully",
            "profilePicture": public_url
        }

    async def delete_user(self, db: AsyncSession, user_id: str) -> Dict[str, str]:
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID")

        user = await db.get(User, user_uuid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        await db.delete(user)
        await db.commit()

        return {
            "message": "User deleted successfully",
            "userId": user_id
        }

    async def delete_all_users(self, db: AsyncSession) -> Dict[str, Any]:
        # Delete students first due to foreign keys
        await db.execute(delete(Student))
        
        # Delete users
        result = await db.execute(delete(User))
        await db.commit()

        return {
            "message": "All users deleted successfully",
            "deletedCount": result.rowcount
        }

    async def get_all_content(
        self,
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        limit: int = 12,
        search: Optional[str] = None,
        file_type: Optional[str] = None,
        time_range: Optional[str] = None,
        size_range: Optional[str] = None,
        sort_by: str = "newest"
    ) -> Dict[str, Any]:
        skip = (page - 1) * limit

        # Filter: Date range
        date_filter = None
        if time_range:
            now = datetime.now()
            if time_range == "today":
                date_filter = datetime(now.year, now.month, now.day, 0, 0, 0)
            elif time_range == "week":
                date_filter = now - timedelta(days=7)
            elif time_range == "month":
                date_filter = now - timedelta(days=30)
            elif time_range == "quarter":
                date_filter = now - timedelta(days=90)
            elif time_range == "year":
                date_filter = now - timedelta(days=365)

        # Filter: File size range (MB to bytes)
        size_min = None
        size_max = None
        if size_range:
            MB = 1024 * 1024
            if size_range == "small":
                size_max = 10 * MB
            elif size_range == "medium":
                size_min = 10 * MB
                size_max = 100 * MB
            elif size_range == "large":
                size_min = 100 * MB
                size_max = 500 * MB
            elif size_range == "xlarge":
                size_min = 500 * MB

        # Query builder for Videos
        video_filters = [
            Video.uploaderId == UUID(user_id),
            Video.status != VideoStatus.DELETED
        ]

        if search:
            video_filters.append(or_(
                Video.title.ilike(f"%{search}%"),
                Video.description.ilike(f"%{search}%")
            ))

        if date_filter:
            video_filters.append(Video.createdAt >= date_filter)

        if size_min is not None:
            video_filters.append(Video.fileSize >= size_min)

        if size_max is not None:
            video_filters.append(Video.fileSize <= size_max)

        # Query builder for Documents
        doc_filters = [
            Document.uploaderId == UUID(user_id)
        ]

        if search:
            doc_filters.append(or_(
                Document.title.ilike(f"%{search}%"),
                Document.description.ilike(f"%{search}%")
            ))

        if date_filter:
            doc_filters.append(Document.createdAt >= date_filter)

        if size_min is not None:
            doc_filters.append(Document.fileSize >= size_min)

        if size_max is not None:
            doc_filters.append(Document.fileSize <= size_max)

        # Fetch based on file_type request
        videos = []
        documents = []

        # If file_type is 'video' or not specified, fetch videos
        if not file_type or file_type == "video":
            stmt = select(Video).where(and_(*video_filters))
            result = await db.execute(stmt)
            videos = result.scalars().all()

        # If file_type is NOT 'video', fetch documents
        if not file_type or file_type != "video":
            if file_type and file_type != "video":
                if file_type == "pdf":
                    doc_filters.append(Document.mimeType.like("%pdf%"))
                elif file_type == "word":
                    doc_filters.append(or_(
                        Document.mimeType.like("%msword%"),
                        Document.mimeType.like("%wordprocessingml%")
                    ))
                elif file_type == "excel":
                    doc_filters.append(or_(
                        Document.mimeType.like("%ms-excel%"),
                        Document.mimeType.like("%spreadsheetml%")
                    ))
                elif file_type == "powerpoint":
                    doc_filters.append(or_(
                        Document.mimeType.like("%ms-powerpoint%"),
                        Document.mimeType.like("%presentationml%")
                    ))
                elif file_type == "image":
                    doc_filters.append(Document.mimeType.like("image/%"))

            stmt = select(Document).where(and_(*doc_filters))
            result = await db.execute(stmt)
            documents = result.scalars().all()

        # Normalize results list
        combined = []
        for v in videos:
            combined.append({
                "id": str(v.id),
                "title": v.title,
                "description": v.description,
                "type": "video",
                "mimeType": v.mimeType,
                "fileSize": float(v.fileSize),
                "createdAt": v.createdAt,
                "updatedAt": v.updatedAt,
                "category": v.category,
                "visibility": v.visibility,
                "status": v.status,
                "duration": float(v.duration) if v.duration is not None else None,
                "viewCount": v.viewCount,
                "originalFilename": v.originalFilename,
            })

        for d in documents:
            combined.append({
                "id": str(d.id),
                "title": d.title,
                "description": d.description,
                "type": "document",
                "mimeType": d.mimeType,
                "fileSize": float(d.fileSize),
                "createdAt": d.createdAt,
                "updatedAt": d.updatedAt,
                "documentType": d.documentType,
                "documentId": str(d.id),
                "originalFilename": d.originalFilename,
                "isDownloadable": d.isDownloadable,
            })

        # Sorting logic
        if sort_by == "oldest":
            combined.sort(key=lambda x: x["createdAt"])
        elif sort_by == "title":
            combined.sort(key=lambda x: x["title"].lower())
        elif sort_by == "size-desc":
            combined.sort(key=lambda x: x["fileSize"], reverse=True)
        elif sort_by == "size-asc":
            combined.sort(key=lambda x: x["fileSize"])
        elif sort_by == "popular":
            # Only video type has viewCount, document defaults to 0 views
            combined.sort(key=lambda x: x.get("viewCount", 0), reverse=True)
        else:  # newest
            combined.sort(key=lambda x: x["createdAt"], reverse=True)

        # Pagination slicing
        total = len(combined)
        paginated = combined[skip: skip + limit]
        total_pages = (total + limit - 1) // limit if limit > 0 else 1

        return {
            "success": True,
            "message": "Content fetched successfully",
            "data": paginated,
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": total_pages
        }
