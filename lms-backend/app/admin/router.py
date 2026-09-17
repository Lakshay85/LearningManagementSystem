from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Request, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import require_admin, PermissionChecker, get_current_user
from app.models.enums import Permission
from app.admin.schemas import (
    CreateUserSchema,
    UpdateUserStatusSchema,
    UpdateUserRoleSchema,
    SetLLMLimitSchema,
    ResetPasswordSchema,
    UpdateSystemSettingSchema,
    AdminPermissionsSchema
)
from app.admin.service import admin_service

router = APIRouter(prefix="/admin", tags=["Admin"])

def get_client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


# -------------------------------------------------------------
# 1. Dashboard Stats
# -------------------------------------------------------------
@router.get("/dashboard/stats")
async def get_dashboard_stats(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    return await admin_service.get_dashboard_stats(db)


# -------------------------------------------------------------
# 2. User Management
# -------------------------------------------------------------
@router.get("/users")
async def list_users(
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(PermissionChecker(Permission.USERS_VIEW.value)),
    db: AsyncSession = Depends(get_db)
):
    return await admin_service.list_users(
        db=db,
        search=search,
        role=role,
        status_filter=status,
        page=page,
        limit=limit
    )

@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    dto: CreateUserSchema,
    request: Request,
    current_user: dict = Depends(PermissionChecker(Permission.USERS_MANAGE.value)),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    return await admin_service.create_user(
        db=db,
        dto=dto,
        actor_id=current_user["userId"],
        ip_address=ip
    )

@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: str,
    current_user: dict = Depends(PermissionChecker(Permission.USERS_VIEW.value)),
    db: AsyncSession = Depends(get_db)
):
    return await admin_service.get_user_detail(db, user_id)

@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    dto: UpdateUserStatusSchema,
    request: Request,
    current_user: dict = Depends(PermissionChecker(Permission.USERS_MANAGE.value)),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    return await admin_service.update_user_status(
        db=db,
        user_id=user_id,
        is_active=dto.isActive,
        actor_id=current_user["userId"],
        ip_address=ip
    )

@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    dto: UpdateUserRoleSchema,
    request: Request,
    current_user: dict = Depends(PermissionChecker(Permission.USERS_MANAGE.value)),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    return await admin_service.update_user_role(
        db=db,
        user_id=user_id,
        new_role=dto.role,
        actor_id=current_user["userId"],
        ip_address=ip
    )

@router.patch("/users/{user_id}/llm-limits")
async def set_user_llm_limits(
    user_id: str,
    dto: SetLLMLimitSchema,
    request: Request,
    current_user: dict = Depends(PermissionChecker(Permission.LLM_CONFIGURE.value)),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    return await admin_service.set_user_llm_limits(
        db=db,
        user_id=user_id,
        daily_limit=dto.llmDailyLimit,
        monthly_limit=dto.llmMonthlyLimit,
        actor_id=current_user["userId"],
        ip_address=ip
    )

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    dto: ResetPasswordSchema,
    request: Request,
    current_user: dict = Depends(PermissionChecker(Permission.USERS_MANAGE.value)),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    return await admin_service.reset_user_password(
        db=db,
        user_id=user_id,
        new_password=dto.newPassword,
        actor_id=current_user["userId"],
        ip_address=ip
    )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    current_user: dict = Depends(PermissionChecker(Permission.USERS_DELETE.value)),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    return await admin_service.delete_user(
        db=db,
        user_id=user_id,
        actor_id=current_user["userId"],
        ip_address=ip
    )

@router.patch("/users/{user_id}/permissions")
async def update_admin_permissions(
    user_id: str,
    dto: AdminPermissionsSchema,
    request: Request,
    current_user: dict = Depends(PermissionChecker(Permission.ADMIN_MANAGE.value)),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    return await admin_service.update_admin_permissions(
        db=db,
        user_id=user_id,
        permissions=dto.permissions,
        actor_id=current_user["userId"],
        ip_address=ip
    )


# -------------------------------------------------------------
# 3. Course Oversight
# -------------------------------------------------------------
@router.get("/courses")
async def list_all_courses(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(PermissionChecker(Permission.COURSES_VIEW_ALL.value)),
    db: AsyncSession = Depends(get_db)
):
    return await admin_service.list_all_courses(
        db=db,
        search=search,
        status_filter=status,
        page=page,
        limit=limit
    )

@router.post("/courses/{course_id}/unpublish")
async def unpublish_course(
    course_id: str,
    request: Request,
    current_user: dict = Depends(PermissionChecker(Permission.COURSES_MANAGE.value)),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    return await admin_service.unpublish_course(
        db=db,
        course_id=course_id,
        actor_id=current_user["userId"],
        ip_address=ip
    )


# -------------------------------------------------------------
# 4. Content Oversight
# -------------------------------------------------------------
@router.get("/content/documents")
async def list_all_documents(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(PermissionChecker(Permission.CONTENT_VIEW_ALL.value)),
    db: AsyncSession = Depends(get_db)
):
    return await admin_service.list_all_documents(
        db=db,
        search=search,
        page=page,
        limit=limit
    )

@router.delete("/content/documents/{document_id}")
async def remove_document(
    document_id: str,
    request: Request,
    current_user: dict = Depends(PermissionChecker(Permission.CONTENT_MANAGE.value)),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    return await admin_service.remove_document(
        db=db,
        document_id=document_id,
        actor_id=current_user["userId"],
        ip_address=ip
    )

@router.get("/content/videos")
async def list_all_videos(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(PermissionChecker(Permission.CONTENT_VIEW_ALL.value)),
    db: AsyncSession = Depends(get_db)
):
    return await admin_service.list_all_videos(
        db=db,
        search=search,
        page=page,
        limit=limit
    )

@router.delete("/content/videos/{video_id}")
async def remove_video(
    video_id: str,
    request: Request,
    current_user: dict = Depends(PermissionChecker(Permission.CONTENT_MANAGE.value)),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    return await admin_service.remove_video(
        db=db,
        video_id=video_id,
        actor_id=current_user["userId"],
        ip_address=ip
    )


# -------------------------------------------------------------
# 5. Quiz Oversight
# -------------------------------------------------------------
@router.get("/quizzes")
async def list_all_quizzes(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(PermissionChecker(Permission.QUIZZES_VIEW_ALL.value)),
    db: AsyncSession = Depends(get_db)
):
    return await admin_service.list_all_quizzes(
        db=db,
        search=search,
        status_filter=status,
        page=page,
        limit=limit
    )

@router.post("/quizzes/{quiz_id}/archive")
async def archive_quiz(
    quiz_id: str,
    request: Request,
    current_user: dict = Depends(PermissionChecker(Permission.QUIZZES_MANAGE.value)),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    return await admin_service.archive_quiz(
        db=db,
        quiz_id=quiz_id,
        actor_id=current_user["userId"],
        ip_address=ip
    )


# -------------------------------------------------------------
# 6. LLM Usage Analytics
# -------------------------------------------------------------
@router.get("/llm/usage")
async def get_llm_usage_overview(
    current_user: dict = Depends(PermissionChecker(Permission.LLM_VIEW_USAGE.value)),
    db: AsyncSession = Depends(get_db)
):
    return await admin_service.get_llm_usage_overview(db)

@router.get("/llm/usage/{user_id}")
async def get_user_llm_usage(
    user_id: str,
    current_user: dict = Depends(PermissionChecker(Permission.LLM_VIEW_USAGE.value)),
    db: AsyncSession = Depends(get_db)
):
    return await admin_service.get_user_llm_usage(db, user_id)


# -------------------------------------------------------------
# 7. Audit Logs
# -------------------------------------------------------------
@router.get("/audit-logs")
async def list_audit_logs(
    action: Optional[str] = Query(None),
    targetType: Optional[str] = Query(None),
    actorId: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(PermissionChecker(Permission.AUDIT_LOGS_VIEW.value)),
    db: AsyncSession = Depends(get_db)
):
    return await admin_service.list_audit_logs(
        db=db,
        action=action,
        target_type=targetType,
        actor_id=actorId,
        page=page,
        limit=limit
    )


# -------------------------------------------------------------
# 8. System Settings
# -------------------------------------------------------------
@router.get("/settings")
async def get_all_settings(
    current_user: dict = Depends(PermissionChecker(Permission.SYSTEM_SETTINGS.value)),
    db: AsyncSession = Depends(get_db)
):
    return await admin_service.get_all_settings(db)

@router.patch("/settings/{key}")
async def update_setting(
    key: str,
    dto: UpdateSystemSettingSchema,
    request: Request,
    current_user: dict = Depends(PermissionChecker(Permission.SYSTEM_SETTINGS.value)),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    return await admin_service.update_setting(
        db=db,
        key=key,
        value=dto.value,
        description=dto.description,
        actor_id=current_user["userId"],
        ip_address=ip
    )
