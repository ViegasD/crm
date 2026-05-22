"""Durable persistence + replay support for incoming webhooks."""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.enums import WebhookEventStatus
from app.models.webhook import WebhookEvent

logger = logging.getLogger(__name__)


def _hash_signature(signature: str | None) -> str | None:
    if not signature:
        return None
    return hashlib.sha256(signature.encode()).hexdigest()


async def record_webhook_event(
    *,
    provider: str,
    headers: dict[str, Any],
    payload: dict[str, Any],
    workspace_id: UUID | None = None,
    channel_account_id: UUID | None = None,
    signature: str | None = None,
) -> UUID:
    """Persist a webhook event in its own transaction.

    Returns the new event id so callers can update status after async work.
    """
    event_id: UUID | None = None
    try:
        async with AsyncSessionLocal() as db:
            event = WebhookEvent(
                workspace_id=workspace_id,
                channel_account_id=channel_account_id,
                provider=provider,
                signature_hash=_hash_signature(signature),
                headers={k: v for k, v in headers.items() if k.lower() != "authorization"},
                payload=payload,
                status=WebhookEventStatus.received,
            )
            db.add(event)
            await db.commit()
            event_id = event.id
    except SQLAlchemyError:
        logger.exception("Failed to persist webhook event")
    return event_id  # type: ignore[return-value]


async def mark_event_status(
    event_id: UUID | None,
    status: WebhookEventStatus,
    error_message: str | None = None,
) -> None:
    if event_id is None:
        return
    try:
        async with AsyncSessionLocal() as db:
            event = await db.get(WebhookEvent, event_id)
            if not event:
                return
            event.status = status
            event.attempts += 1
            event.error_message = error_message
            if status in (
                WebhookEventStatus.processed,
                WebhookEventStatus.ignored,
            ):
                event.processed_at = datetime.now(timezone.utc)
                event.next_retry_at = None
            elif status == WebhookEventStatus.failed:
                # retry clock is handled by webhook_retry.schedule_retry
                event.last_error_at = datetime.now(timezone.utc)
            await db.commit()
    except SQLAlchemyError:
        logger.exception("Failed to update webhook event status: %s", event_id)


async def find_replayable(
    db: AsyncSession, provider: str, signature: str
) -> WebhookEvent | None:
    """Return a previous processed event for the same provider/signature."""
    sig_hash = _hash_signature(signature)
    if not sig_hash:
        return None
    result = await db.execute(
        select(WebhookEvent).where(
            WebhookEvent.provider == provider,
            WebhookEvent.signature_hash == sig_hash,
        )
    )
    return result.scalar_one_or_none()
