"""
WhatsApp Meta Cloud API webhook handler.

GET  /webhooks/whatsapp/meta  — Hub challenge verification
POST /webhooks/whatsapp/meta  — Inbound events (messages, status updates)

Security pipeline (Tier 1 + Tier 2):
1. Rate limit (per ip + provider)
2. Parse JSON
3. Resolve channel account by phone_number_id
4. IP allowlist (if any configured for the workspace)
5. Circuit breaker check
6. HMAC verification — accepts current OR previous secret during rotation
7. Stale timestamp (payload)
8. Replay protection (Redis)
9. Durable persistence in webhook_events
10. Normalize + persist + record_attempt
11. Update circuit + return
"""
import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.channels.whatsapp.meta_cloud import MetaCloudAdapter
from app.core.database import get_db
from app.core.rate_limit import webhook_rate_limit
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
from app.services.webhook_ops_service import (
    check_ip_allowed,
    is_circuit_open,
    record_attempt,
    record_circuit_failure,
    record_circuit_success,
    verify_hmac_with_rotation,
)
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


async def _get_credential(db: AsyncSession, channel_account_id) -> ChannelCredential | None:
    result = await db.execute(
        select(ChannelCredential).where(
            ChannelCredential.channel_account_id == channel_account_id,
            ChannelCredential.credential_type == "meta_cloud",
        )
    )
    return result.scalar_one_or_none()


def _extract_payload_timestamp(body: dict) -> int | None:
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
        phone_number_id = body["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"]
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

    # 3. IP allowlist (Tier 2)
    if not await check_ip_allowed(db, account.workspace_id, "meta_cloud", ip):
        await log_security_event(
            action="webhook_ip_blocked",
            workspace_id=account.workspace_id,
            target_type="channel_account",
            target_id=account.id,
            new_value={"provider": "meta_cloud"},
            ip_address=ip,
            user_agent=ua,
        )
        raise HTTPException(status_code=403, detail="IP not allowed")

    # 4. Circuit breaker (Tier 2)
    if await is_circuit_open(db, account.workspace_id, account.id):
        await log_security_event(
            action="webhook_circuit_open_rejected",
            workspace_id=account.workspace_id,
            target_type="channel_account",
            target_id=account.id,
            new_value={"provider": "meta_cloud"},
            ip_address=ip,
            user_agent=ua,
        )
        raise HTTPException(status_code=503, detail="Channel temporarily unavailable")

    # 5. HMAC verification — supports rotation
    credential = await _get_credential(db, account.id)
    if not credential:
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

    ok, used_secret = verify_hmac_with_rotation(credential, "app_secret", raw_body, sig_header)
    if not ok:
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
    if used_secret == "previous":
        await log_security_event(
            action="webhook_signed_with_previous_secret",
            workspace_id=account.workspace_id,
            target_type="channel_account",
            target_id=account.id,
            new_value={"provider": "meta_cloud"},
            ip_address=ip,
            user_agent=ua,
        )

    # 6. Timestamp anti-replay
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

    # 7. Signature replay
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
    await register_webhook_signature(redis, "meta_cloud", sig_header)

    # 8. Durable persistence
    event_id = await record_webhook_event(
        provider="meta_cloud",
        headers=headers,
        payload=body,
        workspace_id=account.workspace_id,
        channel_account_id=account.id,
        signature=sig_header,
    )

    # 9. Normalize + persist + attempt log
    adapter = MetaCloudAdapter(access_token="", phone_number_id=phone_number_id, app_secret="")
    started = time.perf_counter()
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
        latency = int((time.perf_counter() - started) * 1000)
        logger.exception("Meta webhook processing failed")
        from app.services.webhook_retry import schedule_retry

        await mark_event_status(event_id, WebhookEventStatus.failed, str(exc))
        await schedule_retry(event_id, str(exc))
        await record_attempt(
            webhook_event_id=event_id,
            attempt=1,
            payload=body,
            status="failed",
            error_message=str(exc),
            latency_ms=latency,
        )
        await record_circuit_failure(account.workspace_id, account.id, str(exc))
        return {"status": "deferred"}

    latency = int((time.perf_counter() - started) * 1000)
    await mark_event_status(event_id, WebhookEventStatus.processed)
    await record_attempt(
        webhook_event_id=event_id,
        attempt=1,
        payload=body,
        status="success",
        error_message=None,
        latency_ms=latency,
    )
    await record_circuit_success(account.workspace_id, account.id)
    return {"status": "ok"}
