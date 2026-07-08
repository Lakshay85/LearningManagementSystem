from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class UserCreatedEvent(BaseModel):
    userId: str
    email: str
    firstName: str
    lastName: str
    role: str
    createdAt: datetime

class UserUpdatedEvent(BaseModel):
    userId: str
    email: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    updatedAt: datetime

class UserDeletedEvent(BaseModel):
    userId: str
    deletedAt: datetime

class CourseCreatedEvent(BaseModel):
    courseId: str
    title: str
    description: Optional[str] = None
    instructorId: str
    category: Optional[str] = None
    createdAt: datetime

class CourseUpdatedEvent(BaseModel):
    courseId: str
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    updatedAt: datetime

class CoursePublishedEvent(BaseModel):
    courseId: str
    title: str
    instructorId: str
    publishedAt: datetime

class ContentAddedToCourseEvent(BaseModel):
    courseId: str
    courseTitle: str
    instructorId: str
    contentType: str  # 'video' or 'document'
    contentId: str
    contentTitle: str
    addedAt: datetime

class StudentEnrolledEvent(BaseModel):
    enrollmentId: str
    userId: str
    courseId: str
    courseTitle: str
    instructorId: str
    studentName: str
    enrolledAt: datetime

class DocumentUploadedEvent(BaseModel):
    documentId: str
    userId: str
    courseId: Optional[str] = None
    fileName: str
    fileType: str
    fileSize: int
    uploadedAt: datetime

class DocumentProcessedEvent(BaseModel):
    documentId: str
    ragDocId: str
    status: str  # 'completed' | 'failed'
    chunksCreated: Optional[int] = None
    error: Optional[str] = None
    processedAt: datetime

class DocumentLinkedToCourseEvent(BaseModel):
    documentId: str
    ragDocId: str
    courseId: str
    linkedAt: datetime

class VideoUploadedEvent(BaseModel):
    videoId: str
    userId: str
    title: str
    uploadedAt: datetime

class VideoLinkedToCourseEvent(BaseModel):
    videoId: str
    courseId: str
    linkedAt: datetime

class NotificationEvent(BaseModel):
    userId: str
    type: str
    title: str
    message: str
    referenceType: Optional[str] = None
    referenceId: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
