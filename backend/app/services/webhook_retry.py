"""Retry orchestration for durable webhook_events processing.

Strategy: jittered exponential backoff.
- attempt 1 → 60s
- attempt 2 → ~5min
- attempt 3 → ~30min
- attempt 4 → ~2h
- attempt 5 → ~6h
- attempt 6+ → ~24h
After max_attempts (default 8) → status = dead_letter, requires manual replay.
"""
from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.channel import ChannelAccount
from app.models.enums import WebhookEventStatus, WhatsAppProvider
from app.models.webhook import WebhookEvent

logger = logging.getLogger(__name__)

# Base delays in seconds, attempt index (1-based) → base delay
_BASE_DELAYS = [60, 300, 1800, 7200, 21600, 86400, 86400, 86400]


def next_delay_seconds(attempt: int) -> int:
    """Return jittered backoff for the next try after `attempt` failures."""
    idx = max(0, min(attempt - 1, len(_BASE_DELAYS) - 1))
    base = _BASE_DELAYS[idx]
    jitter = random.uniform(0.5, 1.5)
    return int(base * jitter)


async def schedule_retry(event_id: UUID, error_message: str | None = None) -> None:
    """Update the event so the worker picks it up after a backoff delay.

    If attempts >= max_attempts, the event is moved to dead_letter.
    """
    async with AsyncSessionLocal() as db:
        event = await db.get(WebhookEvent, event_id)
        if not event:
            return
        event.attempts += 1
        event.last_error_at = datetime.now(timezone.utc)
        event.error_message = error_message
        if event.attempts >= event.max_attempts:
            event.status = WebhookEventStatus.dead_letter
            event.next_retry_at = None
        else:
            event.status = WebhookEventStatus.failed
            delay = next_delay_seconds(event.attempts)
            event.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
        await db.commit()


async def reprocess_event(event_id: UUID) -> tuple[bool, str | None]:
    """Reprocess a single webhook event. Returns (success, error_message)."""
    from app.channels.whatsapp.evolution import EvolutionAdapter
    from app.channels.whatsapp.meta_cloud import MetaCloudAdapter
    from app.core.encryption import decrypt_payload
    from app.models.channel import ChannelCredential
    from app.services.message_service import persist_normalized_event
    from app.services.webhook_event_service import mark_event_status
    from app.websocket.manager import manager

    async with AsyncSessionLocal() as db:
        event = await db.get(WebhookEvent, event_id)
        if not event:
            return False, "event not found"
        if event.status == WebhookEventStatus.processed:
            return True, None
        if not event.channel_account_id:
            await mark_event_status(event_id, WebhookEventStatus.ignored, "no channel account")
            return False, "no channel account"
        account = await db.get(ChannelAccount, event.channel_account_id)
        if not account:
            await mark_event_status(event_id, WebhookEventStatus.ignored, "channel account gone")
            return False, "channel account gone"

        # Build adapter for the provider
        try:
            if event.provider == "meta_cloud":
                cred_q = await db.execute(
                    select(ChannelCredential).where(
                        ChannelCredential.channel_account_id == account.id,
                        ChannelCredential.credential_type == "meta_cloud",
                    )
                )
                cred = cred_q.scalar_one_or_none()
                app_secret = decrypt_payload(cred.encrypted_payload).get("app_secret") if cred else ""
                adapter = MetaCloudAdapter(
                    access_token="",
                    phone_number_id=account.phone_number_id or "",
                    app_secret=app_secret or "",
                )
            elif event.provider == "evolution":
                cred_q = await db.execute(
                    select(ChannelCredential).where(
                        ChannelCredential.channel_account_id == account.id,
                        ChannelCredential.credential_type == "evolution",
                    )
                )
                cred = cred_q.scalar_one_or_none()
                creds_dict = decrypt_payload(cred.encrypted_payload) if cred else {}
                mode = "cloud" if account.provider == WhatsAppProvider.evolution_cloud else "baileys"
                adapter = EvolutionAdapter(
                    instance_name=account.external_account_id or "",
                    api_key=creds_dict.get("evolution_api_key"),
                    base_url=creds_dict.get("evolution_base_url"),
                    webhook_secret=creds_dict.get("webhook_secret"),
                    mode=mode,
                )
            else:
                await mark_event_status(event_id, WebhookEventStatus.ignored, f"unknown provider {event.provider}")
                return False, f"unknown provider {event.provider}"

            events = adapter.parse_webhook(event.headers or {}, event.payload or {})
            for ne in events:
                ne.workspace_id = str(account.workspace_id)
                ne.channel_account_id = str(account.id)
                msg = await persist_normalized_event(db, account, ne)
                if msg:
                    await manager.broadcast(
                        str(account.workspace_id),
                        {
                            "type": "message.new",
                            "conversation_id": str(msg.conversation_id),
                            "message_id": str(msg.id),
                        },
                    )
            await db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.exception("webhook reprocess failed: %s", event_id)
            await schedule_retry(event_id, str(exc))
            return False, str(exc)

    await mark_event_status(event_id, WebhookEventStatus.processed)
    return True, None


async def claim_pending_events(limit: int = 25) -> list[UUID]:
    """Return up to `limit` event ids ready to be tried again.

    Picks events whose status is failed/received AND next_retry_at <= now (or null
    if just received).
    """
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        q = (
            select(WebhookEvent.id)
            .where(
                WebhookEvent.status.in_([WebhookEventStatus.failed, WebhookEventStatus.received]),
                (WebhookEvent.next_retry_at.is_(None)) | (WebhookEvent.next_retry_at <= now),
            )
            .order_by(WebhookEvent.next_retry_at.asc().nullsfirst(), WebhookEvent.created_at.asc())
            .limit(limit)
        )
        result = await db.execute(q)
        return [row[0] for row in result.all()]


async def manual_retry(event_id: UUID) -> tuple[bool, str | None]:
    """Manual replay: reset the retry clock and try once now."""
    async with AsyncSessionLocal() as db:
        event = await db.get(WebhookEvent, event_id)
        if not event:
            return False, "event not found"
        event.next_retry_at = datetime.now(timezone.utc)
        if event.status == WebhookEventStatus.dead_letter:
            event.attempts = 0
            event.status = WebhookEventStatus.failed
        await db.commit()
    return await reprocess_event(event_id)
