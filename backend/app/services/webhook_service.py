"""
Webhook event persistence helpers.

Each function opens its own AsyncSessionLocal session and commits independently,
so records are durable even if the request session is rolled back on error.
"""
import uuid
from datetime import datetime, timezone

from app.core.database import AsyncSessionLocal
from app.models.enums import WebhookEventStatus
from app.models.webhook import WebhookEvent


async def save_raw_event(
    provider: str,
    channel_account_id: uuid.UUID | None,
    workspace_id: uuid.UUID | None,
    payload: dict,
) -> uuid.UUID:
    """Persist a webhook event with status=received in its own transaction."""
    async with AsyncSessionLocal() as session:
        we = WebhookEvent(
            provider=provider,
            channel_account_id=channel_account_id,
            workspace_id=workspace_id,
            payload=payload,
            status=WebhookEventStatus.received,
        )
        session.add(we)
        await session.commit()
        await session.refresh(we)
        return we.id


async def update_event_status(
    we_id: uuid.UUID,
    status: WebhookEventStatus,
    error: str | None = None,
) -> None:
    """Update a webhook event's status in its own transaction."""
    async with AsyncSessionLocal() as session:
        we = await session.get(WebhookEvent, we_id)
        if we is None:
            return
        we.status = status
        if error is not None:
            we.error_message = error
        if status == WebhookEventStatus.processed:
            we.processed_at = datetime.now(timezone.utc)
        await session.commit()
