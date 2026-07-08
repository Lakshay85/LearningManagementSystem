class Exchanges:
    USER = 'lms.user.events'
    COURSE = 'lms.course.events'
    DOCUMENT = 'lms.document.events'
    RAG = 'lms.rag.events'
    NOTIFICATION = 'lms.notification.events'

class RoutingKeys:
    # User events
    USER_CREATED = 'user.created'
    USER_UPDATED = 'user.updated'
    USER_DELETED = 'user.deleted'

    # Course events
    COURSE_CREATED = 'course.created'
    COURSE_UPDATED = 'course.updated'
    COURSE_DELETED = 'course.deleted'
    COURSE_PUBLISHED = 'course.published'
    CONTENT_ADDED_TO_COURSE = 'course.content.added'

    # Enrollment events
    STUDENT_ENROLLED = 'enrollment.created'
    STUDENT_UNENROLLED = 'enrollment.deleted'

    # Document events
    DOCUMENT_UPLOADED = 'document.uploaded'
    DOCUMENT_PROCESSED = 'document.processed'
    DOCUMENT_DELETED = 'document.deleted'
    DOCUMENT_LINKED_TO_COURSE = 'document.linked'

    # Video events
    VIDEO_UPLOADED = 'video.uploaded'
    VIDEO_LINKED_TO_COURSE = 'video.linked'

    # Notification events
    NOTIFICATION_CREATED = 'notification.created'

class Queues:
    RAG_DOCUMENT_PROCESSING = 'rag.document.processing'
    RAG_USER_EVENTS = 'rag.user.events'
    RAG_COURSE_EVENTS = 'rag.course.events'
    NOTIFICATION_EVENTS = 'notification.events'
