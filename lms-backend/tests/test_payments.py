import hashlib, hmac, json, uuid
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.payments import razorpay_client, service
from app.payments.models import PaymentOrder, PaymentStatus
from app.payments.pricing import amount_in_paise, effective_price, is_paid_course
from sqlalchemy import select

KEY_SECRET = "key_secret"
HOOK = "hook_secret"


def course(**kw):
    d = dict(id=uuid.uuid4(), title="C", isFree=False, price=Decimal("499.00"),
             discountPrice=None, currency="INR")
    d.update(kw)
    return SimpleNamespace(**d)


def sig(order_id, payment_id, secret=KEY_SECRET):
    return hmac.new(secret.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()


def hook_sig(body: bytes, secret=HOOK):
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


class Enroller:
    def __init__(self, raises=None):
        self.calls = []
        self.raises = raises

    async def __call__(self, db, course_id, user_id):
        self.calls.append((course_id, user_id))
        await db.commit()
        if self.raises:
            raise self.raises


@pytest.fixture(autouse=True)
def fake_razorpay(monkeypatch):
    PROVIDER.clear()
    async def fake_create(key_id, key_secret, amount, currency, receipt, notes):
        return {"id": "order_" + uuid.uuid4().hex[:10], "amount": amount, "currency": currency}
    monkeypatch.setattr(razorpay_client, "create_order", fake_create)


PROVIDER = {}


async def fake_fetch_payment(key_id, key_secret, payment_id):
    if payment_id not in PROVIDER:
        raise HTTPException(status_code=400, detail="Payment not found")
    return PROVIDER[payment_id]


async def do_verify(db, user, order_id, payment_id, signature, enroll, status="captured", amount=None,
                    currency=None, bind_order=None):
    """verify_checkout against a fake provider that reports `status` for this payment."""
    order = (await db.execute(select(PaymentOrder).where(PaymentOrder.razorpayOrderId == order_id))).scalar_one_or_none()
    if order is not None:
        PROVIDER[payment_id] = {
            "id": payment_id, "order_id": bind_order or order_id, "status": status,
            "amount": amount if amount is not None else order.amountPaise,
            "currency": currency or order.currency,
        }
    return await service.verify_checkout(db, user, order_id, payment_id, signature, enroll,
                                         fetch_payment_fn=fake_fetch_payment)


async def all_orders(db):
    return (await db.execute(select(PaymentOrder))).scalars().all()


# ---- pricing ----
def test_pricing_uses_discount_only_when_lower():
    assert effective_price(course(discountPrice=Decimal("299"))) == Decimal("299")
    assert effective_price(course(discountPrice=Decimal("999"))) == Decimal("499.00")
    assert amount_in_paise(course(price=Decimal("499.50"))) == 49950


def test_free_courses():
    assert not is_paid_course(course(isFree=True))
    assert not is_paid_course(course(price=None))
    assert not is_paid_course(course(discountPrice=Decimal("0")))


# ---- order creation ----
async def make_order(db, user=None, **kw):
    user = user or str(uuid.uuid4())
    c = course(**kw)
    res = await service.create_course_order(db, c, user, already_enrolled=False)
    return c, user, res


async def test_order_amount_is_server_side(db):
    c, user, res = await make_order(db, discountPrice=Decimal("299"))
    assert res["amount"] == 29900 and res["currency"] == "INR"
    row = (await db.execute(select(PaymentOrder))).scalar_one()
    assert row.amountPaise == 29900 and str(row.userId) == user and row.status == "created"


async def test_order_rejections(db):
    with pytest.raises(HTTPException) as e:
        await service.create_course_order(db, course(isFree=True), str(uuid.uuid4()), False)
    assert e.value.status_code == 400
    with pytest.raises(HTTPException) as e:
        await service.create_course_order(db, course(currency="USD"), str(uuid.uuid4()), False)
    assert e.value.status_code == 400
    with pytest.raises(HTTPException) as e:
        await service.create_course_order(db, course(price=Decimal("0.50")), str(uuid.uuid4()), False)
    assert e.value.status_code == 400
    with pytest.raises(HTTPException) as e:
        await service.create_course_order(db, course(), str(uuid.uuid4()), True)
    assert e.value.status_code == 409


async def test_live_keys_refused(db, monkeypatch):
    monkeypatch.setattr(service.settings, "RAZORPAY_KEY_ID", "rzp_live_x")
    with pytest.raises(HTTPException) as e:
        await service.create_course_order(db, course(), str(uuid.uuid4()), False)
    assert e.value.status_code == 503


async def test_unconfigured_refused(db, monkeypatch):
    monkeypatch.setattr(service.settings, "RAZORPAY_KEY_SECRET", "")
    with pytest.raises(HTTPException) as e:
        await service.create_course_order(db, course(), str(uuid.uuid4()), False)
    assert e.value.status_code == 503


# ---- checkout verification ----
async def test_verify_success_enrolls_once_and_is_idempotent(db):
    c, user, res = await make_order(db)
    enroll = Enroller()
    out = await do_verify(db, user, res["orderId"], "pay_1", sig(res["orderId"], "pay_1"), enroll)
    assert out["status"] == "paid" and not out["alreadyProcessed"]
    again = await do_verify(db, user, res["orderId"], "pay_1", sig(res["orderId"], "pay_1"), enroll)
    assert again["alreadyProcessed"]
    assert len(set(enroll.calls)) == 1  # enrollment is re-attempted on retry (repairs half-done work), same target
    assert len(await all_orders(db)) == 1
    assert await service.has_paid_order(db, user, str(c.id))


async def test_verify_bad_signature(db):
    c, user, res = await make_order(db)
    enroll = Enroller()
    with pytest.raises(HTTPException) as e:
        await do_verify(db, user, res["orderId"], "pay_1", sig(res["orderId"], "pay_1", "wrong"), enroll)
    assert e.value.status_code == 400 and not enroll.calls
    assert not await service.has_paid_order(db, user, str(c.id))


async def test_verify_other_users_order_is_404(db):
    c, user, res = await make_order(db)
    with pytest.raises(HTTPException) as e:
        await do_verify(db, str(uuid.uuid4()), res["orderId"], "pay_1", sig(res["orderId"], "pay_1"), Enroller())
    assert e.value.status_code == 404


async def test_verify_second_payment_id_on_paid_order_rejected(db):
    c, user, res = await make_order(db)
    enroll = Enroller()
    await do_verify(db, user, res["orderId"], "pay_1", sig(res["orderId"], "pay_1"), enroll)
    with pytest.raises(HTTPException) as e:
        await do_verify(db, user, res["orderId"], "pay_2", sig(res["orderId"], "pay_2"), enroll)
    assert e.value.status_code == 409 and len(enroll.calls) == 1


async def test_already_enrolled_409_still_counts_as_paid(db):
    c, user, res = await make_order(db)
    enroll = Enroller(raises=HTTPException(status_code=409, detail="x"))
    out = await do_verify(db, user, res["orderId"], "pay_1", sig(res["orderId"], "pay_1"), enroll)
    assert out["status"] == "paid"


async def test_enroll_failure_keeps_paid_record(db):
    c, user, res = await make_order(db)
    enroll = Enroller(raises=HTTPException(status_code=500, detail="boom"))
    with pytest.raises(HTTPException):
        await do_verify(db, user, res["orderId"], "pay_1", sig(res["orderId"], "pay_1"), enroll)
    assert await service.has_paid_order(db, user, str(c.id))


# ---- cancel ----
async def test_cancel_only_own_created_order(db):
    c, user, res = await make_order(db)
    with pytest.raises(HTTPException):
        await service.cancel_order(db, str(uuid.uuid4()), res["orderId"])
    assert (await service.cancel_order(db, user, res["orderId"]))["status"] == "cancelled"
    # a paid order cannot be cancelled
    c2, user2, res2 = await make_order(db)
    await do_verify(db, user2, res2["orderId"], "pay_9", sig(res2["orderId"], "pay_9"), Enroller())
    assert (await service.cancel_order(db, user2, res2["orderId"]))["status"] == "paid"


# ---- webhook ----
def event(order_id, payment_id="pay_w", amount=49900, currency="INR", status="captured", name="payment.captured"):
    return {"event": name, "payload": {"payment": {"entity": {
        "id": payment_id, "order_id": order_id, "amount": amount, "currency": currency, "status": status}}}}


class Revoker:
    def __init__(self):
        self.calls = []

    async def __call__(self, db, course_id, user_id):
        self.calls.append((course_id, user_id))


async def hook(db, payload, enroll, secret=HOOK, revoke=None):
    raw = json.dumps(payload).encode()
    return await service.handle_webhook(db, raw, hook_sig(raw, secret), payload, enroll, revoke,
                                        fetch_payment_fn=fake_fetch_payment)


async def test_webhook_fulfills_and_is_idempotent(db):
    c, user, res = await make_order(db)
    enroll = Enroller()
    assert (await hook(db, event(res["orderId"]), enroll))["status"] == "ok"
    await hook(db, event(res["orderId"]), enroll)
    assert len(set(enroll.calls)) == 1


async def test_webhook_bad_signature_and_missing_secret(db, monkeypatch):
    c, user, res = await make_order(db)
    payload = event(res["orderId"])
    raw = json.dumps(payload).encode()
    with pytest.raises(HTTPException):
        await service.handle_webhook(db, raw, hook_sig(raw, "nope"), payload, Enroller())
    with pytest.raises(HTTPException):
        await service.handle_webhook(db, raw, None, payload, Enroller())
    monkeypatch.setattr(service.settings, "RAZORPAY_WEBHOOK_SECRET", "")
    with pytest.raises(HTTPException):
        await service.handle_webhook(db, raw, hook_sig(raw, ""), payload, Enroller())


async def test_webhook_amount_currency_mismatch_not_fulfilled(db):
    c, user, res = await make_order(db)
    enroll = Enroller()
    assert (await hook(db, event(res["orderId"], amount=100), enroll))["status"] == "ignored"
    assert (await hook(db, event(res["orderId"], currency="USD"), enroll))["status"] == "ignored"
    assert not enroll.calls and not await service.has_paid_order(db, user, str(c.id))


async def test_webhook_unknown_order_and_uncaptured(db):
    c, user, res = await make_order(db)
    enroll = Enroller()
    assert (await hook(db, event("order_unknown"), enroll))["status"] == "ignored"
    assert (await hook(db, event(res["orderId"], status="failed"), enroll))["status"] == "ignored"
    assert not enroll.calls


async def test_webhook_failed_event_never_downgrades_paid(db):
    c, user, res = await make_order(db)
    enroll = Enroller()
    await hook(db, event(res["orderId"]), enroll)
    await hook(db, event(res["orderId"], name="payment.failed", status="failed"), enroll)
    row = (await db.execute(select(PaymentOrder))).scalar_one()
    assert row.status == PaymentStatus.PAID


async def test_webhook_other_payment_on_paid_order_ignored(db):
    c, user, res = await make_order(db)
    enroll = Enroller()
    await hook(db, event(res["orderId"], "pay_a"), enroll)
    assert (await hook(db, event(res["orderId"], "pay_b"), enroll))["status"] == "ignored"
    assert len(enroll.calls) == 1


async def test_concurrent_enrollment_integrity_error_is_tolerated(db):
    from sqlalchemy.exc import IntegrityError
    c, user, res = await make_order(db)
    enroll = Enroller(raises=IntegrityError("x", {}, Exception("dup")))
    out = await do_verify(db, user, res["orderId"], "pay_1", sig(res["orderId"], "pay_1"), enroll)
    assert out["status"] == "paid"
    assert await service.has_paid_order(db, user, str(c.id))


async def test_second_order_refused_after_paid(db):
    c, user, res = await make_order(db)
    await do_verify(db, user, res["orderId"], "pay_1", sig(res["orderId"], "pay_1"), Enroller())
    with pytest.raises(HTTPException) as e:
        await service.create_course_order(db, c, user, False)
    assert e.value.status_code == 409


# ---- server-side payment confirmation (checkout path) ----
async def test_verify_rejects_unsettled_or_mismatched_provider_payment(db):
    c, user, res = await make_order(db)
    enroll = Enroller()
    s1 = sig(res["orderId"], "pay_1")
    for kwargs, code in [
        (dict(status="authorized"), 409),            # not captured yet: no access
        (dict(status="created"), 409),
        (dict(status="failed"), 400),
        (dict(amount=100), 400),                     # wrong amount
        (dict(currency="USD"), 400),
        (dict(bind_order="order_other"), 400),       # payment belongs to a different order
    ]:
        with pytest.raises(HTTPException) as e:
            await do_verify(db, user, res["orderId"], "pay_1", s1, enroll, **kwargs)
        assert e.value.status_code == code, kwargs
    assert not enroll.calls and not await service.has_paid_order(db, user, str(c.id))
    out = await do_verify(db, user, res["orderId"], "pay_1", s1, enroll)  # now captured
    assert out["status"] == "paid"


async def test_verify_unknown_payment_at_provider(db):
    c, user, res = await make_order(db)
    with pytest.raises(HTTPException) as e:
        await service.verify_checkout(db, user, res["orderId"], "pay_nope", sig(res["orderId"], "pay_nope"),
                                      Enroller(), fetch_payment_fn=fake_fetch_payment)
    assert e.value.status_code == 400


# ---- refunds ----
def refund_event(payment_id, amount_refunded, refund_amount=None):
    return {"event": "refund.processed", "payload": {
        "payment": {"entity": {"id": payment_id, "amount_refunded": amount_refunded}},
        "refund": {"entity": {"id": "rfnd_1", "payment_id": payment_id, "amount": refund_amount or amount_refunded}}}}


async def paid_order(db):
    c, user, res = await make_order(db)
    await do_verify(db, user, res["orderId"], "pay_1", sig(res["orderId"], "pay_1"), Enroller())
    return c, user, res


async def test_full_refund_revokes_and_blocks_replays(db):
    c, user, res = await paid_order(db)
    revoke = Revoker()
    assert (await hook(db, refund_event("pay_1", 49900), Enroller(), revoke=revoke))["status"] == "refunded"
    row = (await all_orders(db))[0]
    assert row.status == PaymentStatus.REFUNDED and row.refundedPaise == 49900
    assert revoke.calls == [(str(c.id), user)]
    assert not await service.has_paid_order(db, user, str(c.id))
    # replayed refund webhook is harmless; replayed capture cannot resurrect the order
    await hook(db, refund_event("pay_1", 49900), Enroller(), revoke=revoke)
    enroll = Enroller()
    assert (await hook(db, event(res["orderId"], "pay_1"), enroll))["status"] == "ignored"
    assert not enroll.calls and (await all_orders(db))[0].status == PaymentStatus.REFUNDED
    with pytest.raises(HTTPException) as e:  # and the checkout callback cannot either
        await do_verify(db, user, res["orderId"], "pay_1", sig(res["orderId"], "pay_1"), enroll)
    assert e.value.status_code == 409


async def test_partial_refund_keeps_access(db):
    c, user, res = await paid_order(db)
    revoke = Revoker()
    out = await hook(db, refund_event("pay_1", 10000), Enroller(), revoke=revoke)
    assert out["status"] == "partial_refund_recorded" and not revoke.calls
    row = (await all_orders(db))[0]
    assert row.status == PaymentStatus.PAID and row.refundedPaise == 10000
    await hook(db, refund_event("pay_1", 49900), Enroller(), revoke=revoke)  # remainder refunded later
    assert (await all_orders(db))[0].status == PaymentStatus.REFUNDED and len(revoke.calls) == 1


async def test_refund_for_unknown_or_unpaid_payment_ignored(db):
    c, user, res = await make_order(db)
    revoke = Revoker()
    assert (await hook(db, refund_event("pay_zzz", 100), Enroller(), revoke=revoke))["status"] == "ignored"
    assert not revoke.calls and (await all_orders(db))[0].status == PaymentStatus.CREATED
