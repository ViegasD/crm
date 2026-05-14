"""
WhatsApp Meta Cloud API webhook handler.

GET  /webhooks/whatsapp/meta  — Hub challenge verification
POST /webhooks/whatsapp/meta  — Inbound events (messages, status updates)

Security: HMAC-SHA256 via X-Hub-Signature-256 header (app secret).
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.channels.whatsapp.meta_cloud import MetaCloudAdapter
from app.core.database import get_db
from app.core.encryption import decrypt_payload
from app.core.security import verify_hmac_sha256
from app.models.channel import ChannelAccount, ChannelCredential
from app.models.enums import WhatsAppProvider
from app.services.message_service import persist_inbound_message
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


@router.post("")
async def receive_event(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    raw_body = await request.body()
    body = await request.json()

    # Extract phone_number_id from first entry to find channel account
    try:
        phone_number_id = (
            body["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"]
        )
    except (KeyError, IndexError):
        raise HTTPException(status_code=400, detail="Malformed payload")

    account = await _resolve_account(db, phone_number_id)
    if not account:
        # Unknown channel — acknowledge and ignore
        logger.warning("No channel account found for phone_number_id=%s", phone_number_id)
        return {"status": "ignored"}

    # Verify HMAC
    app_secret = await _get_app_secret(db, account.id)
    if app_secret:
        sig_header = request.headers.get("x-hub-signature-256", "")
        sig = sig_header.removeprefix("sha256=")
        if not verify_hmac_sha256(app_secret, raw_body, sig):
            raise HTTPException(status_code=401, detail="Invalid signature")

    adapter = MetaCloudAdapter(
        access_token="",  # not needed for parse
        phone_number_id=phone_number_id,
        app_secret=app_secret or "",
    )
    events = adapter.parse_webhook(dict(request.headers), body)

    for event in events:
        event.workspace_id = str(account.workspace_id)
        event.channel_account_id = str(account.id)
        msg = await persist_inbound_message(db, event)
        if msg:
            await manager.broadcast(
                str(account.workspace_id),
                {"type": "message.new", "conversation_id": str(msg.conversation_id), "message_id": str(msg.id)},
            )

    return {"status": "ok"}
