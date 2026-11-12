import os
import sys

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("RAZORPAY_KEY_ID", "rzp_test_abc")
os.environ.setdefault("RAZORPAY_KEY_SECRET", "key_secret")
os.environ.setdefault("RAZORPAY_WEBHOOK_SECRET", "hook_secret")
os.environ.setdefault("GROQ_API_KEY", "test")  # the app builds an LLM client at import time

import app.models  # noqa: E402,F401  (registers users/courses so the payment FKs resolve)
from app.database import Base  # noqa: E402
from app.payments.models import PaymentOrder  # noqa: E402


@pytest_asyncio.fixture
async def db():
    """Fast SQLite session with only the payment table, for service-level unit tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=[PaymentOrder.__table__]))
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()
