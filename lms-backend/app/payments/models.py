import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, func, Uuid
from app.database import Base


class PaymentStatus:
    CREATED = "created"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"  # fully refunded: access revoked, can buy again


class PaymentOrder(Base):
    """One Razorpay order for one student buying one course.

    The amount is always computed on the server from the course price at the
    time the order is created and is never taken from the client.
    """
    __tablename__ = "payment_orders"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    userId = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    courseId = Column(Uuid(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    amountPaise = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    status = Column(String(20), nullable=False, default=PaymentStatus.CREATED)
    razorpayOrderId = Column(String(64), unique=True, nullable=False)
    razorpayPaymentId = Column(String(64), unique=True, nullable=True)
    refundedPaise = Column(Integer, nullable=False, default=0)
    failureReason = Column(String(300), nullable=True)
    paidAt = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_payment_orders_user_course_status", "userId", "courseId", "status"),
        {"extend_existing": True},
    )
