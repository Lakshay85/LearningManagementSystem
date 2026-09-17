import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.models import (
    User, Student, Teacher, Admin, Course, CourseEnrollment,
    Document, Video, Quiz, QuizQuestion, QuizSubmission,
    LLMUsageLog, AuditLog, SystemSetting
)
from app.models.enums import (
    UserRole, UserStatus, CourseStatus, QuizStatus,
    AuditAction, Permission
)
from app.auth.service import AuthService
from app.admin.schemas import CreateUserSchema

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_SETTINGS = {
    "platformName": {"value": "Antigravity LMS", "description": "Platform brand name"},
    "allowRegistrations": {"value": True, "description": "Allow public self-registration"},
    "enableQuizAI": {"value": True, "description": "Enable AI-powered quiz question generation"},
    "enableStudentRAG": {"value": True, "description": "Enable student AI chat with course materials"},
    "defaultDailyLLMLimit": {"value": 50, "description": "Default daily LLM calls quota for new users (0=unlimited)"},
    "defaultMonthlyLLMLimit": {"value": 500, "description": "Default monthly LLM calls quota for new users (0=unlimited)"}
}

class AdminService:
    # -------------------------------------------------------------
    # 1. Audit Logging Helper
    # -------------------------------------------------------------
    async def log_action(
        self,
        db: AsyncSession,
        actor_id: Optional[str],
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        actor_uuid = None
        if actor_id:
            try:
                actor_uuid = UUID(str(actor_id))
            except (ValueError, TypeError):
                pass

        log = AuditLog(
            actorId=actor_uuid,
            action=action,
            targetType=target_type,
            targetId=str(target_id) if target_id else None,
            details=details,
            ipAddress=ip_address
        )
        db.add(log)
        try:
            await db.commit()
            await db.refresh(log)
        except Exception as e:
            await db.rollback()
            logger.warning(f"Failed to persist audit log: {str(e)}")
        return log

    # -------------------------------------------------------------
    # 2. Platform Analytics & Dashboard Stats
    # -------------------------------------------------------------
    async def get_dashboard_stats(self, db: AsyncSession) -> dict:
        # Users counts
        total_users = await db.scalar(select(func.count(User.id))) or 0
        total_students = await db.scalar(select(func.count(User.id)).where(User.role == 'student')) or 0
        total_faculty = await db.scalar(select(func.count(User.id)).where(User.role == 'faculty')) or 0
        total_admins = await db.scalar(select(func.count(User.id)).where(User.role == 'admin')) or 0
        active_users = await db.scalar(select(func.count(User.id)).where(User.isActive == True)) or 0

        # Courses counts
        total_courses = await db.scalar(select(func.count(Course.id))) or 0
        published_courses = await db.scalar(select(func.count(Course.id)).where(Course.status == CourseStatus.PUBLISHED.value)) or 0
        draft_courses = await db.scalar(select(func.count(Course.id)).where(Course.status == CourseStatus.DRAFT.value)) or 0

        # Content counts
        total_documents = await db.scalar(select(func.count(Document.id))) or 0
        total_videos = await db.scalar(select(func.count(Video.id))) or 0
        total_quizzes = await db.scalar(select(func.count(Quiz.id))) or 0
        total_enrollments = await db.scalar(select(func.count(CourseEnrollment.id))) or 0

        # LLM stats
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        llm_calls_today = await db.scalar(
            select(func.count(LLMUsageLog.id)).where(LLMUsageLog.createdAt >= today_start)
        ) or 0

        llm_calls_month = await db.scalar(
            select(func.count(LLMUsageLog.id)).where(LLMUsageLog.createdAt >= month_start)
        ) or 0

        total_tokens = await db.scalar(
            select(func.sum(LLMUsageLog.totalTokens))
        ) or 0

        # Storage approximate (sum file sizes)
        doc_storage = await db.scalar(select(func.sum(Document.fileSize))) or 0
        video_storage = await db.scalar(select(func.sum(Video.fileSize))) or 0
        total_storage_bytes = int(doc_storage) + int(video_storage)

        # Recent activities
        recent_logs_res = await db.execute(
            select(AuditLog, User.email, User.firstName, User.lastName)
            .outerjoin(User, AuditLog.actorId == User.id)
            .order_by(desc(AuditLog.createdAt))
            .limit(6)
        )
        recent_activities = []
        for log, email, fn, ln in recent_logs_res.all():
            actor_name = f"{fn or ''} {ln or ''}".strip() or email or "System"
            recent_activities.append({
                "id": str(log.id),
                "action": log.action,
                "actorName": actor_name,
                "targetType": log.targetType,
                "targetId": log.targetId,
                "details": log.details,
                "createdAt": log.createdAt.isoformat() if log.createdAt else None
            })

        return {
            "users": {
                "total": total_users,
                "students": total_students,
                "faculty": total_faculty,
                "admins": total_admins,
                "active": active_users,
                "inactive": total_users - active_users
            },
            "courses": {
                "total": total_courses,
                "published": published_courses,
                "drafts": draft_courses,
                "enrollments": total_enrollments
            },
            "content": {
                "documents": total_documents,
                "videos": total_videos,
                "quizzes": total_quizzes,
                "storageBytes": total_storage_bytes
            },
            "llm": {
                "callsToday": llm_calls_today,
                "callsMonth": llm_calls_month,
                "totalTokens": int(total_tokens)
            },
            "recentActivities": recent_activities
        }

    # -------------------------------------------------------------
    # 3. User Management
    # -------------------------------------------------------------
    async def list_users(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        role: Optional[str] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> dict:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        query = select(User)
        conditions = []

        if search:
            s = f"%{search.strip()}%"
            conditions.append(or_(
                User.firstName.ilike(s),
                User.lastName.ilike(s),
                User.email.ilike(s)
            ))
        if role:
            conditions.append(User.role == role)
        if status_filter:
            if status_filter == "active":
                conditions.append(User.isActive == True)
            elif status_filter == "inactive":
                conditions.append(User.isActive == False)

        if conditions:
            query = query.where(and_(*conditions))

        total = await db.scalar(select(func.count()).select_from(query.subquery())) or 0

        query = query.order_by(desc(User.createdAt)).offset((page - 1) * limit).limit(limit)
        users = (await db.execute(query)).scalars().all()

        user_ids = [u.id for u in users]
        # Query today's LLM calls per user
        today_calls_map = {}
        if user_ids:
            calls_res = await db.execute(
                select(LLMUsageLog.userId, func.count(LLMUsageLog.id))
                .where(and_(LLMUsageLog.userId.in_(user_ids), LLMUsageLog.createdAt >= today_start))
                .group_by(LLMUsageLog.userId)
            )
            for uid, c in calls_res.all():
                today_calls_map[uid] = c

        items = []
        for u in users:
            items.append({
                "id": str(u.id),
                "email": u.email,
                "firstName": u.firstName,
                "lastName": u.lastName,
                "role": u.role,
                "isActive": u.isActive,
                "status": u.status.value if hasattr(u.status, 'value') else u.status,
                "llmDailyLimit": u.llmDailyLimit,
                "llmMonthlyLimit": u.llmMonthlyLimit,
                "todayLLMCalls": today_calls_map.get(u.id, 0),
                "lastLogin": u.lastLogin.isoformat() if u.lastLogin else None,
                "createdAt": u.createdAt.isoformat() if u.createdAt else None
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": -(-total // limit) if limit > 0 else 1
        }

    async def get_user_detail(self, db: AsyncSession, user_id: str) -> dict:
        try:
            uid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

        user = await db.get(User, uid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Fetch role-specific details
        role_details = {}
        if user.role == "student":
            student = (await db.execute(select(Student).where(Student.userId == uid))).scalar_one_or_none()
            enrollment_count = await db.scalar(select(func.count(CourseEnrollment.id)).where(CourseEnrollment.studentId == uid)) or 0
            quiz_subs = await db.scalar(select(func.count(QuizSubmission.id)).where(QuizSubmission.studentId == uid)) or 0
            role_details = {
                "enrollmentNumber": student.enrollmentNumber if student else None,
                "grade": student.grade if student else None,
                "enrollmentCount": enrollment_count,
                "quizSubmissionsCount": quiz_subs
            }
        elif user.role in ["faculty", "teacher"]:
            teacher = (await db.execute(select(Teacher).where(Teacher.userId == uid))).scalar_one_or_none()
            course_count = await db.scalar(select(func.count(Course.id)).where(Course.instructorId == uid)) or 0
            docs_count = await db.scalar(select(func.count(Document.id)).where(Document.uploaderId == uid)) or 0
            videos_count = await db.scalar(select(func.count(Video.id)).where(Video.uploaderId == uid)) or 0
            role_details = {
                "department": teacher.department if teacher else None,
                "specialization": teacher.specialization if teacher else None,
                "courseCount": course_count,
                "documentsCount": docs_count,
                "videosCount": videos_count
            }
        elif user.role == "admin":
            admin = (await db.execute(select(Admin).where(Admin.userId == uid))).scalar_one_or_none()
            role_details = {
                "adminLevel": admin.adminLevel if admin else "standard",
                "permissions": admin.permissions if admin and admin.permissions else [],
                "department": admin.department if admin else None
            }

        # LLM stats
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        calls_today = await db.scalar(
            select(func.count(LLMUsageLog.id)).where(and_(LLMUsageLog.userId == uid, LLMUsageLog.createdAt >= today_start))
        ) or 0
        calls_month = await db.scalar(
            select(func.count(LLMUsageLog.id)).where(and_(LLMUsageLog.userId == uid, LLMUsageLog.createdAt >= month_start))
        ) or 0
        total_tokens = await db.scalar(
            select(func.sum(LLMUsageLog.totalTokens)).where(LLMUsageLog.userId == uid)
        ) or 0

        # Recent 15 LLM logs
        logs_res = await db.execute(
            select(LLMUsageLog).where(LLMUsageLog.userId == uid).order_by(desc(LLMUsageLog.createdAt)).limit(15)
        )
        recent_llm_logs = [{
            "id": str(l.id),
            "feature": l.feature,
            "model": l.model,
            "promptTokens": l.promptTokens,
            "completionTokens": l.completionTokens,
            "totalTokens": l.totalTokens,
            "createdAt": l.createdAt.isoformat() if l.createdAt else None
        } for l in logs_res.scalars().all()]

        return {
            "id": str(user.id),
            "email": user.email,
            "firstName": user.firstName,
            "lastName": user.lastName,
            "role": user.role,
            "phoneNumber": user.phoneNumber,
            "isActive": user.isActive,
            "status": user.status.value if hasattr(user.status, 'value') else user.status,
            "llmDailyLimit": user.llmDailyLimit,
            "llmMonthlyLimit": user.llmMonthlyLimit,
            "createdAt": user.createdAt.isoformat() if user.createdAt else None,
            "lastLogin": user.lastLogin.isoformat() if user.lastLogin else None,
            "roleDetails": role_details,
            "llmStats": {
                "callsToday": calls_today,
                "callsMonth": calls_month,
                "totalTokens": int(total_tokens),
                "dailyLimit": user.llmDailyLimit,
                "monthlyLimit": user.llmMonthlyLimit
            },
            "recentLLMLogs": recent_llm_logs
        }

    async def create_user(
        self,
        db: AsyncSession,
        dto: CreateUserSchema,
        actor_id: str,
        ip_address: Optional[str] = None
    ) -> dict:
        existing = await db.execute(select(User).where(User.email == dto.email.lower()))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User with this email already exists")

        hashed_password = AuthService.hash_password(dto.password)
        user = User(
            email=dto.email.lower(),
            password=hashed_password,
            firstName=dto.firstName,
            lastName=dto.lastName,
            role=dto.role,
            phoneNumber=dto.phoneNumber,
            isActive=True,
            status=UserStatus.ACTIVE
        )
        db.add(user)
        await db.flush()

        if dto.role == "student":
            student = Student(userId=user.id)
            db.add(student)
        elif dto.role in ["faculty", "teacher"]:
            teacher = Teacher(userId=user.id, department=dto.department)
            db.add(teacher)
        elif dto.role == "admin":
            admin = Admin(
                userId=user.id,
                adminLevel="standard",
                permissions=[p.value for p in Permission],
                department=dto.department
            )
            db.add(admin)

        await db.commit()
        await db.refresh(user)

        await self.log_action(
            db=db,
            actor_id=actor_id,
            action=AuditAction.USER_CREATED.value,
            target_type="user",
            target_id=str(user.id),
            details={"email": user.email, "role": user.role},
            ip_address=ip_address
        )

        return {"id": str(user.id), "email": user.email, "role": user.role, "message": "User created successfully"}

    async def update_user_status(
        self,
        db: AsyncSession,
        user_id: str,
        is_active: bool,
        actor_id: str,
        ip_address: Optional[str] = None
    ) -> dict:
        try:
            uid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID")

        user = await db.get(User, uid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        old_status = user.isActive
        user.isActive = is_active
        user.status = UserStatus.ACTIVE if is_active else UserStatus.INACTIVE
        await db.commit()

        action = AuditAction.USER_ACTIVATED.value if is_active else AuditAction.USER_DEACTIVATED.value
        await self.log_action(
            db=db,
            actor_id=actor_id,
            action=action,
            target_type="user",
            target_id=str(user.id),
            details={"before": old_status, "after": is_active},
            ip_address=ip_address
        )
        return {"id": str(user.id), "isActive": user.isActive, "message": f"User {'activated' if is_active else 'deactivated'} successfully"}

    async def update_user_role(
        self,
        db: AsyncSession,
        user_id: str,
        new_role: str,
        actor_id: str,
        ip_address: Optional[str] = None
    ) -> dict:
        try:
            uid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID")

        user = await db.get(User, uid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        old_role = user.role
        user.role = new_role

        if new_role == "faculty":
            teacher = (await db.execute(select(Teacher).where(Teacher.userId == uid))).scalar_one_or_none()
            if not teacher:
                db.add(Teacher(userId=uid))
        elif new_role == "student":
            student = (await db.execute(select(Student).where(Student.userId == uid))).scalar_one_or_none()
            if not student:
                db.add(Student(userId=uid))
        elif new_role == "admin":
            admin = (await db.execute(select(Admin).where(Admin.userId == uid))).scalar_one_or_none()
            if not admin:
                db.add(Admin(userId=uid, adminLevel="standard", permissions=[p.value for p in Permission]))

        await db.commit()

        await self.log_action(
            db=db,
            actor_id=actor_id,
            action=AuditAction.USER_ROLE_CHANGED.value,
            target_type="user",
            target_id=str(user.id),
            details={"before": old_role, "after": new_role},
            ip_address=ip_address
        )
        return {"id": str(user.id), "role": user.role, "message": "User role updated successfully"}

    async def set_user_llm_limits(
        self,
        db: AsyncSession,
        user_id: str,
        daily_limit: Optional[int],
        monthly_limit: Optional[int],
        actor_id: str,
        ip_address: Optional[str] = None
    ) -> dict:
        try:
            uid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID")

        user = await db.get(User, uid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        old_limits = {"daily": user.llmDailyLimit, "monthly": user.llmMonthlyLimit}
        user.llmDailyLimit = daily_limit
        user.llmMonthlyLimit = monthly_limit
        await db.commit()

        await self.log_action(
            db=db,
            actor_id=actor_id,
            action=AuditAction.LLM_LIMIT_CHANGED.value,
            target_type="user",
            target_id=str(user.id),
            details={"before": old_limits, "after": {"daily": daily_limit, "monthly": monthly_limit}},
            ip_address=ip_address
        )
        return {
            "id": str(user.id),
            "llmDailyLimit": user.llmDailyLimit,
            "llmMonthlyLimit": user.llmMonthlyLimit,
            "message": "LLM quotas updated successfully"
        }

    async def reset_user_password(
        self,
        db: AsyncSession,
        user_id: str,
        new_password: str,
        actor_id: str,
        ip_address: Optional[str] = None
    ) -> dict:
        try:
            uid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID")

        user = await db.get(User, uid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.password = AuthService.hash_password(new_password)
        await db.commit()

        await self.log_action(
            db=db,
            actor_id=actor_id,
            action=AuditAction.USER_UPDATED.value,
            target_type="user",
            target_id=str(user.id),
            details={"field": "password_reset"},
            ip_address=ip_address
        )
        return {"message": "Password reset successfully"}

    async def delete_user(
        self,
        db: AsyncSession,
        user_id: str,
        actor_id: str,
        ip_address: Optional[str] = None
    ) -> dict:
        try:
            uid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID")

        if str(uid) == str(actor_id):
            raise HTTPException(status_code=400, detail="You cannot delete your own account")

        user = await db.get(User, uid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        email = user.email
        await db.delete(user)
        await db.commit()

        await self.log_action(
            db=db,
            actor_id=actor_id,
            action=AuditAction.USER_DELETED.value,
            target_type="user",
            target_id=str(uid),
            details={"email": email},
            ip_address=ip_address
        )
        return {"message": "User deleted successfully"}

    async def update_admin_permissions(
        self,
        db: AsyncSession,
        user_id: str,
        permissions: List[str],
        actor_id: str,
        ip_address: Optional[str] = None
    ) -> dict:
        try:
            uid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID")

        admin = (await db.execute(select(Admin).where(Admin.userId == uid))).scalar_one_or_none()
        if not admin:
            admin = Admin(userId=uid, adminLevel="standard", permissions=permissions)
            db.add(admin)
        else:
            admin.permissions = permissions

        await db.commit()

        await self.log_action(
            db=db,
            actor_id=actor_id,
            action=AuditAction.USER_UPDATED.value,
            target_type="admin",
            target_id=str(uid),
            details={"permissions": permissions},
            ip_address=ip_address
        )
        return {"userId": user_id, "permissions": permissions, "message": "Admin permissions updated successfully"}

    # -------------------------------------------------------------
    # 4. Course Oversight
    # -------------------------------------------------------------
    async def list_all_courses(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> dict:
        query = select(Course, User.firstName, User.lastName, User.email).join(User, Course.instructorId == User.id)
        conditions = []

        if search:
            s = f"%{search.strip()}%"
            conditions.append(or_(
                Course.title.ilike(s),
                User.firstName.ilike(s),
                User.lastName.ilike(s),
                User.email.ilike(s)
            ))
        if status_filter:
            conditions.append(Course.status == status_filter)

        if conditions:
            query = query.where(and_(*conditions))

        total = await db.scalar(select(func.count()).select_from(query.subquery())) or 0
        query = query.order_by(desc(Course.createdAt)).offset((page - 1) * limit).limit(limit)

        courses_res = (await db.execute(query)).all()
        items = []
        for c, fn, ln, email in courses_res:
            instructor_name = f"{fn or ''} {ln or ''}".strip() or email or "Unknown"
            items.append({
                "id": str(c.id),
                "title": c.title,
                "category": c.category.value if hasattr(c.category, 'value') else c.category,
                "status": c.status.value if hasattr(c.status, 'value') else c.status,
                "enrollmentCount": c.enrollmentCount or 0,
                "instructorId": str(c.instructorId),
                "instructorName": instructor_name,
                "instructorEmail": email,
                "thumbnailUrl": c.thumbnailUrl,
                "createdAt": c.createdAt.isoformat() if c.createdAt else None,
                "publishedAt": c.publishedAt.isoformat() if c.publishedAt else None
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": -(-total // limit) if limit > 0 else 1
        }

    async def unpublish_course(
        self,
        db: AsyncSession,
        course_id: str,
        actor_id: str,
        ip_address: Optional[str] = None
    ) -> dict:
        try:
            cid = UUID(course_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid course ID")

        course = await db.get(Course, cid)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        course.status = CourseStatus.DRAFT.value
        await db.commit()

        await self.log_action(
            db=db,
            actor_id=actor_id,
            action=AuditAction.COURSE_UNPUBLISHED.value,
            target_type="course",
            target_id=str(cid),
            details={"title": course.title},
            ip_address=ip_address
        )
        return {"id": str(cid), "status": course.status, "message": "Course unpublished (set to draft)"}

    # -------------------------------------------------------------
    # 5. Content Oversight (Documents & Videos)
    # -------------------------------------------------------------
    async def list_all_documents(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> dict:
        query = select(Document, User.firstName, User.lastName, User.email).join(User, Document.uploaderId == User.id)
        if search:
            s = f"%{search.strip()}%"
            query = query.where(or_(
                Document.title.ilike(s),
                Document.originalFilename.ilike(s),
                User.firstName.ilike(s),
                User.lastName.ilike(s),
                User.email.ilike(s)
            ))

        total = await db.scalar(select(func.count()).select_from(query.subquery())) or 0
        query = query.order_by(desc(Document.createdAt)).offset((page - 1) * limit).limit(limit)

        docs_res = (await db.execute(query)).all()
        items = []
        for d, fn, ln, email in docs_res:
            uploader_name = f"{fn or ''} {ln or ''}".strip() or email or "Unknown"
            items.append({
                "id": str(d.id),
                "title": d.title,
                "originalFilename": d.originalFilename,
                "documentType": d.documentType.value if hasattr(d.documentType, 'value') else d.documentType,
                "mimeType": d.mimeType,
                "fileSize": int(d.fileSize) if d.fileSize else 0,
                "cdnUrl": d.cdnUrl,
                "uploaderName": uploader_name,
                "uploaderEmail": email,
                "createdAt": d.createdAt.isoformat() if d.createdAt else None
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": -(-total // limit) if limit > 0 else 1
        }

    async def remove_document(
        self,
        db: AsyncSession,
        document_id: str,
        actor_id: str,
        ip_address: Optional[str] = None
    ) -> dict:
        try:
            did = UUID(document_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid document ID")

        doc = await db.get(Document, did)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        title = doc.title
        await db.delete(doc)
        await db.commit()

        await self.log_action(
            db=db,
            actor_id=actor_id,
            action=AuditAction.CONTENT_REMOVED.value,
            target_type="document",
            target_id=str(did),
            details={"title": title},
            ip_address=ip_address
        )
        return {"message": "Document removed successfully"}

    async def list_all_videos(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> dict:
        query = select(Video, User.firstName, User.lastName, User.email).join(User, Video.uploaderId == User.id)
        if search:
            s = f"%{search.strip()}%"
            query = query.where(or_(
                Video.title.ilike(s),
                Video.originalFilename.ilike(s),
                User.firstName.ilike(s),
                User.lastName.ilike(s),
                User.email.ilike(s)
            ))

        total = await db.scalar(select(func.count()).select_from(query.subquery())) or 0
        query = query.order_by(desc(Video.createdAt)).offset((page - 1) * limit).limit(limit)

        vids_res = (await db.execute(query)).all()
        items = []
        for v, fn, ln, email in vids_res:
            uploader_name = f"{fn or ''} {ln or ''}".strip() or email or "Unknown"
            items.append({
                "id": str(v.id),
                "title": v.title,
                "originalFilename": v.originalFilename,
                "category": v.category.value if hasattr(v.category, 'value') else v.category,
                "status": v.status.value if hasattr(v.status, 'value') else v.status,
                "fileSize": int(v.fileSize) if v.fileSize else 0,
                "cdnUrl": v.cdnUrl,
                "thumbnailPath": v.thumbnailPath,
                "uploaderName": uploader_name,
                "uploaderEmail": email,
                "createdAt": v.createdAt.isoformat() if v.createdAt else None
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": -(-total // limit) if limit > 0 else 1
        }

    async def remove_video(
        self,
        db: AsyncSession,
        video_id: str,
        actor_id: str,
        ip_address: Optional[str] = None
    ) -> dict:
        try:
            vid = UUID(video_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid video ID")

        video = await db.get(Video, vid)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        title = video.title
        await db.delete(video)
        await db.commit()

        await self.log_action(
            db=db,
            actor_id=actor_id,
            action=AuditAction.CONTENT_REMOVED.value,
            target_type="video",
            target_id=str(vid),
            details={"title": title},
            ip_address=ip_address
        )
        return {"message": "Video removed successfully"}

    # -------------------------------------------------------------
    # 6. Quiz Oversight
    # -------------------------------------------------------------
    async def list_all_quizzes(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> dict:
        query = (
            select(Quiz, Course.title.label("courseTitle"), User.firstName, User.lastName, User.email)
            .join(Course, Quiz.courseId == Course.id)
            .join(User, Quiz.createdBy == User.id)
        )
        conditions = []
        if search:
            s = f"%{search.strip()}%"
            conditions.append(or_(
                Quiz.title.ilike(s),
                Course.title.ilike(s),
                User.firstName.ilike(s),
                User.lastName.ilike(s)
            ))
        if status_filter:
            conditions.append(Quiz.status == status_filter)

        if conditions:
            query = query.where(and_(*conditions))

        total = await db.scalar(select(func.count()).select_from(query.subquery())) or 0
        query = query.order_by(desc(Quiz.createdAt)).offset((page - 1) * limit).limit(limit)

        quizzes_res = (await db.execute(query)).all()
        items = []
        for q, c_title, fn, ln, email in quizzes_res:
            creator_name = f"{fn or ''} {ln or ''}".strip() or email or "Unknown"
            subs_count = await db.scalar(select(func.count(QuizSubmission.id)).where(QuizSubmission.quizId == q.id)) or 0
            items.append({
                "id": str(q.id),
                "title": q.title,
                "courseId": str(q.courseId),
                "courseTitle": c_title,
                "status": q.status,
                "totalQuestions": q.totalQuestions or 0,
                "submissionsCount": subs_count,
                "creatorName": creator_name,
                "creatorEmail": email,
                "createdAt": q.createdAt.isoformat() if q.createdAt else None
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": -(-total // limit) if limit > 0 else 1
        }

    async def archive_quiz(
        self,
        db: AsyncSession,
        quiz_id: str,
        actor_id: str,
        ip_address: Optional[str] = None
    ) -> dict:
        try:
            qid = UUID(quiz_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid quiz ID")

        quiz = await db.get(Quiz, qid)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        quiz.status = QuizStatus.ARCHIVED.value
        await db.commit()

        await self.log_action(
            db=db,
            actor_id=actor_id,
            action=AuditAction.QUIZ_REMOVED.value,
            target_type="quiz",
            target_id=str(qid),
            details={"title": quiz.title},
            ip_address=ip_address
        )
        return {"id": str(qid), "status": quiz.status, "message": "Quiz archived successfully"}

    # -------------------------------------------------------------
    # 7. LLM Usage Analytics
    # -------------------------------------------------------------
    async def get_llm_usage_overview(self, db: AsyncSession) -> dict:
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        thirty_days_ago = today_start - timedelta(days=29)

        calls_today = await db.scalar(
            select(func.count(LLMUsageLog.id)).where(LLMUsageLog.createdAt >= today_start)
        ) or 0

        calls_month = await db.scalar(
            select(func.count(LLMUsageLog.id)).where(LLMUsageLog.createdAt >= month_start)
        ) or 0

        total_tokens = await db.scalar(select(func.sum(LLMUsageLog.totalTokens))) or 0
        prompt_tokens = await db.scalar(select(func.sum(LLMUsageLog.promptTokens))) or 0
        comp_tokens = await db.scalar(select(func.sum(LLMUsageLog.completionTokens))) or 0

        # Feature breakdown
        feature_res = await db.execute(
            select(LLMUsageLog.feature, func.count(LLMUsageLog.id), func.sum(LLMUsageLog.totalTokens))
            .group_by(LLMUsageLog.feature)
        )
        by_feature = [{
            "feature": f,
            "calls": c,
            "tokens": int(t or 0)
        } for f, c, t in feature_res.all()]

        # 30-day trend
        trend_res = await db.execute(
            select(func.date_trunc('day', LLMUsageLog.createdAt).label("day"), func.count(LLMUsageLog.id))
            .where(LLMUsageLog.createdAt >= thirty_days_ago)
            .group_by("day")
            .order_by("day")
        )
        trend_map = {d.strftime("%Y-%m-%d"): c for d, c in trend_res.all()}
        trend_30_days = []
        for i in range(30):
            day_str = (thirty_days_ago + timedelta(days=i)).strftime("%Y-%m-%d")
            trend_30_days.append({
                "date": day_str,
                "calls": trend_map.get(day_str, 0)
            })

        # Top 10 users by LLM usage
        top_users_res = await db.execute(
            select(User.id, User.email, User.firstName, User.lastName, User.role, func.count(LLMUsageLog.id).label("calls"), func.sum(LLMUsageLog.totalTokens).label("tokens"))
            .join(LLMUsageLog, User.id == LLMUsageLog.userId)
            .group_by(User.id)
            .order_by(desc("calls"))
            .limit(10)
        )
        top_users = [{
            "id": str(u_id),
            "email": email,
            "name": f"{fn or ''} {ln or ''}".strip() or email,
            "role": role,
            "calls": calls,
            "tokens": int(tokens or 0)
        } for u_id, email, fn, ln, role, calls, tokens in top_users_res.all()]

        return {
            "summary": {
                "callsToday": calls_today,
                "callsMonth": calls_month,
                "totalTokens": int(total_tokens),
                "promptTokens": int(prompt_tokens),
                "completionTokens": int(comp_tokens)
            },
            "byFeature": by_feature,
            "trend": trend_30_days,
            "topUsers": top_users
        }

    async def get_user_llm_usage(self, db: AsyncSession, user_id: str) -> dict:
        try:
            uid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID")

        user = await db.get(User, uid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        today_calls = await db.scalar(
            select(func.count(LLMUsageLog.id)).where(and_(LLMUsageLog.userId == uid, LLMUsageLog.createdAt >= today_start))
        ) or 0
        month_calls = await db.scalar(
            select(func.count(LLMUsageLog.id)).where(and_(LLMUsageLog.userId == uid, LLMUsageLog.createdAt >= month_start))
        ) or 0
        total_tokens = await db.scalar(
            select(func.sum(LLMUsageLog.totalTokens)).where(LLMUsageLog.userId == uid)
        ) or 0

        logs_res = await db.execute(
            select(LLMUsageLog).where(LLMUsageLog.userId == uid).order_by(desc(LLMUsageLog.createdAt)).limit(30)
        )
        recent_logs = [{
            "id": str(l.id),
            "feature": l.feature,
            "model": l.model,
            "promptTokens": l.promptTokens,
            "completionTokens": l.completionTokens,
            "totalTokens": l.totalTokens,
            "createdAt": l.createdAt.isoformat() if l.createdAt else None
        } for l in logs_res.scalars().all()]

        return {
            "user": {
                "id": str(user.id),
                "name": f"{user.firstName} {user.lastName}".strip(),
                "email": user.email,
                "dailyLimit": user.llmDailyLimit,
                "monthlyLimit": user.llmMonthlyLimit
            },
            "todayCalls": today_calls,
            "monthCalls": month_calls,
            "totalTokens": int(total_tokens),
            "logs": recent_logs
        }

    # -------------------------------------------------------------
    # 8. Audit Logs
    # -------------------------------------------------------------
    async def list_audit_logs(
        self,
        db: AsyncSession,
        action: Optional[str] = None,
        target_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> dict:
        query = select(AuditLog, User.firstName, User.lastName, User.email).outerjoin(User, AuditLog.actorId == User.id)
        conditions = []

        if action:
            conditions.append(AuditLog.action == action)
        if target_type:
            conditions.append(AuditLog.targetType == target_type)
        if actor_id:
            try:
                conditions.append(AuditLog.actorId == UUID(actor_id))
            except ValueError:
                pass

        if conditions:
            query = query.where(and_(*conditions))

        total = await db.scalar(select(func.count()).select_from(query.subquery())) or 0
        query = query.order_by(desc(AuditLog.createdAt)).offset((page - 1) * limit).limit(limit)

        logs_res = (await db.execute(query)).all()
        items = []
        for log, fn, ln, email in logs_res:
            actor_name = f"{fn or ''} {ln or ''}".strip() or email or "System / External"
            items.append({
                "id": str(log.id),
                "actorId": str(log.actorId) if log.actorId else None,
                "actorName": actor_name,
                "actorEmail": email,
                "action": log.action,
                "targetType": log.targetType,
                "targetId": log.targetId,
                "details": log.details,
                "ipAddress": log.ipAddress,
                "createdAt": log.createdAt.isoformat() if log.createdAt else None
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": -(-total // limit) if limit > 0 else 1
        }

    # -------------------------------------------------------------
    # 9. System Settings
    # -------------------------------------------------------------
    async def get_all_settings(self, db: AsyncSession) -> dict:
        settings_res = await db.execute(select(SystemSetting))
        existing = {s.key: {"value": s.value, "description": s.description} for s in settings_res.scalars().all()}
        
        # Merge default settings if not yet saved in DB
        result = {}
        for k, v in DEFAULT_SYSTEM_SETTINGS.items():
            if k in existing:
                result[k] = existing[k]
            else:
                result[k] = v
        for k, v in existing.items():
            if k not in result:
                result[k] = v

        return result

    async def update_setting(
        self,
        db: AsyncSession,
        key: str,
        value: Any,
        description: Optional[str],
        actor_id: str,
        ip_address: Optional[str] = None
    ) -> dict:
        setting = await db.get(SystemSetting, key)
        actor_uuid = None
        try:
            actor_uuid = UUID(str(actor_id))
        except (ValueError, TypeError):
            pass

        if not setting:
            setting = SystemSetting(
                key=key,
                value=value,
                description=description or DEFAULT_SYSTEM_SETTINGS.get(key, {}).get("description"),
                updatedBy=actor_uuid
            )
            db.add(setting)
        else:
            old_value = setting.value
            setting.value = value
            if description:
                setting.description = description
            setting.updatedBy = actor_uuid

        await db.commit()

        await self.log_action(
            db=db,
            actor_id=actor_id,
            action=AuditAction.SYSTEM_SETTING_CHANGED.value,
            target_type="system",
            target_id=key,
            details={"key": key, "value": value},
            ip_address=ip_address
        )
        return {"key": key, "value": value, "message": f"Setting '{key}' updated successfully"}

admin_service = AdminService()
