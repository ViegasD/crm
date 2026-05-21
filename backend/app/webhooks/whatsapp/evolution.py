"""
Evolution API v2 webhook handler.

POST /webhooks/whatsapp/evolution/{instance_name}

Security: HMAC-SHA256 via x-evolution-signature + replay protection +
durable persistence in webhook_events.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.channels.whatsapp.evolution import EvolutionAdapter
from app.core.database import get_db
from app.core.encryption import decrypt_payload
from app.core.redis import get_redis
from app.core.request_meta import client_ip, user_agent
from app.core.security import (
    is_webhook_signature_registered,
    register_webhook_signature,
    verify_webhook_timestamp,
)
from app.models.channel import ChannelAccount, ChannelCredential
from app.models.enums import WebhookEventStatus, WhatsAppProvider
from app.services.message_service import persist_normalized_event
from app.services.security_audit_service import log_security_event
from app.services.webhook_event_service import mark_event_status, record_webhook_event
from app.websocket.manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks/whatsapp/evolution", tags=["webhooks"])


async def _resolve_account(db: AsyncSession, instance_name: str) -> ChannelAccount | None:
    """Find channel account by Evolution instance name stored in external_account_id."""
    result = await db.execute(
        select(ChannelAccount).where(
            ChannelAccount.external_account_id == instance_name,
            ChannelAccount.provider.in_([
                WhatsAppProvider.evolution_baileys,
                WhatsAppProvider.evolution_cloud,
            ]),
        )
    )
    return result.scalar_one_or_none()


async def _get_evolution_creds(db: AsyncSession, channel_account_id) -> dict:
    result = await db.execute(
        select(ChannelCredential).where(
            ChannelCredential.channel_account_id == channel_account_id,
            ChannelCredential.credential_type == "evolution",
        )
    )
    cred = result.scalar_one_or_none()
    if not cred:
        return {}
    return decrypt_payload(cred.encrypted_payload)


@router.post("/{instance_name}")
async def receive_event(
    instance_name: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    raw_body = await request.body()
    ip = client_ip(request)
    ua = user_agent(request)
    headers = dict(request.headers)

    try:
        body = await request.json()
    except ValueError:
        await log_security_event(
            action="webhook_malformed",
            target_type="whatsapp_evolution_webhook",
            new_value={"reason": "invalid_json", "instance_name": instance_name},
            ip_address=ip,
            user_agent=ua,
        )
        raise HTTPException(status_code=400, detail="Malformed payload")

    account = await _resolve_account(db, instance_name)
    if not account:
        logger.warning("No channel account for Evolution instance=%s", instance_name)
        await log_security_event(
            action="webhook_unknown_channel",
            target_type="whatsapp_evolution_webhook",
            new_value={"instance_name": instance_name},
            ip_address=ip,
            user_agent=ua,
        )
        return {"status": "ignored"}

    mode = "cloud" if account.provider == WhatsAppProvider.evolution_cloud else "baileys"
    creds = await _get_evolution_creds(db, account.id)
    webhook_secret = creds.get("webhook_secret")
    signature = request.headers.get("x-evolution-signature", "")
    timestamp = request.headers.get("x-webhook-timestamp") or request.headers.get("x-evolution-timestamp")

    adapter = EvolutionAdapter(
        instance_name=instance_name,
        api_key=creds.get("evolution_api_key"),
        base_url=creds.get("evolution_base_url"),
        webhook_secret=webhook_secret,
        mode=mode,
    )

    if not adapter.verify_webhook_signature(headers, raw_body):
        await log_security_event(
            action="webhook_invalid_signature",
            workspace_id=account.workspace_id,
            target_type="channel_account",
            target_id=account.id,
            new_value={"provider": str(account.provider), "missing_secret": not bool(webhook_secret)},
            ip_address=ip,
            user_agent=ua,
        )
        raise HTTPException(status_code=401, detail="Invalid signature")
    if timestamp and not verify_webhook_timestamp(timestamp):
        await log_security_event(
            action="webhook_stale_timestamp",
            workspace_id=account.workspace_id,
            target_type="channel_account",
            target_id=account.id,
            new_value={"provider": str(account.provider), "timestamp": timestamp},
            ip_address=ip,
            user_agent=ua,
        )
        raise HTTPException(status_code=409, detail="Stale webhook timestamp")
    redis = await get_redis()
    if await is_webhook_signature_registered(redis, "evolution", signature):
        await log_security_event(
            action="webhook_replay_detected",
            workspace_id=account.workspace_id,
            target_type="channel_account",
            target_id=account.id,
            new_value={"provider": str(account.provider)},
            ip_address=ip,
            user_agent=ua,
        )
        raise HTTPException(status_code=409, detail="Replay detected")

    await register_webhook_signature(redis, "evolution", signature)
    event_id = await record_webhook_event(
        provider="evolution",
        headers=headers,
        payload=body,
        workspace_id=account.workspace_id,
        channel_account_id=account.id,
        signature=signature,
    )

    try:
        events = adapter.parse_webhook(headers, body)
        for event in events:
            event.workspace_id = str(account.workspace_id)
            event.channel_account_id = str(account.id)
            msg = await persist_normalized_event(db, account, event)
            if msg:
                await manager.broadcast(
                    str(account.workspace_id),
                    {"type": "message.new", "conversation_id": str(msg.conversation_id), "message_id": str(msg.id)},
                )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Evolution webhook processing failed")
        await mark_event_status(event_id, WebhookEventStatus.failed, str(exc))
        raise

    await mark_event_status(event_id, WebhookEventStatus.processed)
    return {"status": "ok"}
