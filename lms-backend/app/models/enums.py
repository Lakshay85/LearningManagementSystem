from enum import Enum

class UserRole(str, Enum):
    STUDENT = 'student'
    FACULTY = 'faculty'
    PARENT = 'parent'
    ADMIN = 'admin'

class UserStatus(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    SUSPENDED = 'suspended'
    PENDING = 'pending'

class SubscriptionType(str, Enum):
    FREE = 'free'
    PREMIUM = 'premium'
    ENTERPRISE = 'enterprise'

class SubscriptionStatus(str, Enum):
    ACTIVE = 'active'
    EXPIRED = 'expired'
    TRIAL = 'trial'
    CANCELLED = 'cancelled'

class CourseCategory(str, Enum):
    PROGRAMMING = 'programming'
    WEB_DEVELOPMENT = 'web_development'
    MOBILE_DEVELOPMENT = 'mobile_development'
    DATA_SCIENCE = 'data_science'
    MACHINE_LEARNING = 'machine_learning'
    DESIGN = 'design'
    BUSINESS = 'business'
    MARKETING = 'marketing'
    PHOTOGRAPHY = 'photography'
    MUSIC = 'music'
    LANGUAGE = 'language'
    ACADEMICS = 'academics'
    OTHER = 'other'

class CourseLevel(str, Enum):
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
    ALL_LEVELS = 'all_levels'

class CourseStatus(str, Enum):
    DRAFT = 'draft'
    PENDING_REVIEW = 'pending_review'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'

class QuizStatus(str, Enum):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'

class CourseVisibility(str, Enum):
    PUBLIC = 'public'
    PRIVATE = 'private'
    UNLISTED = 'unlisted'

class ContentType(str, Enum):
    VIDEO = 'video'
    DOCUMENT = 'document'
    TEXT = 'text'
    QUIZ = 'quiz'
    ASSIGNMENT = 'assignment'

class DocumentType(str, Enum):
    PDF = 'pdf'
    WORD = 'word'
    POWERPOINT = 'powerpoint'
    EXCEL = 'excel'
    OTHER = 'other'

class EnrollmentStatus(str, Enum):
    ACTIVE = 'active'
    COMPLETED = 'completed'
    DROPPED = 'dropped'
    EXPIRED = 'expired'

class VideoStatus(str, Enum):
    PROCESSING = 'processing'
    READY = 'ready'
    FAILED = 'failed'
    DELETED = 'deleted'

class VideoVisibility(str, Enum):
    PRIVATE = 'private'
    PUBLIC = 'public'
    UNLISTED = 'unlisted'

class VideoCategory(str, Enum):
    LECTURE = 'lecture'
    TUTORIAL = 'tutorial'
    LAB = 'lab'
    SEMINAR = 'seminar'
    WORKSHOP = 'workshop'
    OTHER = 'other'

class DocumentVisibility(str, Enum):
    PRIVATE = 'private'
    PUBLIC = 'public'
    UNLISTED = 'unlisted'

class NotificationType(str, Enum):
    COURSE_PUBLISHED = 'course_published'
    COURSE_UPDATED = 'course_updated'
    CONTENT_ADDED = 'content_added'
    ENROLLMENT_SUCCESS = 'enrollment_success'
    NEW_ENROLLMENT = 'new_enrollment'
    VIDEO_UPLOADED = 'video_uploaded'
    VIDEO_PROCESSED = 'video_processed'
    DOCUMENT_UPLOADED = 'document_uploaded'
    SYSTEM_ANNOUNCEMENT = 'system_announcement'
    REMINDER = 'reminder'

class NotificationReferenceType(str, Enum):
    COURSE = 'course'
    VIDEO = 'video'
    DOCUMENT = 'document'
    USER = 'user'
    ENROLLMENT = 'enrollment'
