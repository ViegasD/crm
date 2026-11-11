"""
Webhook replay tasks.

replay_stale_webhook_events  — scheduled every 5 min by Celery Beat.
    Finds webhook_events with status=received and created_at within the last
    hour, then dispatches process_webhook_event for each.

process_webhook_event  — processes a single stored webhook event.
    Loads the raw payload, instantiates the correct adapter (skip sig check
    since the event was already verified on first receipt), and calls
    persist_normalized_event for each parsed NormalizedEvent.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.enums import WebhookEventStatus, WhatsAppProvider
from app.models.webhook import WebhookEvent
from app.services.message_service import persist_normalized_event
from app.services.webhook_service import update_event_status
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Scheduler task
# ---------------------------------------------------------------------------

@celery_app.task(name="app.workers.tasks.webhook.replay_stale_webhook_events")
def replay_stale_webhook_events() -> None:
    """Find received events < 1 h old and dispatch individual replay tasks."""
    asyncio.run(_find_and_dispatch())


async def _find_and_dispatch() -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(WebhookEvent.id).where(
                WebhookEvent.status == WebhookEventStatus.received,
                WebhookEvent.created_at > cutoff,
            )
        )
        ids = result.scalars().all()

    logger.info("replay_stale_webhook_events: found %d stale event(s)", len(ids))
    for we_id in ids:
        process_webhook_event.delay(str(we_id))


# ---------------------------------------------------------------------------
# Per-event replay task
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="app.workers.tasks.webhook.process_webhook_event",
)
def process_webhook_event(self, we_id_str: str) -> None:
    """Re-process a single webhook event by its UUID."""
    try:
        asyncio.run(_process_one(UUID(we_id_str)))
    except Exception as exc:
        logger.error("process_webhook_event failed we_id=%s: %s", we_id_str, exc)
        raise self.retry(exc=exc)


async def _process_one(we_id: UUID) -> None:
    async with AsyncSessionLocal() as session:
        we = await session.get(WebhookEvent, we_id)
        if we is None or we.status != WebhookEventStatus.received:
            return

        # Claim the event — prevent concurrent replays
        we.status = WebhookEventStatus.processing
        await session.commit()

    try:
        await _run_event(we_id)
        await update_event_status(we_id, WebhookEventStatus.processed)
    except Exception as exc:
        logger.exception("Replay failed for webhook event %s", we_id)
        await update_event_status(we_id, WebhookEventStatus.failed, str(exc))
        raise


async def _run_event(we_id: UUID) -> None:
    """Load event + account, instantiate adapter, parse and handle each NormalizedEvent."""
    from app.models.channel import ChannelAccount, ChannelCredential
    from app.core.encryption import decrypt_payload

    async with AsyncSessionLocal() as session:
        we = await session.get(WebhookEvent, we_id)
        if we is None:
            return

        if we.channel_account_id is None:
            logger.warning("Webhook event %s has no channel_account_id — skipping replay", we_id)
            return

        account = await session.get(ChannelAccount, we.channel_account_id)
        if account is None:
            logger.warning("ChannelAccount %s not found for webhook event %s", we.channel_account_id, we_id)
            return

        # Load credentials
        from sqlalchemy import select as sa_select
        cred_result = await session.execute(
            sa_select(ChannelCredential).where(
                ChannelCredential.channel_account_id == account.id,
            )
        )
        creds_row = cred_result.scalar_one_or_none()
        creds: dict = decrypt_payload(creds_row.encrypted_payload) if creds_row else {}

        provider = we.provider
        raw_payload = we.raw_payload

    # Instantiate adapter based on provider (outside session — no DB calls needed)
    if provider in (WhatsAppProvider.evolution_baileys.value, WhatsAppProvider.evolution_cloud.value):
        from app.channels.whatsapp.evolution import EvolutionAdapter
        mode = "cloud" if provider == WhatsAppProvider.evolution_cloud.value else "baileys"
        adapter = EvolutionAdapter(
            instance_name=account.external_account_id,
            api_key=creds.get("evolution_api_key"),
            base_url=creds.get("evolution_base_url"),
            webhook_secret=None,  # skip sig on replay
            mode=mode,
        )
    elif provider == WhatsAppProvider.meta_cloud.value:
        from app.channels.whatsapp.meta_cloud import MetaCloudAdapter
        adapter = MetaCloudAdapter(
            access_token="",  # not needed for parsing
            phone_number_id=account.phone_number_id or "",
            app_secret="",  # skip sig on replay
        )
    else:
        logger.error("Unknown provider '%s' for webhook event %s — cannot replay", provider, we_id)
        return

    # Parse and process each normalized event in its own session
    events = adapter.parse_webhook({}, raw_payload)
    for event in events:
        event.workspace_id = str(account.workspace_id)
        event.channel_account_id = str(account.id)
        async with AsyncSessionLocal() as session:
            await persist_normalized_event(session, account, event)
            await session.commit()
