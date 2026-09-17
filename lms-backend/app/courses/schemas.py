from pydantic import BaseModel, Field
from typing import Optional, List
from app.models.enums import CourseCategory, CourseLevel, CourseVisibility, CourseStatus

class CreateCourseSchema(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    subtitle: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    category: Optional[CourseCategory] = None
    subcategory: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    language: Optional[str] = Field(None, max_length=10)
    level: Optional[CourseLevel] = None
    prerequisites: Optional[str] = None
    learningObjectives: Optional[str] = None
    targetAudience: Optional[str] = None
    visibility: Optional[CourseVisibility] = None
    isFree: Optional[bool] = None
    price: Optional[float] = None
    discountPrice: Optional[float] = None
    currency: Optional[str] = Field(None, max_length=3)

class UpdateCourseSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    subtitle: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    category: Optional[CourseCategory] = None
    subcategory: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    language: Optional[str] = Field(None, max_length=10)
    level: Optional[CourseLevel] = None
    prerequisites: Optional[str] = None
    learningObjectives: Optional[str] = None
    targetAudience: Optional[str] = None
    visibility: Optional[CourseVisibility] = None
    status: Optional[CourseStatus] = None
    isFree: Optional[bool] = None
    price: Optional[float] = None
    discountPrice: Optional[float] = None
    currency: Optional[str] = Field(None, max_length=3)

class CreateSectionSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    order: Optional[int] = None
    isPreview: Optional[bool] = None

class UpdateSectionSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    order: Optional[int] = None
    isPreview: Optional[bool] = None

class CreateContentSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    order: Optional[int] = None
    isPreview: Optional[bool] = None
    isRequired: Optional[bool] = None
    estimatedMinutes: Optional[int] = None
    videoId: Optional[str] = None
    quizId: Optional[str] = None
    textContent: Optional[str] = None

class UploadDocumentSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    order: Optional[int] = None
    isPreview: Optional[bool] = None
    isRequired: Optional[bool] = None
