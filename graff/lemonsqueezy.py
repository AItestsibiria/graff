# Copyright (c) 2025 BAI / AItestsibiria. Business Source License 1.1.
# Commercial SaaS use requires a commercial license: egnovoselov@gmail.com
"""Lemon Squeezy payment integration.

Env:
  LS_API_KEY         — API-ключ (Settings → API)
  LS_STORE_ID        — ID магазина (Settings → Stores)
  LS_VARIANT_PRO     — Variant ID тарифа Pro
  LS_VARIANT_TEAM    — Variant ID тарифа Team
  LS_WEBHOOK_SECRET  — секрет вебхука (Settings → Webhooks)
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os

LS_API_KEY        = os.environ.get("LS_API_KEY", "")
LS_STORE_ID       = os.environ.get("LS_STORE_ID", "")
LS_VARIANT_PRO    = os.environ.get("LS_VARIANT_PRO", "")
LS_VARIANT_TEAM   = os.environ.get("LS_VARIANT_TEAM", "")
LS_WEBHOOK_SECRET = os.environ.get("LS_WEBHOOK_SECRET", "")

PLAN_VARIANTS = {"pro": LS_VARIANT_PRO, "team": LS_VARIANT_TEAM}

_HEADERS = {
    "Accept": "application/vnd.api+json",
    "Content-Type": "application/vnd.api+json",
}


def _headers() -> dict:
    return {**_HEADERS, "Authorization": f"Bearer {LS_API_KEY}"}


async def create_checkout(email: str, plan: str, api_key: str, success_url: str) -> str:
    """Создать сессию оплаты → вернуть URL страницы Lemon Squeezy."""
    import httpx

    variant_id = os.environ.get(f"LS_VARIANT_{plan.upper()}", "")
    if not variant_id:
        raise ValueError(f"LS_VARIANT_{plan.upper()} не задан")

    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": email,
                    "custom": {"api_key": api_key, "plan": plan},
                },
                "product_options": {
                    "redirect_url": success_url,
                },
            },
            "relationships": {
                "store":   {"data": {"type": "stores",   "id": str(os.environ.get("LS_STORE_ID", ""))}},
                "variant": {"data": {"type": "variants", "id": str(variant_id)}},
            },
        }
    }

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            "https://api.lemonsqueezy.com/v1/checkouts",
            headers=_headers(),
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
        return data["data"]["attributes"]["url"]


def verify_webhook(payload: bytes, signature: str) -> bool:
    """Проверить HMAC-SHA256 подпись вебхука Lemon Squeezy."""
    if not LS_WEBHOOK_SECRET:
        return True  # dev-режим
    expected = hmac.new(
        LS_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def parse_webhook(body: dict) -> dict | None:
    """Разобрать событие вебхука → вернуть {email, plan, sub_id} или None."""
    event = body.get("meta", {}).get("event_name", "")
    if event not in ("order_created", "subscription_created",
                     "subscription_updated", "subscription_resumed"):
        return None

    attrs = body.get("data", {}).get("attributes", {})
    custom = body.get("meta", {}).get("custom_data") or {}

    # plan из custom_data (мы передаём при создании чекаута)
    plan = custom.get("plan", "pro")
    api_key = custom.get("api_key", "")
    email = attrs.get("user_email") or attrs.get("email", "")
    sub_id = str(body.get("data", {}).get("id", ""))

    return {"email": email, "plan": plan, "api_key": api_key, "sub_id": sub_id}
