from pydantic import BaseModel, Field
from typing import Optional
from app.models.enums import VideoCategory, VideoVisibility, VideoStatus

class UploadVideoSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[VideoCategory] = None
    visibility: Optional[VideoVisibility] = None

class UpdateVideoSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[VideoCategory] = None
    visibility: Optional[VideoVisibility] = None
    status: Optional[VideoStatus] = None

class UpdateVisibilitySchema(BaseModel):
    visibility: VideoVisibility

class VideoQuerySchema(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    category: Optional[VideoCategory] = None
    visibility: Optional[VideoVisibility] = None
    status: Optional[VideoStatus] = None
    search: Optional[str] = None
    sortBy: str = "createdAt"
    sortOrder: str = "DESC"
