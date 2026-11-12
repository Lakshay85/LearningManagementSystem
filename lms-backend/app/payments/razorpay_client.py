"""Minimal Razorpay REST client (orders only) plus signature helpers.

Uses httpx (already a dependency) so no extra SDK is needed.
"""
import hashlib
import hmac
from typing import Optional

import httpx
from fastapi import HTTPException

RAZORPAY_API = "https://api.razorpay.com/v1"


def _hmac_hex(secret: str, message: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def verify_checkout_signature(order_id: str, payment_id: str, signature: str, key_secret: str) -> bool:
    """Checkout callback: HMAC_SHA256(order_id + '|' + payment_id, key_secret)."""
    if not (order_id and payment_id and signature and key_secret):
        return False
    expected = _hmac_hex(key_secret, f"{order_id}|{payment_id}".encode("utf-8"))
    return hmac.compare_digest(expected, signature)


def verify_webhook_signature(raw_body: bytes, signature: Optional[str], webhook_secret: str) -> bool:
    """Webhook: HMAC_SHA256(raw request body, webhook_secret) in X-Razorpay-Signature."""
    if not (signature and webhook_secret):
        return False
    expected = _hmac_hex(webhook_secret, raw_body)
    return hmac.compare_digest(expected, signature)


async def create_order(key_id: str, key_secret: str, amount_paise: int, currency: str,
                       receipt: str, notes: dict) -> dict:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{RAZORPAY_API}/orders",
                auth=(key_id, key_secret),
                json={"amount": amount_paise, "currency": currency, "receipt": receipt, "notes": notes},
            )
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Payment provider is unreachable. Please try again.")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Payment provider rejected the order. Please try again.")
    data = resp.json()
    if data.get("amount") != amount_paise or data.get("currency") != currency or not data.get("id"):
        raise HTTPException(status_code=502, detail="Payment provider returned an unexpected order.")
    return data


async def fetch_payment(key_id: str, key_secret: str, payment_id: str) -> dict:
    """Server-side lookup of a payment (the source of truth for status, amount, order binding)."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{RAZORPAY_API}/payments/{payment_id}", auth=(key_id, key_secret))
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Payment provider is unreachable. Please try again.")
    if resp.status_code == 404:
        raise HTTPException(status_code=400, detail="Payment not found")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Could not confirm the payment with the provider. Please try again.")
    return resp.json()
