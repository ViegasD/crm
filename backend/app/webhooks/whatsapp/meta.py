"""
WhatsApp Meta Cloud API webhook handler.

GET  /webhooks/whatsapp/meta  — Hub challenge verification
POST /webhooks/whatsapp/meta  — Inbound events (messages, status updates)

Security pipeline:
1. Parse JSON (400 on malformed)
2. Resolve channel account by phone_number_id
3. Verify HMAC-SHA256 X-Hub-Signature-256 (401 on missing/invalid)
4. Reject stale payload timestamp (>5min, 409)
5. Reject replayed signature via Redis (409)
6. Persist payload in webhook_events (durable)
7. Normalize and persist messages
8. Mark webhook_events status
9. Return 200
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.channels.whatsapp.meta_cloud import MetaCloudAdapter
from app.core.database import get_db
from app.core.encryption import decrypt_payload
from app.core.rate_limit import webhook_rate_limit
from app.core.redis import get_redis
from app.core.request_meta import client_ip, user_agent
from app.core.security import (
    is_webhook_signature_registered,
    register_webhook_signature,
    verify_hmac_sha256,
    verify_webhook_timestamp,
)
from app.models.channel import ChannelAccount, ChannelCredential
from app.models.enums import WebhookEventStatus, WhatsAppProvider
from app.services.message_service import persist_normalized_event
from app.services.security_audit_service import log_security_event
from app.services.webhook_event_service import mark_event_status, record_webhook_event
from app.websocket.manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks/whatsapp/meta", tags=["webhooks"])


async def _resolve_account(db: AsyncSession, phone_number_id: str) -> ChannelAccount | None:
    result = await db.execute(
        select(ChannelAccount).where(
            ChannelAccount.phone_number_id == phone_number_id,
            ChannelAccount.provider == WhatsAppProvider.meta_cloud,
        )
    )
    return result.scalar_one_or_none()


async def _get_app_secret(db: AsyncSession, channel_account_id) -> str | None:
    result = await db.execute(
        select(ChannelCredential).where(
            ChannelCredential.channel_account_id == channel_account_id,
            ChannelCredential.credential_type == "meta_cloud",
        )
    )
    cred = result.scalar_one_or_none()
    if not cred:
        return None
    return decrypt_payload(cred.encrypted_payload).get("app_secret")


def _extract_payload_timestamp(body: dict) -> int | None:
    """Meta payloads carry timestamps inside entry[].changes[].value.{messages,statuses}[]."""
    try:
        value = body["entry"][0]["changes"][0]["value"]
    except (KeyError, IndexError, TypeError):
        return None
    for key in ("messages", "statuses"):
        items = value.get(key) or []
        if items:
            ts = items[0].get("timestamp")
            if ts is not None:
                try:
                    return int(ts)
                except (TypeError, ValueError):
                    return None
    return None


@router.get("")
async def verify_hub(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
):
    """Facebook Hub challenge-response for webhook subscription."""
    from app.core.config import settings
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_webhook_verify_token:
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("", dependencies=[Depends(webhook_rate_limit("meta", limit=300, window_seconds=60))])
async def receive_event(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    raw_body = await request.body()
    ip = client_ip(request)
    ua = user_agent(request)
    headers = dict(request.headers)
    sig_header = request.headers.get("x-hub-signature-256", "")

    # 1. Parse JSON
    try:
        body = await request.json()
    except ValueError:
        await log_security_event(
            action="webhook_malformed",
            target_type="whatsapp_meta_webhook",
            new_value={"reason": "invalid_json"},
            ip_address=ip,
            user_agent=ua,
        )
        raise HTTPException(status_code=400, detail="Malformed payload")

    # 2. Resolve channel
    try:
        phone_number_id = (
            body["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"]
        )
    except (KeyError, IndexError, TypeError):
        await log_security_event(
            action="webhook_malformed",
            target_type="whatsapp_meta_webhook",
            new_value={"reason": "missing_phone_number_id"},
            ip_address=ip,
            user_agent=ua,
        )
        raise HTTPException(status_code=400, detail="Malformed payload")

    account = await _resolve_account(db, phone_number_id)
    if not account:
        logger.warning("No channel account found for phone_number_id=%s", phone_number_id)
        await log_security_event(
            action="webhook_unknown_channel",
            target_type="whatsapp_meta_webhook",
            new_value={"phone_number_id": phone_number_id},
            ip_address=ip,
            user_agent=ua,
        )
        return {"status": "ignored"}

    # 3. Verify HMAC
    app_secret = await _get_app_secret(db, account.id)
    if not app_secret:
        await log_security_event(
            action="webhook_missing_secret",
            workspace_id=account.workspace_id,
            target_type="channel_account",
            target_id=account.id,
            new_value={"provider": "meta_cloud"},
            ip_address=ip,
            user_agent=ua,
        )
        raise HTTPException(status_code=401, detail="Webhook secret not configured")
    if not verify_hmac_sha256(app_secret, raw_body, sig_header):
        await log_security_event(
            action="webhook_invalid_signature",
            workspace_id=account.workspace_id,
            target_type="channel_account",
            target_id=account.id,
            new_value={"provider": "meta_cloud"},
            ip_address=ip,
            user_agent=ua,
        )
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 4. Timestamp anti-replay (when the payload contains one)
    payload_ts = _extract_payload_timestamp(body)
    if payload_ts is not None and not verify_webhook_timestamp(payload_ts):
        await log_security_event(
            action="webhook_stale_timestamp",
            workspace_id=account.workspace_id,
            target_type="channel_account",
            target_id=account.id,
            new_value={"provider": "meta_cloud", "timestamp": payload_ts},
            ip_address=ip,
            user_agent=ua,
        )
        raise HTTPException(status_code=409, detail="Stale webhook timestamp")

    # 5. Signature replay window (Redis)
    redis = await get_redis()
    if await is_webhook_signature_registered(redis, "meta_cloud", sig_header):
        await log_security_event(
            action="webhook_replay_detected",
            workspace_id=account.workspace_id,
            target_type="channel_account",
            target_id=account.id,
            new_value={"provider": "meta_cloud"},
            ip_address=ip,
            user_agent=ua,
        )
        raise HTTPException(status_code=409, detail="Replay detected")

    # 6. Reserve signature BEFORE processing — prevents concurrent retries from racing
    await register_webhook_signature(redis, "meta_cloud", sig_header)

    # 7. Durable persistence (own transaction)
    event_id = await record_webhook_event(
        provider="meta_cloud",
        headers=headers,
        payload=body,
        workspace_id=account.workspace_id,
        channel_account_id=account.id,
        signature=sig_header,
    )

    # 8. Normalize + persist
    adapter = MetaCloudAdapter(
        access_token="",
        phone_number_id=phone_number_id,
        app_secret=app_secret or "",
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
                    {
                        "type": "message.new",
                        "conversation_id": str(msg.conversation_id),
                        "message_id": str(msg.id),
                    },
                )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Meta webhook processing failed")
        from app.services.webhook_retry import schedule_retry

        await mark_event_status(event_id, WebhookEventStatus.failed, str(exc))
        await schedule_retry(event_id, str(exc))
        # We still return 200 to the provider — the event is durably stored
        # and the worker will retry. Returning 5xx triggers their own retries
        # which would just duplicate work.
        return {"status": "deferred"}

    await mark_event_status(event_id, WebhookEventStatus.processed)
    return {"status": "ok"}
