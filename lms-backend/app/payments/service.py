import logging
import uuid
from datetime import datetime
from typing import Awaitable, Callable, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.payments import razorpay_client
from app.payments.models import PaymentOrder, PaymentStatus
from app.payments.pricing import amount_in_paise, is_paid_course, MIN_AMOUNT_PAISE

CURRENCY = "INR"
logger = logging.getLogger(__name__)


def ensure_configured() -> None:
    """Refuse to run unless test keys exist. Live keys are always refused (test-mode-only build)."""
    key_id = settings.RAZORPAY_KEY_ID
    if not key_id or not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=503, detail="Payments are not configured.")
    if not key_id.startswith("rzp_test_"):
        raise HTTPException(status_code=503, detail="Only Razorpay test keys (rzp_test_...) are allowed.")


async def create_course_order(db: AsyncSession, course, user_id: str, already_enrolled: bool) -> dict:
    ensure_configured()
    if already_enrolled:
        raise HTTPException(status_code=409, detail="You are already enrolled in this course")
    if not is_paid_course(course):
        raise HTTPException(status_code=400, detail="This course is free. Use the enroll endpoint.")
    if (course.currency or CURRENCY) != CURRENCY:
        raise HTTPException(status_code=400, detail="Only INR courses can be purchased.")
    amount = amount_in_paise(course)
    if amount < MIN_AMOUNT_PAISE:
        raise HTTPException(status_code=400, detail="Course price is below the minimum payable amount.")

    if await has_paid_order(db, user_id, str(course.id)):
        raise HTTPException(status_code=409, detail="You already paid for this course. Use enroll to get access.")

    existing = (await db.execute(
        select(PaymentOrder).where(and_(
            PaymentOrder.userId == UUID(str(user_id)),
            PaymentOrder.courseId == course.id,
            PaymentOrder.status == PaymentStatus.CREATED,
            PaymentOrder.amountPaise == amount,
        )).order_by(PaymentOrder.createdAt.desc()).limit(1)
    )).scalar_one_or_none()
    if existing:  # reuse the open order instead of creating a second chargeable one
        return {
            "orderId": existing.razorpayOrderId, "amount": amount, "currency": CURRENCY,
            "keyId": settings.RAZORPAY_KEY_ID, "courseId": str(course.id), "courseTitle": course.title,
        }

    order_id = uuid.uuid4()
    rp = await razorpay_client.create_order(
        settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET, amount, CURRENCY,
        receipt=str(order_id)[:40], notes={"courseId": str(course.id), "userId": str(user_id)},
    )
    order = PaymentOrder(
        id=order_id, userId=UUID(str(user_id)), courseId=course.id, amountPaise=amount,
        currency=CURRENCY, status=PaymentStatus.CREATED, razorpayOrderId=rp["id"],
    )
    db.add(order)
    await db.commit()
    return {
        "orderId": rp["id"], "amount": amount, "currency": CURRENCY,
        "keyId": settings.RAZORPAY_KEY_ID, "courseId": str(course.id), "courseTitle": course.title,
    }


async def _get_order(db: AsyncSession, razorpay_order_id: str, user_id: Optional[str] = None,
                     lock: bool = False) -> Optional[PaymentOrder]:
    conds = [PaymentOrder.razorpayOrderId == razorpay_order_id]
    if user_id is not None:
        conds.append(PaymentOrder.userId == UUID(str(user_id)))
    stmt = select(PaymentOrder).where(and_(*conds))
    if lock:
        stmt = stmt.with_for_update()
    return (await db.execute(stmt)).scalar_one_or_none()


EnrollFn = Callable[[AsyncSession, str, str], Awaitable[object]]


async def fulfill_order(db: AsyncSession, order: PaymentOrder, payment_id: str, enroll: EnrollFn) -> bool:
    """Record the payment durably, then enroll. Safe to call repeatedly. Returns True if newly marked paid.

    Order of operations matters:
      1. The paid record is committed on its own first, so a later enrollment failure can
         never lose the fact that the student paid (it is what allows reconciliation).
      2. Enrollment is attempted every time (also for an already-paid order), so a retry of the
         checkout callback or webhook repairs a half-finished fulfilment.
    Access is only ever granted through a paid record, which is only written after a verified
    signature (or webhook) for an order whose amount the server set.
    """
    order_id, course_id, user_id = order.id, str(order.courseId), str(order.userId)
    newly = order.status != PaymentStatus.PAID
    if newly:
        order.status = PaymentStatus.PAID
        order.razorpayPaymentId = payment_id
        order.paidAt = datetime.utcnow()
        order.failureReason = None
        db.add(order)
        await db.commit()
    try:
        await enroll(db, course_id, user_id)
    except HTTPException as e:
        await db.rollback()
        if e.status_code != 409:  # 409 = already enrolled, which is the desired end state
            logger.error("Paid order %s but enrollment failed: %s", order_id, e.detail)
            raise HTTPException(
                status_code=500,
                detail="Payment received, but enrollment could not be completed yet. Do not pay again; try enrolling again shortly or contact support.",
            )
    except IntegrityError:
        await db.rollback()  # a concurrent request enrolled the student first
    except Exception:
        await db.rollback()
        logger.exception("Paid order %s but enrollment crashed", order_id)
        raise HTTPException(
            status_code=500,
            detail="Payment received, but enrollment could not be completed yet. Do not pay again; try enrolling again shortly or contact support.",
        )
    return newly


def check_payment_matches_order(payment: dict, order: PaymentOrder, payment_id: str) -> Optional[str]:
    """None when the provider's payment is captured and bound to this order with the exact amount.
    'pending' for created/authorized (not settled, no access yet); 'invalid' for any mismatch."""
    if payment.get("id") != payment_id or payment.get("order_id") != order.razorpayOrderId:
        return "invalid"
    if payment.get("amount") != order.amountPaise or payment.get("currency") != order.currency:
        return "invalid"
    status = payment.get("status")
    if status == "captured":
        return None
    if status in ("created", "authorized"):
        return "pending"
    return "invalid"  # failed / refunded / anything else


async def verify_checkout(db: AsyncSession, user_id: str, razorpay_order_id: str, razorpay_payment_id: str,
                          signature: str, enroll: EnrollFn, fetch_payment_fn=None) -> dict:
    fetch_payment_fn = fetch_payment_fn or razorpay_client.fetch_payment
    ensure_configured()
    order = await _get_order(db, razorpay_order_id, user_id=user_id, lock=True)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if not razorpay_client.verify_checkout_signature(
            razorpay_order_id, razorpay_payment_id, signature, settings.RAZORPAY_KEY_SECRET):
        raise HTTPException(status_code=400, detail="Payment signature verification failed")
    if order.status == PaymentStatus.PAID and order.razorpayPaymentId != razorpay_payment_id:
        raise HTTPException(status_code=409, detail="Order already paid with a different payment")
    if order.status == PaymentStatus.REFUNDED:
        raise HTTPException(status_code=409, detail="This payment was refunded")
    if order.status != PaymentStatus.PAID:
        # Do not trust the client-side callback alone: ask the provider what actually happened.
        payment = await fetch_payment_fn(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET, razorpay_payment_id)
        problem = check_payment_matches_order(payment, order, razorpay_payment_id)
        if problem == "pending":
            raise HTTPException(
                status_code=409,
                detail="Your payment is not confirmed yet. You will be enrolled automatically once it is captured; do not pay again.",
            )
        if problem:
            raise HTTPException(status_code=400, detail="Payment could not be verified")
    course_id = str(order.courseId)  # read before fulfil: a rollback expires loaded attributes
    newly = await fulfill_order(db, order, razorpay_payment_id, enroll)
    return {"status": "paid", "courseId": course_id, "alreadyProcessed": not newly}


async def cancel_order(db: AsyncSession, user_id: str, razorpay_order_id: str) -> dict:
    order = await _get_order(db, razorpay_order_id, user_id=user_id, lock=True)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status == PaymentStatus.CREATED:
        order.status = PaymentStatus.CANCELLED
        await db.commit()
    return {"status": order.status}


RevokeFn = Callable[[AsyncSession, str, str], Awaitable[object]]


async def _handle_refund(db: AsyncSession, payload: dict, revoke: Optional[RevokeFn], fetch_payment_fn) -> dict:
    body = payload.get("payload") or {}
    pay = ((body.get("payment") or {}).get("entity")) or {}
    ref = ((body.get("refund") or {}).get("entity")) or {}
    payment_id = ref.get("payment_id") or pay.get("id")
    if not payment_id:
        return {"status": "ignored"}
    order = (await db.execute(
        select(PaymentOrder).where(PaymentOrder.razorpayPaymentId == payment_id).with_for_update()
    )).scalar_one_or_none()
    if not order or order.status not in (PaymentStatus.PAID, PaymentStatus.REFUNDED):
        return {"status": "ignored"}
    # absolute refunded total from the payment entity (idempotent under webhook replays);
    # fall back to asking the provider rather than summing events
    total = pay.get("amount_refunded")
    if total is None:
        total = (await fetch_payment_fn(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET, payment_id)).get("amount_refunded")
    if not isinstance(total, int) or total <= 0:
        return {"status": "ignored"}
    order_course, order_user = str(order.courseId), str(order.userId)
    order.refundedPaise = min(max(order.refundedPaise or 0, total), order.amountPaise)
    fully = order.refundedPaise >= order.amountPaise
    if fully:
        order.status = PaymentStatus.REFUNDED
    await db.commit()
    if fully and revoke:
        await revoke(db, order_course, order_user)
    return {"status": "refunded" if fully else "partial_refund_recorded"}


async def handle_webhook(db: AsyncSession, raw_body: bytes, signature: Optional[str],
                         payload: dict, enroll: EnrollFn, revoke: Optional[RevokeFn] = None,
                         fetch_payment_fn=None) -> dict:
    fetch_payment_fn = fetch_payment_fn or razorpay_client.fetch_payment
    if not razorpay_client.verify_webhook_signature(raw_body, signature, settings.RAZORPAY_WEBHOOK_SECRET):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    event = payload.get("event")
    if event == "refund.processed":
        return await _handle_refund(db, payload, revoke, fetch_payment_fn)
    entity = (((payload.get("payload") or {}).get("payment") or {}).get("entity")) or {}
    rp_order_id = entity.get("order_id")
    payment_id = entity.get("id")
    if event not in ("payment.captured", "order.paid", "payment.failed") or not rp_order_id or not payment_id:
        return {"status": "ignored"}
    order = await _get_order(db, rp_order_id, lock=True)
    if not order:
        return {"status": "ignored"}
    if order.status == PaymentStatus.REFUNDED:
        return {"status": "ignored"}  # a replayed capture must never undo a refund
    if event == "payment.failed":
        if order.status == PaymentStatus.CREATED:
            order.failureReason = str(entity.get("error_description") or "payment failed")[:300]
            await db.commit()
        return {"status": "recorded"}
    # captured / order.paid: amount and currency must match what the server priced
    if entity.get("amount") != order.amountPaise or entity.get("currency") != order.currency:
        order.failureReason = "amount or currency mismatch"
        await db.commit()
        return {"status": "ignored"}
    if entity.get("status") != "captured":
        return {"status": "ignored"}
    if order.status == PaymentStatus.PAID and order.razorpayPaymentId != payment_id:
        return {"status": "ignored"}
    await fulfill_order(db, order, payment_id, enroll)
    return {"status": "ok"}


async def has_paid_order(db: AsyncSession, user_id: str, course_id: str) -> bool:
    stmt = select(PaymentOrder.id).where(and_(
        PaymentOrder.userId == UUID(str(user_id)),
        PaymentOrder.courseId == UUID(str(course_id)),
        PaymentOrder.status == PaymentStatus.PAID,
    )).limit(1)
    return (await db.execute(stmt)).first() is not None
