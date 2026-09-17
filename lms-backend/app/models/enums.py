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

class Permission(str, Enum):
    # User management
    USERS_VIEW = 'users.view'
    USERS_MANAGE = 'users.manage'          # create, edit, activate/deactivate
    USERS_DELETE = 'users.delete'
    
    # Course oversight
    COURSES_VIEW_ALL = 'courses.view_all'  # see all faculty courses
    COURSES_MANAGE = 'courses.manage'      # unpublish/flag courses
    
    # Content oversight
    CONTENT_VIEW_ALL = 'content.view_all'  # see all docs/videos
    CONTENT_MANAGE = 'content.manage'      # remove/flag content
    
    # Quiz oversight
    QUIZZES_VIEW_ALL = 'quizzes.view_all'
    QUIZZES_MANAGE = 'quizzes.manage'
    
    # LLM controls
    LLM_VIEW_USAGE = 'llm.view_usage'     # view usage analytics
    LLM_CONFIGURE = 'llm.configure'       # set per-user limits
    
    # System settings
    SYSTEM_SETTINGS = 'system.settings'    # global platform config
    AUDIT_LOGS_VIEW = 'audit.logs_view'    # view audit trail
    
    # Admin management
    ADMIN_MANAGE = 'admin.manage'          # create/modify other admins

class AuditAction(str, Enum):
    USER_CREATED = 'user.created'
    USER_UPDATED = 'user.updated'
    USER_ACTIVATED = 'user.activated'
    USER_DEACTIVATED = 'user.deactivated'
    USER_DELETED = 'user.deleted'
    USER_ROLE_CHANGED = 'user.role_changed'
    LLM_LIMIT_CHANGED = 'llm.limit_changed'
    COURSE_UNPUBLISHED = 'course.unpublished'
    CONTENT_REMOVED = 'content.removed'
    QUIZ_REMOVED = 'quiz.removed'
    SYSTEM_SETTING_CHANGED = 'system.setting_changed'
    ADMIN_LOGIN = 'admin.login'

