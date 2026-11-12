import json

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from uuid import UUID

from app.auth.dependencies import get_current_user
from app.courses.service import CourseService
from app.database import get_db
from app.models.enums import CourseStatus
from app.models.enums import EnrollmentStatus
from app.models.models import Course, CourseEnrollment
from sqlalchemy import select, and_
from app.payments import service as payments

router = APIRouter(prefix="/payments", tags=["Payments"])
course_service = CourseService()


class VerifyPaymentSchema(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class CancelOrderSchema(BaseModel):
    razorpay_order_id: str


async def _enroll_verified(db: AsyncSession, course_id: str, student_id: str):
    return await course_service.enroll_in_course(db, course_id, student_id, payment_verified=True)


async def _revoke_enrollment(db: AsyncSession, course_id: str, student_id: str):
    """Fully refunded purchase: take the access back (idempotent)."""
    enrollment = (await db.execute(select(CourseEnrollment).where(and_(
        CourseEnrollment.courseId == UUID(course_id), CourseEnrollment.studentId == UUID(student_id),
        CourseEnrollment.status.in_([EnrollmentStatus.ACTIVE.value, EnrollmentStatus.COMPLETED.value]))))
    ).scalar_one_or_none()
    if not enrollment:
        return
    enrollment.status = EnrollmentStatus.DROPPED.value
    course = await db.get(Course, UUID(course_id))
    if course and (course.enrollmentCount or 0) > 0:
        course.enrollmentCount -= 1
    await db.commit()


@router.post("/courses/{courseId}/order", status_code=status.HTTP_201_CREATED)
async def create_order(courseId: str, db: AsyncSession = Depends(get_db),
                       current_user: dict = Depends(get_current_user)):
    try:
        course_uuid = UUID(courseId)
    except ValueError:
        raise HTTPException(status_code=404, detail="Course not found")
    course = await db.get(Course, course_uuid)
    if not course or course.status != CourseStatus.PUBLISHED:
        raise HTTPException(status_code=404, detail="Course not found or not available for purchase")
    already = await course_service.is_enrolled(db, courseId, current_user["userId"])
    return await payments.create_course_order(db, course, current_user["userId"], already)


@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_payment(body: VerifyPaymentSchema, db: AsyncSession = Depends(get_db),
                         current_user: dict = Depends(get_current_user)):
    return await payments.verify_checkout(
        db, current_user["userId"], body.razorpay_order_id, body.razorpay_payment_id,
        body.razorpay_signature, _enroll_verified,
    )


@router.post("/cancel", status_code=status.HTTP_200_OK)
async def cancel_order(body: CancelOrderSchema, db: AsyncSession = Depends(get_db),
                       current_user: dict = Depends(get_current_user)):
    return await payments.cancel_order(db, current_user["userId"], body.razorpay_order_id)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def razorpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    raw = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")
    try:
        payload = json.loads(raw or b"{}")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    return await payments.handle_webhook(db, raw, signature, payload, _enroll_verified, _revoke_enrollment)
