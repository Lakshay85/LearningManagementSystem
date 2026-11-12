"""End-to-end tests against a real PostgreSQL (pgserver) and the real FastAPI routers.

Skipped automatically when `pgserver` is not installed (pip install pgserver).
Razorpay itself is never called: order creation is faked, signatures are computed locally.
"""
import asyncio
import hashlib
import hmac
import json
import tempfile
import uuid
from decimal import Decimal

import pytest
import pytest_asyncio

pgserver = pytest.importorskip("pgserver")

# The RAG package loads embedding models at import time (needs > 2 GB RAM and is unrelated to
# payments), so it is replaced by a light stub. Everything else is the real application.
import sys  # noqa: E402
import types  # noqa: E402
from fastapi import APIRouter  # noqa: E402

if "app.rag" not in sys.modules:
    _rag = types.ModuleType("app.rag")
    _rag.rag_router, _rag.ingest_router, _rag.rag_service = APIRouter(), APIRouter(), object()
    _svc = types.ModuleType("app.rag.service")
    _svc.rag_service = object()
    _dto = types.ModuleType("app.rag.dto")
    _dto.IngestFileDto = type("IngestFileDto", (), {})
    _rag.service, _rag.dto = _svc, _dto
    sys.modules.update({"app.rag": _rag, "app.rag.service": _svc, "app.rag.dto": _dto})

import httpx  # noqa: E402
from jose import jwt  # noqa: E402
from sqlalchemy import select, text, func  # noqa: E402
from sqlalchemy.dialects.postgresql import ENUM  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.models import User, Course, CourseEnrollment  # noqa: E402
from app.payments import razorpay_client  # noqa: E402
from app.payments.models import PaymentOrder  # noqa: E402

KEY_SECRET = "key_secret"
HOOK = "hook_secret"


@pytest.fixture(scope="session")
def pg_uri():
    d = tempfile.mkdtemp()
    server = pgserver.get_server(d)
    uri = server.get_uri()  # postgresql://postgres:@/postgres?host=/tmp/xxx
    host = uri.split("host=")[1]
    yield f"postgresql+asyncpg://postgres@/postgres?host={host}"
    server.cleanup()


@pytest_asyncio.fixture
async def env(pg_uri, monkeypatch):
    engine = create_async_engine(pg_uri)
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        enums = {}
        for table in Base.metadata.tables.values():
            for col in table.columns:
                if isinstance(col.type, ENUM) and col.type.name:
                    enums[col.type.name] = col.type.enums
        for name, values in enums.items():
            vals = ", ".join("'" + v.replace("'", "''") + "'" for v in values)
            await conn.execute(text(f"CREATE TYPE {name} AS ENUM ({vals})"))
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with Session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    counter = {"n": 0}

    async def fake_create(key_id, key_secret, amount, currency, receipt, notes):
        counter["n"] += 1
        return {"id": f"order_{counter['n']}_{uuid.uuid4().hex[:6]}", "amount": amount, "currency": currency}

    provider = {}

    async def fake_fetch(key_id, key_secret, payment_id):
        from fastapi import HTTPException
        if payment_id not in provider:
            raise HTTPException(status_code=400, detail="Payment not found")
        return provider[payment_id]

    monkeypatch.setattr(razorpay_client, "create_order", fake_create)
    monkeypatch.setattr(razorpay_client, "fetch_payment", fake_fetch)
    monkeypatch.setattr(settings, "RAZORPAY_KEY_ID", "rzp_test_abc")
    monkeypatch.setattr(settings, "RAZORPAY_KEY_SECRET", KEY_SECRET)
    monkeypatch.setattr(settings, "RAZORPAY_WEBHOOK_SECRET", HOOK)

    async with Session() as s:
        faculty = User(email="f@x.com", password="x", role="faculty", firstName="F", lastName="T")
        stu1 = User(email="s1@x.com", password="x", role="student", firstName="A", lastName="B")
        stu2 = User(email="s2@x.com", password="x", role="student", firstName="C", lastName="D")
        s.add_all([faculty, stu1, stu2])
        await s.flush()
        paid = Course(title="Paid", slug="paid", status="published", visibility="public", isFree=False,
                      price=Decimal("500.00"), discountPrice=Decimal("399.00"), currency="INR",
                      instructorId=faculty.id)
        free = Course(title="Free", slug="free", status="published", visibility="public", isFree=True,
                      instructorId=faculty.id)
        draft = Course(title="Draft", slug="draft", status="draft", isFree=False, price=Decimal("100"),
                       currency="INR", instructorId=faculty.id)
        s.add_all([paid, free, draft])
        await s.commit()
        ids = dict(stu1=str(stu1.id), stu2=str(stu2.id), paid=str(paid.id), free=str(free.id), draft=str(draft.id))

    def token(uid, role="student"):
        return jwt.encode({"sub": uid, "email": "x@x.com", "role": role}, settings.JWT_ACCESS_SECRET, algorithm="HS256")

    transport = httpx.ASGITransport(app=app)

    def client(uid):
        return httpx.AsyncClient(transport=transport, base_url="http://t",
                                 headers={"Authorization": f"Bearer {token(uid)}"})

    e = SimpleEnv(Session, ids, client)
    e.provider = provider
    yield e
    app.dependency_overrides.clear()
    await engine.dispose()


class SimpleEnv:
    def __init__(self, Session, ids, client):
        self.Session, self.ids, self.client = Session, ids, client

    async def enrollments(self, course_key="paid"):
        async with self.Session() as s:
            rows = (await s.execute(select(CourseEnrollment).where(
                CourseEnrollment.courseId == uuid.UUID(self.ids[course_key])))).scalars().all()
            count = (await s.get(Course, uuid.UUID(self.ids[course_key]))).enrollmentCount
            return rows, count

    def provider_pays(self, order_id, payment_id, status="captured", amount=39900, currency="INR", **extra):
        self.provider[payment_id] = {"id": payment_id, "order_id": order_id, "status": status,
                                     "amount": amount, "currency": currency, **extra}

    async def orders(self):
        async with self.Session() as s:
            return (await s.execute(select(PaymentOrder))).scalars().all()


def checkout_sig(order_id, payment_id, secret=KEY_SECRET):
    return hmac.new(secret.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()


def webhook_req(order_id, payment_id, amount, name="payment.captured", status="captured", secret=HOOK):
    body = json.dumps({"event": name, "payload": {"payment": {"entity": {
        "id": payment_id, "order_id": order_id, "amount": amount, "currency": "INR", "status": status}}}}).encode()
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return body, {"X-Razorpay-Signature": sig, "Content-Type": "application/json"}


async def new_order(c, course_id):
    r = await c.post(f"/payments/courses/{course_id}/order")
    assert r.status_code == 201, r.text
    return r.json()


async def test_paid_course_cannot_be_enrolled_without_payment(env):
    async with env.client(env.ids["stu1"]) as c:
        r = await c.post(f"/courses/{env.ids['paid']}/enroll")
        assert r.status_code == 402
        r = await c.post(f"/courses/{env.ids['free']}/enroll")
        assert r.status_code == 201
    rows, _ = await env.enrollments("paid")
    assert rows == []


async def test_unpaid_order_states_do_not_grant_access(env):
    async with env.client(env.ids["stu1"]) as c:
        o = await new_order(c, env.ids["paid"])
        assert (await c.post(f"/courses/{env.ids['paid']}/enroll")).status_code == 402
        await c.post("/payments/cancel", json={"razorpay_order_id": o["orderId"]})
        assert (await c.post(f"/courses/{env.ids['paid']}/enroll")).status_code == 402


async def test_full_purchase_flow_uses_server_price(env):
    async with env.client(env.ids["stu1"]) as c:
        o = await new_order(c, env.ids["paid"])
        env.provider_pays(o["orderId"], "pay_1")
        assert o["amount"] == 39900 and o["currency"] == "INR"   # discount price, from the DB
        r = await c.post("/payments/verify", json={
            "razorpay_order_id": o["orderId"], "razorpay_payment_id": "pay_1",
            "razorpay_signature": checkout_sig(o["orderId"], "pay_1")})
        assert r.status_code == 200 and r.json()["status"] == "paid"
        st = await c.get(f"/courses/{env.ids['paid']}/enrollment-status")
        assert st.json()["isEnrolled"] is True
        # a second order after paying is refused (no double charge)
        assert (await c.post(f"/payments/courses/{env.ids['paid']}/order")).status_code == 409
    rows, count = await env.enrollments()
    assert len(rows) == 1 and count == 1


async def test_bad_signature_and_other_users_order(env):
    async with env.client(env.ids["stu1"]) as c1, env.client(env.ids["stu2"]) as c2:
        o = await new_order(c1, env.ids["paid"])
        env.provider_pays(o["orderId"], "pay_1")
        bad = await c1.post("/payments/verify", json={
            "razorpay_order_id": o["orderId"], "razorpay_payment_id": "pay_1", "razorpay_signature": "00"})
        assert bad.status_code == 400
        # student 2 tries to use student 1's order with a *valid* signature
        steal = await c2.post("/payments/verify", json={
            "razorpay_order_id": o["orderId"], "razorpay_payment_id": "pay_1",
            "razorpay_signature": checkout_sig(o["orderId"], "pay_1")})
        assert steal.status_code == 404
        assert (await c2.post(f"/courses/{env.ids['paid']}/enroll")).status_code == 402
    rows, _ = await env.enrollments()
    assert rows == []


async def test_unavailable_and_free_courses_cannot_be_ordered(env):
    async with env.client(env.ids["stu1"]) as c:
        assert (await c.post(f"/payments/courses/{env.ids['draft']}/order")).status_code == 404
        assert (await c.post(f"/payments/courses/{env.ids['free']}/order")).status_code == 400
        assert (await c.post(f"/payments/courses/{uuid.uuid4()}/order")).status_code == 404
        assert (await c.post("/payments/courses/not-a-uuid/order")).status_code == 404


async def test_unauthenticated_calls_rejected(env):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        assert (await c.post(f"/payments/courses/{env.ids['paid']}/order")).status_code == 401
        assert (await c.post("/payments/verify", json={
            "razorpay_order_id": "a", "razorpay_payment_id": "b", "razorpay_signature": "c"})).status_code == 401


async def test_open_order_is_reused(env):
    async with env.client(env.ids["stu1"]) as c:
        o1 = await new_order(c, env.ids["paid"])
        o2 = await new_order(c, env.ids["paid"])
        assert o1["orderId"] == o2["orderId"]
    assert len(await env.orders()) == 1


async def test_webhook_signature_and_amount_checks(env):
    async with env.client(env.ids["stu1"]) as c:
        o = await new_order(c, env.ids["paid"])
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as anon:
            body, h = webhook_req(o["orderId"], "pay_1", 39900, secret="wrong")
            assert (await anon.post("/payments/webhook", content=body, headers=h)).status_code == 400
            body, h = webhook_req(o["orderId"], "pay_1", 100)  # wrong amount
            assert (await anon.post("/payments/webhook", content=body, headers=h)).json()["status"] == "ignored"
            assert (await c.post(f"/courses/{env.ids['paid']}/enroll")).status_code == 402
            body, h = webhook_req(o["orderId"], "pay_1", 39900)
            assert (await anon.post("/payments/webhook", content=body, headers=h)).json()["status"] == "ok"
        assert (await c.get(f"/courses/{env.ids['paid']}/enrollment-status")).json()["isEnrolled"] is True


async def test_concurrent_verify_and_webhooks_enroll_exactly_once(env):
    async with env.client(env.ids["stu1"]) as c:
        o = await new_order(c, env.ids["paid"])
        env.provider_pays(o["orderId"], "pay_1")
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as anon:
            body, h = webhook_req(o["orderId"], "pay_1", 39900)
            verify = {"razorpay_order_id": o["orderId"], "razorpay_payment_id": "pay_1",
                      "razorpay_signature": checkout_sig(o["orderId"], "pay_1")}
            results = await asyncio.gather(
                *[c.post("/payments/verify", json=verify) for _ in range(4)],
                *[anon.post("/payments/webhook", content=body, headers=h) for _ in range(4)],
            )
    assert all(r.status_code == 200 for r in results), [r.text for r in results if r.status_code != 200]
    rows, count = await env.enrollments()
    assert len(rows) == 1 and count == 1
    orders = await env.orders()
    assert len(orders) == 1 and orders[0].status == "paid" and orders[0].razorpayPaymentId == "pay_1"


async def test_enrollment_failure_keeps_payment_and_is_recoverable(env, monkeypatch):
    from app.courses.service import CourseService
    real = CourseService.enroll_in_course
    calls = {"n": 0}

    async def flaky(self, db, course_id, student_id, payment_verified=False):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("db hiccup")
        return await real(self, db, course_id, student_id, payment_verified=payment_verified)

    monkeypatch.setattr(CourseService, "enroll_in_course", flaky)
    async with env.client(env.ids["stu1"]) as c:
        o = await new_order(c, env.ids["paid"])
        env.provider_pays(o["orderId"], "pay_1")
        verify = {"razorpay_order_id": o["orderId"], "razorpay_payment_id": "pay_1",
                  "razorpay_signature": checkout_sig(o["orderId"], "pay_1")}
        r = await c.post("/payments/verify", json=verify)
        assert r.status_code == 500 and "Do not pay again" in r.text
        orders = await env.orders()
        assert orders[0].status == "paid"                      # payment is not lost
        rows, _ = await env.enrollments()
        assert rows == []                                       # but no half-state access
        r = await c.post("/payments/verify", json=verify)       # client/webhook retry repairs it
        assert r.status_code == 200
    rows, count = await env.enrollments()
    assert len(rows) == 1 and count == 1


async def test_paid_user_can_reenroll_after_drop_without_paying_again(env):
    async with env.client(env.ids["stu1"]) as c:
        o = await new_order(c, env.ids["paid"])
        env.provider_pays(o["orderId"], "pay_1")
        await c.post("/payments/verify", json={
            "razorpay_order_id": o["orderId"], "razorpay_payment_id": "pay_1",
            "razorpay_signature": checkout_sig(o["orderId"], "pay_1")})
        async with env.Session() as s:
            e = (await s.execute(select(CourseEnrollment))).scalar_one()
            e.status = "dropped"
            await s.commit()
        assert (await c.post(f"/courses/{env.ids['paid']}/enroll")).status_code == 201
        # another student who never paid still cannot
    async with env.client(env.ids["stu2"]) as c2:
        assert (await c2.post(f"/courses/{env.ids['paid']}/enroll")).status_code == 402


async def test_unsettled_provider_payment_does_not_grant_access(env):
    async with env.client(env.ids["stu1"]) as c:
        o = await new_order(c, env.ids["paid"])
        verify = {"razorpay_order_id": o["orderId"], "razorpay_payment_id": "pay_1",
                  "razorpay_signature": checkout_sig(o["orderId"], "pay_1")}
        env.provider_pays(o["orderId"], "pay_1", status="authorized")
        r = await c.post("/payments/verify", json=verify)
        assert r.status_code == 409 and "not confirmed" in r.text
        assert (await c.post(f"/courses/{env.ids['paid']}/enroll")).status_code == 402
        env.provider_pays(o["orderId"], "pay_1", amount=100)  # captured, but the wrong amount
        assert (await c.post("/payments/verify", json=verify)).status_code == 400
        env.provider_pays(o["orderId"], "pay_1")
        assert (await c.post("/payments/verify", json=verify)).status_code == 200


async def test_full_refund_revokes_access_and_allows_repurchase(env):
    async with env.client(env.ids["stu1"]) as c:
        o = await new_order(c, env.ids["paid"])
        env.provider_pays(o["orderId"], "pay_1")
        assert (await c.post("/payments/verify", json={
            "razorpay_order_id": o["orderId"], "razorpay_payment_id": "pay_1",
            "razorpay_signature": checkout_sig(o["orderId"], "pay_1")})).status_code == 200
        body = json.dumps({"event": "refund.processed", "payload": {
            "payment": {"entity": {"id": "pay_1", "amount_refunded": 39900}},
            "refund": {"entity": {"id": "rfnd_1", "payment_id": "pay_1", "amount": 39900}}}}).encode()
        h = {"X-Razorpay-Signature": hmac.new(HOOK.encode(), body, hashlib.sha256).hexdigest()}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as anon:
            for _ in range(2):  # replay is harmless
                assert (await anon.post("/payments/webhook", content=body, headers=h)).json()["status"] == "refunded"
        assert (await c.get(f"/courses/{env.ids['paid']}/enrolled-content")).status_code in (403, 404)
        assert (await c.post(f"/courses/{env.ids['paid']}/enroll")).status_code == 402
        orders = await env.orders()
        assert orders[0].status == "refunded" and orders[0].refundedPaise == 39900
        rows, count = await env.enrollments()
        assert len(rows) == 1 and rows[0].status == "dropped" and count == 0
        # can buy again after a full refund
        o2 = await new_order(c, env.ids["paid"])
        assert o2["orderId"] != o["orderId"]
