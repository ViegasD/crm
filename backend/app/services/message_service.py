import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.channels.base import NormalizedEvent
from app.channels.whatsapp.factory import get_whatsapp_adapter
from app.models.channel import ChannelAccount
from app.models.contact import Contact, ContactPhone
from app.models.conversation import (
    Conversation,
    ConversationEvent,
    Message,
    MessageIdentity,
)
from app.models.enums import (
    ConvEventType,
    ConversationStatus,
    MessageOrigin,
    MessageType,
    SenderType,
)
from app.schemas.message import SendMessageRequest
from app.services.provider_media_service import (
    enqueue_inbound_media_downloads,
    normalize_inbound_attachments,
)


META_STATUS_MAP = {
    "accepted": "queued",
    "sent": "sent",
    "delivered": "delivered",
    "read": "read",
    "failed": "failed",
}


logger = logging.getLogger(__name__)


def _is_placeholder_contact_name(current_name: str | None, phone: str) -> bool:
    if not current_name:
        return True
    if current_name == phone:
        return True
    if phone.endswith("@g.us") and current_name == f"Group {phone.split('@')[0]}":
        return True
    return False


async def fetch_group_contact_names(
    db: AsyncSession,
    channel_account: ChannelAccount,
    phones: list[str],
) -> dict[str, str]:
    group_phones = [phone for phone in phones if phone.endswith("@g.us")]
    if not group_phones:
        return {}

    adapter = await get_whatsapp_adapter(db, channel_account)
    fetcher = getattr(adapter, "fetch_group_names", None)
    if not callable(fetcher):
        return {}

    try:
        return await fetcher(group_phones)
    except Exception:  # noqa: BLE001
        logger.exception(
            "Failed to resolve group names for channel_account=%s groups=%s",
            channel_account.id,
            ",".join(group_phones),
        )
        return {}


async def handle_inbound_normalized_event(
    db: AsyncSession,
    event: NormalizedEvent,
) -> Message | None:
    """Dispatcher: orchestrate contact/conversation lookup and message persistence
    for a NormalizedEvent. Returns None for non-message events."""
    if event.event_type != "message.received":
        return None

    workspace_id = UUID(event.workspace_id)
    channel_account = await db.get(ChannelAccount, UUID(event.channel_account_id))
    if channel_account is None:
        return None

    contact_name = event.contact_name
    if event.is_group and _is_placeholder_contact_name(contact_name, event.contact_phone):
        contact_name = (
            await fetch_group_contact_names(db, channel_account, [event.contact_phone])
        ).get(event.contact_phone, contact_name)

    contact = await get_or_create_contact_by_phone(
        db,
        workspace_id,
        event.contact_phone,
        name=contact_name,
    )
    conversation, _ = await get_or_create_conversation(db, workspace_id, channel_account, contact)

    try:
        msg_type = MessageType[event.message_type]
    except KeyError:
        msg_type = MessageType.text

    return await persist_inbound_message(
        db=db,
        workspace_id=workspace_id,
        conversation=conversation,
        contact=contact,
        channel_account=channel_account,
        provider=event.provider,
        external_message_id=event.external_message_id,
        text=event.text,
        message_type=msg_type,
        attachments=event.attachments,
        wamid=event.wamid,
    )


async def get_or_create_contact_by_phone(
    db: AsyncSession, workspace_id: UUID, phone: str, name: str | None = None
) -> Contact:
    # Find by phone in contact_phones
    result = await db.execute(
        select(ContactPhone)
        .where(ContactPhone.workspace_id == workspace_id, ContactPhone.phone == phone)
    )
    cp = result.scalar_one_or_none()
    if cp:
        contact = await db.get(Contact, cp.contact_id)
        if contact and name and _is_placeholder_contact_name(contact.name, phone):
            contact.name = name
            await db.flush()
        return contact

    # Create new contact
    contact = Contact(workspace_id=workspace_id, name=name or phone)
    db.add(contact)
    await db.flush()
    db.add(ContactPhone(contact_id=contact.id, workspace_id=workspace_id, phone=phone, is_primary=True))
    await db.flush()
    return contact


async def get_or_create_conversation(
    db: AsyncSession,
    workspace_id: UUID,
    channel_account: ChannelAccount,
    contact: Contact,
) -> tuple[Conversation, bool]:
    """Resolve which conversation an inbound message should belong to.

    Delegates to ``timeline_service.resolve_inbound_conversation`` which applies
    the workspace/sector ``ConversationPolicy``:

    - existing open conversation → reuse it
    - last resolved conversation within the reopen window (or always_reopen) → reopen + emit ``auto_reopened`` event
    - otherwise → brand-new conversation/protocol + emit ``new_protocol_created`` event

    Returns ``(conversation, created)`` for backward-compat with callers that
    only care about whether the row was just inserted.
    """
    from app.services.timeline_service import resolve_inbound_conversation

    resolution = await resolve_inbound_conversation(
        db,
        workspace_id=workspace_id,
        contact_id=contact.id,
        channel_account_id=channel_account.id,
        sector_id_hint=channel_account.sector_id,
    )
    # Sector inheritance: if a brand-new conversation was created and the
    # channel account has a default sector, attach it so SLA/routing still apply
    if resolution.action == "new" and resolution.conversation.sector_id is None:
        resolution.conversation.sector_id = channel_account.sector_id
        await db.flush()
    return resolution.conversation, resolution.action == "new"


def build_idempotency_key(provider: str, channel_account_id: UUID, external_message_id: str) -> str:
    return f"{provider}:{channel_account_id}:{external_message_id}"


async def is_duplicate_message(db: AsyncSession, idempotency_key: str) -> bool:
    result = await db.execute(
        select(MessageIdentity).where(MessageIdentity.idempotency_key == idempotency_key)
    )
    return result.scalar_one_or_none() is not None


async def persist_inbound_message(
    db: AsyncSession,
    workspace_id: UUID,
    conversation: Conversation,
    contact: Contact,
    channel_account: ChannelAccount,
    provider: str,
    external_message_id: str,
    text: str | None,
    message_type: MessageType = MessageType.text,
    attachments: list[dict] | None = None,
    message_metadata: dict | None = None,
    wamid: str | None = None,
) -> Message:
    idempotency_key = build_idempotency_key(provider, channel_account.id, external_message_id)

    if await is_duplicate_message(db, idempotency_key):
        # Already processed — return existing
        result = await db.execute(
            select(Message)
            .join(MessageIdentity, MessageIdentity.message_id == Message.id)
            .where(MessageIdentity.idempotency_key == idempotency_key)
        )
        return result.scalar_one()

    msg = Message(
        workspace_id=workspace_id,
        conversation_id=conversation.id,
        sender_type=SenderType.contact,
        sender_id=contact.id,
        origin=MessageOrigin.customer,
        content=text,
        type=message_type,
        attachments=attachments or [],
        metadata_=message_metadata or {},
    )
    db.add(msg)
    await db.flush()

    db.add(MessageIdentity(
        workspace_id=workspace_id,
        message_id=msg.id,
        channel_account_id=channel_account.id,
        provider=provider,
        external_message_id=external_message_id,
        wamid=wamid,
        idempotency_key=idempotency_key,
        direction="inbound",
    ))

    # Timeline marker
    from app.services.timeline_service import log_message_event

    await log_message_event(
        db,
        workspace_id=workspace_id,
        conversation_id=conversation.id,
        direction="inbound",
        message_id=msg.id,
        actor_type="contact",
    )

    # Increment unread count
    conversation.unread_agent_count += 1
    await db.flush()
    return msg


async def persist_normalized_event(
    db: AsyncSession,
    channel_account: ChannelAccount,
    event: NormalizedEvent,
) -> Message | None:
    if event.event_type == "message.status":
        return await _persist_message_status_event(db, channel_account, event)

    if event.event_type != "message.received" or event.direction != "inbound":
        return None

    try:
        message_type = MessageType(event.message_type)
    except ValueError:
        message_type = MessageType.text

    contact_name = event.contact_name
    if event.is_group and _is_placeholder_contact_name(contact_name, event.contact_phone):
        try:
            resolved = await asyncio.wait_for(
                fetch_group_contact_names(db, channel_account, [event.contact_phone]),
                timeout=3.0,
            )
            contact_name = resolved.get(event.contact_phone, contact_name)
        except asyncio.TimeoutError:
            pass

    contact = await get_or_create_contact_by_phone(
        db,
        channel_account.workspace_id,
        event.contact_phone,
        name=contact_name,
    )
    conversation, _ = await get_or_create_conversation(
        db,
        channel_account.workspace_id,
        channel_account,
        contact,
    )
    idempotency_key = build_idempotency_key(event.provider, channel_account.id, event.external_message_id)
    is_duplicate = await is_duplicate_message(db, idempotency_key)
    normalized_attachments = normalize_inbound_attachments(
        event.provider,
        event.message_type,
        event.attachments,
    )
    inbound_metadata = {}
    if event.sender_name:
        inbound_metadata["sender_name"] = event.sender_name
    if event.is_group:
        inbound_metadata["is_group"] = True
        inbound_metadata["group_jid"] = event.contact_phone
    msg = await persist_inbound_message(
        db=db,
        workspace_id=channel_account.workspace_id,
        conversation=conversation,
        contact=contact,
        channel_account=channel_account,
        provider=event.provider,
        external_message_id=event.external_message_id,
        text=event.text,
        message_type=message_type,
        attachments=normalized_attachments,
        message_metadata=inbound_metadata,
        wamid=event.wamid,
    )
    if not is_duplicate:
        await enqueue_inbound_media_downloads(db, channel_account, msg)
        # Auto-wake snooze when the customer sends a new inbound message
        from sqlalchemy import delete as sa_delete

        from app.models.catalog import ConversationSnooze

        await db.execute(
            sa_delete(ConversationSnooze).where(
                ConversationSnooze.conversation_id == conversation.id
            )
        )

        if channel_account.auto_assignment and not conversation.assignee_id:
            from app.services.sla_service import assign_conversation_if_needed

            await assign_conversation_if_needed(db, conversation, method="inbound_auto")

        try:
            from app.services.external_webhooks import emit_event

            await emit_event(
                channel_account.workspace_id,
                "message.received",
                {
                    "conversation_id": str(conversation.id),
                    "message_id": str(msg.id),
                    "channel_account_id": str(channel_account.id),
                    "contact_id": str(contact.id),
                    "provider": event.provider,
                    "message_type": event.message_type,
                },
            )
        except Exception:  # noqa: BLE001
            pass

        try:
            from app.services.flow_executor import run_message_received_flows
        except ModuleNotFoundError:
            logger.warning("Inbound flow hook unavailable; skipping message-triggered flows")
        else:
            await run_message_received_flows(db, conversation, msg)
    return msg


async def send_agent_message(
    db: AsyncSession,
    workspace_id: UUID,
    conversation: Conversation,
    agent_id: UUID,
    body: SendMessageRequest,
) -> Message:
    from app.services.media_access import bind_attachments

    attachments = await bind_attachments(db, workspace_id, conversation.id, agent_id, body.attachments)
    # Ignore all caller-provided URLs and metadata; only stored upload records
    # can authorize outbound file access or populate the persisted attachment.
    body = body.model_copy(update={"attachments": attachments})
    if body.is_note:
        origin = MessageOrigin.crm_agent
        msg_type = MessageType.internal_note
        sender_type = SenderType.agent
    else:
        origin = MessageOrigin.crm_agent
        msg_type = body.type
        sender_type = SenderType.agent

    msg = Message(
        workspace_id=workspace_id,
        conversation_id=conversation.id,
        sender_type=sender_type,
        sender_id=agent_id,
        origin=origin,
        content=body.content,
        type=msg_type,
        attachments=body.attachments,
    )
    db.add(msg)

    if not body.is_note:
        channel_account = await db.get(ChannelAccount, conversation.channel_account_id)
        if channel_account is None:
            raise HTTPException(status_code=400, detail="Channel account not found")

        to_phone = await _get_contact_phone(db, workspace_id, conversation.contact_id)
        if not to_phone:
            raise HTTPException(status_code=400, detail="Contact phone not found")

        adapter = await get_whatsapp_adapter(db, channel_account)
        sent_message = await _send_outbound_whatsapp_message(adapter, to_phone, body)

        msg.metadata_ = {
            **(msg.metadata_ or {}),
            "delivery_status": "queued",
            "delivery_status_updated_at": datetime.now(timezone.utc).isoformat(),
            "provider": channel_account.provider.value if channel_account.provider else None,
        }

        await db.flush()
        db.add(MessageIdentity(
            workspace_id=workspace_id,
            message_id=msg.id,
            channel_account_id=channel_account.id,
            provider=channel_account.provider,
            external_message_id=sent_message.external_message_id,
            wamid=sent_message.wamid,
            idempotency_key=build_idempotency_key(
                channel_account.provider.value if channel_account.provider else "unknown",
                channel_account.id,
                sent_message.external_message_id,
            ),
            direction="outbound",
        ))

    # Mark first reply time if not set
    if not conversation.first_replied_at and not body.is_note:
        conversation.first_replied_at = datetime.now(timezone.utc)

    try:
        from app.services.presence_idle import mark_agent_active

        await mark_agent_active(workspace_id, agent_id)
    except Exception:  # noqa: BLE001
        pass

    await db.flush()
    # Timeline marker for outbound (skip pure internal notes — they have their own event below)
    if not body.is_note:
        from app.services.timeline_service import log_message_event

        await log_message_event(
            db,
            workspace_id=workspace_id,
            conversation_id=conversation.id,
            direction="outbound",
            message_id=msg.id,
            actor_id=agent_id,
            actor_type="agent",
        )
    if body.is_note:
        db.add(ConversationEvent(
            workspace_id=workspace_id,
            conversation_id=conversation.id,
            type=ConvEventType.note_added,
            actor_id=agent_id,
            actor_type="agent",
            payload={"message_id": str(msg.id)},
        ))

        from app.models.catalog import MentionInbox
        from app.services.mention_service import resolve_mentions
        from app.websocket.manager import manager

        mentioned = await resolve_mentions(db, workspace_id, body.content)
        snippet = (body.content or "")[:240]
        for user in mentioned:
            if user.id == agent_id:
                continue
            db.add(ConversationEvent(
                workspace_id=workspace_id,
                conversation_id=conversation.id,
                type=ConvEventType.mention,
                actor_id=agent_id,
                actor_type="agent",
                payload={
                    "message_id": str(msg.id),
                    "mentioned_user_id": str(user.id),
                    "mentioned_user_name": user.name,
                },
            ))
            db.add(MentionInbox(
                workspace_id=workspace_id,
                user_id=user.id,
                conversation_id=conversation.id,
                message_id=msg.id,
                mentioned_by=agent_id,
                snippet=snippet,
            ))
            await manager.broadcast(
                str(workspace_id),
                {
                    "type": "mention",
                    "conversation_id": str(conversation.id),
                    "message_id": str(msg.id),
                    "mentioned_user_id": str(user.id),
                    "snippet": snippet,
                },
            )
        await db.flush()
    return msg


async def _get_contact_phone(db: AsyncSession, workspace_id: UUID, contact_id: UUID) -> str | None:
    result = await db.execute(
        select(ContactPhone)
        .where(ContactPhone.workspace_id == workspace_id, ContactPhone.contact_id == contact_id)
        .order_by(ContactPhone.is_primary.desc(), ContactPhone.created_at.asc())
        .limit(1)
    )
    phone = result.scalar_one_or_none()
    return phone.phone if phone else None


async def _send_outbound_whatsapp_message(adapter, to_phone: str, body: SendMessageRequest):
    if body.attachments:
        if len(body.attachments) != 1:
            raise HTTPException(status_code=400, detail="Only one attachment per outbound message is supported")

        attachment = body.attachments[0]
        from app.core.config import settings
        from app.core.minio import generate_presigned_url
        # Provider fetches cannot use a browser/user capability. This URL is
        # generated from canonical metadata after bind_attachments, never input.
        media_url = generate_presigned_url(settings.minio_bucket, attachment["key"], expires=300)

        media_type = str(body.type)
        if media_type not in {"image", "audio", "video", "file"}:
            mime_type = str(attachment.get("mimeType") or "")
            if mime_type.startswith("image/"):
                media_type = "image"
            elif mime_type.startswith("audio/"):
                media_type = "audio"
            elif mime_type.startswith("video/"):
                media_type = "video"
            else:
                media_type = "file"

        return await adapter.send_media(
            to_phone,
            media_url,
            media_type,
            caption=body.content,
        )

    if not body.content:
        raise HTTPException(status_code=400, detail="Message content is required")

    return await adapter.send_text(to_phone, body.content)


async def _persist_message_status_event(
    db: AsyncSession,
    channel_account: ChannelAccount,
    event: NormalizedEvent,
) -> Message | None:
    candidate_ids = [candidate for candidate in {event.external_message_id, event.wamid} if candidate]
    if not candidate_ids:
        return None

    result = await db.execute(
        select(Message)
        .join(MessageIdentity, MessageIdentity.message_id == Message.id)
        .where(
            MessageIdentity.channel_account_id == channel_account.id,
            or_(
                MessageIdentity.external_message_id.in_(candidate_ids),
                MessageIdentity.wamid.in_(candidate_ids),
            ),
        )
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    message = result.scalar_one_or_none()
    if message is None:
        return None

    raw_status = str(event.raw.get("status") or "").strip().lower()
    normalized_status = META_STATUS_MAP.get(raw_status, raw_status or "queued")

    metadata = dict(message.metadata_ or {})
    metadata["delivery_status"] = normalized_status
    metadata["delivery_status_updated_at"] = event.timestamp
    metadata["provider"] = event.provider
    if raw_status:
        metadata["provider_status_raw"] = raw_status

    error_message = _extract_status_error_message(event.raw)
    if error_message:
        metadata["delivery_status_error"] = error_message
    elif normalized_status != "failed":
        metadata.pop("delivery_status_error", None)

    message.metadata_ = metadata
    await db.flush()
    return message


def _extract_status_error_message(raw_status_payload: dict) -> str | None:
    errors = raw_status_payload.get("errors")
    if not isinstance(errors, list) or not errors:
        return None

    first_error = errors[0] if isinstance(errors[0], dict) else None
    if not first_error:
        return None

    for field in ("message", "title", "details"):
        value = first_error.get(field)
        if value:
            return str(value)
    return None
