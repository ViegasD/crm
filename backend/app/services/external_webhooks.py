"""Outbound webhooks: deliver internal events to external customer URLs.

Public API:
    await emit_event(workspace_id, event_type, payload)
        Enqueues an api_webhook_deliveries row per matching active subscription.
        The Celery worker (webhook.deliver_external) actually performs the POST
        with HMAC-SHA256 signature in X-CRM-Signature.

Backoff: jittered exponential (1m, 5m, 30m, 2h, 6h, 24h × 3) up to 8 attempts.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.encryption import decrypt_payload
from app.models.stage9_extras import (
    ExternalWebhookDelivery,
    ExternalWebhookSubscription,
)

logger = logging.getLogger(__name__)

_BASE_DELAYS = [60, 300, 1800, 7200, 21600, 86400, 86400, 86400]
MAX_ATTEMPTS = 8


def _next_delay(attempt: int) -> int:
    idx = max(0, min(attempt - 1, len(_BASE_DELAYS) - 1))
    return int(_BASE_DELAYS[idx] * random.uniform(0.5, 1.5))


def _sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _secret_value(raw: str) -> str:
    try:
        return str(decrypt_payload(raw).get("secret") or raw)
    except Exception:  # noqa: BLE001
        return raw


async def emit_event(workspace_id: UUID, event_type: str, payload: dict) -> int:
    """Create one delivery per matching subscription. Returns count enqueued."""
    enqueued = 0
    try:
        async with AsyncSessionLocal() as db:
            subs = (
                await db.execute(
                    select(ExternalWebhookSubscription).where(
                        ExternalWebhookSubscription.workspace_id == workspace_id,
                        ExternalWebhookSubscription.active.is_(True),
                    )
                )
            ).scalars().all()
            for sub in subs:
                if sub.events and event_type not in sub.events:
                    continue
                db.add(
                    ExternalWebhookDelivery(
                        subscription_id=sub.id,
                        workspace_id=workspace_id,
                        event_type=event_type,
                        payload=payload,
                        status="pending",
                        next_retry_at=datetime.now(timezone.utc),
                    )
                )
                enqueued += 1
            if enqueued:
                await db.commit()
    except SQLAlchemyError:
        logger.exception("emit_event persistence failed")
    return enqueued


async def deliver_one(delivery_id: UUID) -> tuple[bool, str | None]:
    async with AsyncSessionLocal() as db:
        delivery = await db.get(ExternalWebhookDelivery, delivery_id)
        if not delivery:
            return False, "delivery not found"
        if delivery.status == "delivered":
            return True, None
        sub = await db.get(ExternalWebhookSubscription, delivery.subscription_id)
        if not sub or not sub.active:
            delivery.status = "cancelled"
            delivery.last_error = "subscription inactive"
            await db.commit()
            return False, delivery.last_error

        body_dict = {
            "event_type": delivery.event_type,
            "workspace_id": str(sub.workspace_id),
            "payload": delivery.payload,
            "delivery_id": str(delivery.id),
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        body_bytes = json.dumps(body_dict, separators=(",", ":"), sort_keys=True).encode()
        headers = {
            "Content-Type": "application/json",
            "X-CRM-Event": delivery.event_type,
            "X-CRM-Delivery": str(delivery.id),
            "X-CRM-Signature": _sign(_secret_value(sub.secret), body_bytes),
        }
        delivery.attempts += 1
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(sub.url, content=body_bytes, headers=headers)
                delivery.response_status = resp.status_code
                resp.raise_for_status()
            delivery.status = "delivered"
            delivery.delivered_at = datetime.now(timezone.utc)
            delivery.next_retry_at = None
            delivery.last_error = None
            await db.commit()
            return True, None
        except Exception as exc:  # noqa: BLE001
            delivery.last_error = str(exc)
            if delivery.attempts >= MAX_ATTEMPTS:
                delivery.status = "dead_letter"
                delivery.next_retry_at = None
            else:
                delivery.status = "pending"
                delivery.next_retry_at = datetime.now(timezone.utc) + timedelta(
                    seconds=_next_delay(delivery.attempts)
                )
            await db.commit()
            return False, str(exc)


async def claim_pending_deliveries(limit: int = 25) -> list[UUID]:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ExternalWebhookDelivery.id)
            .where(
                ExternalWebhookDelivery.status == "pending",
                (ExternalWebhookDelivery.next_retry_at.is_(None))
                | (ExternalWebhookDelivery.next_retry_at <= now),
            )
            .order_by(ExternalWebhookDelivery.next_retry_at.asc().nullsfirst())
            .limit(limit)
        )
        return [row[0] for row in result.all()]
