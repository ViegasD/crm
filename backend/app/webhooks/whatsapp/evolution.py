"""
Evolution API v2 webhook handler.

POST /webhooks/whatsapp/evolution/{instance_name}

Security: Optional HMAC-SHA256 via x-evolution-signature, or no-secret dev mode.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.channels.whatsapp.evolution import EvolutionAdapter
from app.core.database import get_db
from app.core.encryption import decrypt_payload
from app.models.channel import ChannelAccount, ChannelCredential
from app.models.enums import WhatsAppProvider
from app.services.message_service import persist_inbound_message
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
    body = await request.json()

    account = await _resolve_account(db, instance_name)
    if not account:
        logger.warning("No channel account for Evolution instance=%s", instance_name)
        return {"status": "ignored"}

    mode = "cloud" if account.provider == WhatsAppProvider.evolution_cloud else "baileys"
    creds = await _get_evolution_creds(db, account.id)
    webhook_secret = creds.get("webhook_secret")

    adapter = EvolutionAdapter(
        instance_name=instance_name,
        api_key=creds.get("evolution_api_key"),
        base_url=creds.get("evolution_base_url"),
        webhook_secret=webhook_secret,
        mode=mode,
    )

    if not adapter.verify_webhook_signature(dict(request.headers), raw_body):
        raise HTTPException(status_code=401, detail="Invalid signature")

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
