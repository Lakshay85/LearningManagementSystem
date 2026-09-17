import uuid
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, 
    Numeric, Text, Date, Index, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as pgEnum
from sqlalchemy.orm import relationship as orm_relationship
from app.database import Base
from app.models.enums import (
    UserRole, UserStatus, SubscriptionType, SubscriptionStatus,
    CourseCategory, CourseLevel, CourseStatus, CourseVisibility,
    ContentType, DocumentType, EnrollmentStatus, VideoStatus,
    VideoVisibility, VideoCategory, DocumentVisibility,
    NotificationType, NotificationReferenceType, QuizStatus
)

enum_val = lambda x: [item.value for item in x]

class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    role = Column(pgEnum('admin', 'faculty', 'student', 'parent', name='users_role_enum', create_type=False), nullable=False)
    firstName = Column(String, nullable=False)
    lastName = Column(String, nullable=False)
    phoneNumber = Column(String, nullable=True)
    dateOfBirth = Column(Date, nullable=True)
    gender = Column(String, nullable=True)
    profilePicture = Column(String, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, nullable=True)
    postalCode = Column(String, nullable=True)
    isActive = Column(Boolean, default=True)
    isEmailVerified = Column(Boolean, default=False)
    isPhoneVerified = Column(Boolean, default=False)
    status = Column(pgEnum('active', 'inactive', 'suspended', 'pending', name='users_status_enum', create_type=False), default=UserStatus.ACTIVE)
    subscriptionType = Column(pgEnum('free', 'premium', 'enterprise', name='users_subscriptiontype_enum', create_type=False), default=SubscriptionType.FREE)
    subscriptionStatus = Column(pgEnum('active', 'expired', 'trial', 'cancelled', name='users_subscriptionstatus_enum', create_type=False), default=SubscriptionStatus.TRIAL)
    subscriptionStartDate = Column(DateTime, nullable=True)
    subscriptionEndDate = Column(DateTime, nullable=True)
    lastLogin = Column(DateTime, nullable=True)
    refreshToken = Column(String, nullable=True)
    passwordResetToken = Column(String, nullable=True)
    passwordResetExpires = Column(DateTime, nullable=True)
    emailVerificationToken = Column(String, nullable=True)
    preferredLanguage = Column(String, nullable=True)
    timezone = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    student = orm_relationship("Student", back_populates="user", uselist=False, cascade="all, delete-orphan")
    teacher = orm_relationship("Teacher", back_populates="user", uselist=False, cascade="all, delete-orphan")
    parent = orm_relationship("Parent", back_populates="user", uselist=False, cascade="all, delete-orphan")
    admin = orm_relationship("Admin", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Student(Base):
    __tablename__ = 'students'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    userId = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    enrollmentNumber = Column(String, unique=True, nullable=True)
    grade = Column(String, nullable=True)
    section = Column(String, nullable=True)
    rollNumber = Column(String, nullable=True)
    parentId = Column(UUID(as_uuid=True), ForeignKey('parents.id', ondelete='SET NULL'), nullable=True)
    enrollmentDate = Column(Date, nullable=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = orm_relationship("User", back_populates="student")
    parent = orm_relationship("Parent", back_populates="children")


class Teacher(Base):
    __tablename__ = 'teachers'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    userId = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    employeeId = Column(String, unique=True, nullable=True)
    department = Column(String, nullable=True)
    specialization = Column(String, nullable=True)
    qualification = Column(String, nullable=True)
    experience = Column(Numeric(10, 2), nullable=True)
    joiningDate = Column(Date, nullable=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = orm_relationship("User", back_populates="teacher")


class Parent(Base):
    __tablename__ = 'parents'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    userId = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    occupation = Column(String, nullable=True)
    relationship = Column(String, nullable=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = orm_relationship("User", back_populates="parent")
    children = orm_relationship("Student", back_populates="parent")


class Admin(Base):
    __tablename__ = 'admins'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    userId = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    adminLevel = Column(String, nullable=True)
    permissions = Column(JSONB, nullable=True)
    department = Column(String, nullable=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = orm_relationship("User", back_populates="admin")


class Video(Base):
    __tablename__ = 'videos'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(pgEnum('lecture', 'tutorial', 'lab', 'seminar', 'workshop', 'other', name='videos_category_enum', create_type=False), default=VideoCategory.OTHER)
    visibility = Column(pgEnum('private', 'public', 'unlisted', name='videos_visibility_enum', create_type=False), default=VideoVisibility.PRIVATE)
    status = Column(pgEnum('processing', 'ready', 'failed', 'deleted', name='videos_status_enum', create_type=False), default=VideoStatus.PROCESSING)
    originalFilename = Column(String, nullable=False)
    storedFilename = Column(String, nullable=False)
    mimeType = Column(String, nullable=False)
    fileSize = Column(Numeric(20, 0), nullable=False)
    duration = Column(Numeric, nullable=True)
    thumbnailPath = Column(String, nullable=True)
    storagePath = Column(String, nullable=True)
    imagekitFileId = Column(String, nullable=True)
    cdnUrl = Column(String, nullable=True)
    viewCount = Column(Integer, default=0)
    uploaderId = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    metadata_json = Column("metadata", JSONB, nullable=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    uploader = orm_relationship("User")

    __table_args__ = (
        Index('ix_videos_uploaderId_status', 'uploaderId', 'status'),
        Index('ix_videos_visibility_status', 'visibility', 'status'),
        {'extend_existing': True}
    )


class Document(Base):
    __tablename__ = 'documents'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    originalFilename = Column(String, nullable=False)
    storedFilename = Column(String, nullable=False)
    storagePath = Column(String, nullable=False)
    mimeType = Column(String, nullable=False)
    fileSize = Column(Numeric(20, 0), nullable=False)
    documentType = Column(pgEnum('pdf', 'word', 'powerpoint', 'excel', 'other', name='documents_documenttype_enum', create_type=False), default=DocumentType.OTHER)
    visibility = Column(pgEnum('private', 'public', 'unlisted', name='documents_visibility_enum', create_type=False), default=DocumentVisibility.PRIVATE)
    imagekitFileId = Column(String, nullable=True)
    cdnUrl = Column(String, nullable=True)
    pageCount = Column(Integer, nullable=True)
    isDownloadable = Column(Boolean, default=True)
    uploaderId = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    metadata_json = Column("metadata", JSONB, nullable=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    uploader = orm_relationship("User")


class Course(Base):
    __tablename__ = 'courses'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    subtitle = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)
    slug = Column(String(250), unique=True, nullable=False)
    thumbnailUrl = Column(String, nullable=True)
    promoVideoUrl = Column(String, nullable=True)
    category = Column(pgEnum('programming', 'web_development', 'mobile_development', 'data_science', 'machine_learning', 'design', 'business', 'marketing', 'photography', 'music', 'language', 'academics', 'other', name='courses_category_enum', create_type=False), default=CourseCategory.OTHER)
    subcategory = Column(String(100), nullable=True)
    tags = Column(Text, nullable=True)
    language = Column(String(10), default='en')
    level = Column(pgEnum('beginner', 'intermediate', 'advanced', 'all_levels', name='courses_level_enum', create_type=False), default=CourseLevel.ALL_LEVELS)
    prerequisites = Column(Text, nullable=True)
    learningObjectives = Column(Text, nullable=True)
    targetAudience = Column(Text, nullable=True)
    status = Column(pgEnum('draft', 'pending_review', 'published', 'archived', name='courses_status_enum', create_type=False), default=CourseStatus.DRAFT)
    visibility = Column(pgEnum('private', 'public', 'unlisted', name='courses_visibility_enum', create_type=False), default=CourseVisibility.PRIVATE)
    isFree = Column(Boolean, default=True)
    price = Column(Numeric(10, 2), nullable=True)
    discountPrice = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), default='INR')
    estimatedDuration = Column(Integer, nullable=True)
    totalVideos = Column(Integer, default=0)
    totalDocuments = Column(Integer, default=0)
    enrollmentCount = Column(Integer, default=0)
    averageRating = Column(Numeric(3, 2), default=0.0)
    ratingCount = Column(Integer, default=0)
    publishedAt = Column(DateTime, nullable=True)
    instructorId = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    instructor = orm_relationship("User")
    sections = orm_relationship("CourseSection", back_populates="course", cascade="all, delete-orphan", order_by="CourseSection.order")

    __table_args__ = (
        Index('ix_courses_instructorId_status', 'instructorId', 'status'),
        Index('ix_courses_status_visibility', 'status', 'visibility'),
        {'extend_existing': True}
    )


class CourseSection(Base):
    __tablename__ = 'course_sections'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, nullable=False)
    isPreview = Column(Boolean, default=False)
    courseId = Column(UUID(as_uuid=True), ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    course = orm_relationship("Course", back_populates="sections")
    contents = orm_relationship("CourseContent", back_populates="section", cascade="all, delete-orphan", order_by="CourseContent.order")

    __table_args__ = (
        Index('ix_course_sections_courseId_order', 'courseId', 'order'),
        {'extend_existing': True}
    )


class Quiz(Base):
    __tablename__ = 'quizzes'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    courseId = Column(UUID(as_uuid=True), ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default=QuizStatus.DRAFT.value, nullable=False, index=True)
    timeLimitMinutes = Column(Integer, nullable=True)
    totalQuestions = Column(Integer, default=0)
    passingScore = Column(Integer, nullable=True)
    createdBy = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    publishedAt = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    course = orm_relationship("Course")
    creator = orm_relationship("User")
    questions = orm_relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan", order_by="QuizQuestion.order")
    submissions = orm_relationship("QuizSubmission", back_populates="quiz", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_quizzes_courseId_status', 'courseId', 'status'),
        {'extend_existing': True}
    )


class QuizQuestion(Base):
    __tablename__ = 'quiz_questions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quizId = Column(UUID(as_uuid=True), ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False, index=True)
    questionText = Column(Text, nullable=False)
    options = Column(JSONB, nullable=False)
    correctAnswer = Column(String, nullable=False)
    explanation = Column(Text, nullable=True)
    order = Column(Integer, nullable=False, default=0)
    points = Column(Integer, default=1)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    quiz = orm_relationship("Quiz", back_populates="questions")

    __table_args__ = (
        Index('ix_quiz_questions_quizId_order', 'quizId', 'order'),
        {'extend_existing': True}
    )


class QuizSubmission(Base):
    __tablename__ = 'quiz_submissions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quizId = Column(UUID(as_uuid=True), ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False, index=True)
    studentId = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    score = Column(Numeric(5, 2), nullable=False)
    totalCorrect = Column(Integer, nullable=False)
    totalQuestions = Column(Integer, nullable=False)
    answers = Column(JSONB, nullable=False)
    submittedAt = Column(DateTime, server_default=func.now())

    quiz = orm_relationship("Quiz", back_populates="submissions")
    student = orm_relationship("User")

    __table_args__ = (
        UniqueConstraint('quizId', 'studentId', name='uq_quiz_submissions_quiz_student'),
        Index('ix_quiz_submissions_quizId_studentId', 'quizId', 'studentId'),
        {'extend_existing': True}
    )


class CourseContent(Base):
    __tablename__ = 'course_contents'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    contentType = Column(pgEnum('video', 'document', 'text', 'quiz', 'assignment', name='course_contents_contenttype_enum', create_type=False), default=ContentType.VIDEO)
    order = Column(Integer, nullable=False)
    isPreview = Column(Boolean, default=False)
    isRequired = Column(Boolean, default=False)
    estimatedMinutes = Column(Integer, nullable=True)
    videoId = Column(UUID(as_uuid=True), ForeignKey('videos.id', ondelete='SET NULL'), nullable=True)
    documentId = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete='SET NULL'), nullable=True)
    quizId = Column(UUID(as_uuid=True), ForeignKey('quizzes.id', ondelete='SET NULL'), nullable=True)
    textContent = Column(Text, nullable=True)
    sectionId = Column(UUID(as_uuid=True), ForeignKey('course_sections.id', ondelete='CASCADE'), nullable=False, index=True)
    courseId = Column(UUID(as_uuid=True), ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    section = orm_relationship("CourseSection", back_populates="contents")
    video = orm_relationship("Video")
    document = orm_relationship("Document")
    quiz = orm_relationship("Quiz")
    course = orm_relationship("Course")

    __table_args__ = (
        Index('ix_course_contents_sectionId_order', 'sectionId', 'order'),
        Index('ix_course_contents_quizId', 'quizId'),
        {'extend_existing': True}
    )


class CourseEnrollment(Base):
    __tablename__ = 'course_enrollments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    courseId = Column(UUID(as_uuid=True), ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    studentId = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    status = Column(pgEnum('active', 'completed', 'dropped', 'expired', name='course_enrollments_status_enum', create_type=False), default=EnrollmentStatus.ACTIVE)
    progress = Column(Numeric(5, 2), default=0.0)
    lastAccessedAt = Column(DateTime, nullable=True)
    completedAt = Column(DateTime, nullable=True)
    certificateId = Column(String, nullable=True)
    enrolledAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    course = orm_relationship("Course")
    student = orm_relationship("User")

    __table_args__ = (
        UniqueConstraint('courseId', 'studentId', name='uq_course_enrollment_course_student'),
        Index('ix_course_enrollments_courseId_status', 'courseId', 'status'),
        Index('ix_course_enrollments_studentId_status', 'studentId', 'status'),
        {'extend_existing': True}
    )


class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    userId = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    type = Column(pgEnum('course_published', 'course_updated', 'content_added', 'enrollment_success', 'new_enrollment', 'video_uploaded', 'video_processed', 'document_uploaded', 'system_announcement', 'reminder', name='notifications_type_enum', create_type=False), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    isRead = Column(Boolean, default=False)
    readAt = Column(DateTime, nullable=True)
    referenceType = Column(pgEnum('course', 'video', 'document', 'user', 'enrollment', name='notifications_referencetype_enum', create_type=False), nullable=True)
    referenceId = Column(String, nullable=True)
    metadata_json = Column("metadata", JSONB, nullable=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = orm_relationship("User")

    __table_args__ = (
        Index('ix_notifications_userId_isRead', 'userId', 'isRead'),
        Index('ix_notifications_userId_createdAt', 'userId', 'createdAt'),
        {'extend_existing': True}
    )


class NotificationPreference(Base):
    __tablename__ = 'notification_preferences'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    userId = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    emailNotifications = Column(Boolean, default=True)
    pushNotifications = Column(Boolean, default=True)
    inAppNotifications = Column(Boolean, default=True)
    courseUpdates = Column(Boolean, default=True)
    enrollmentAlerts = Column(Boolean, default=True)
    newContentAlerts = Column(Boolean, default=True)
    systemAnnouncements = Column(Boolean, default=True)
    reminderNotifications = Column(Boolean, default=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = orm_relationship("User")
