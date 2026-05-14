from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
        return await db.get(Contact, cp.contact_id)

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
    """Returns (conversation, created). Reuses open/pending conv for same contact+channel."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.workspace_id == workspace_id,
            Conversation.channel_account_id == channel_account.id,
            Conversation.contact_id == contact.id,
            Conversation.status.in_([ConversationStatus.open, ConversationStatus.in_progress]),
        )
    )
    conv = result.scalar_one_or_none()
    if conv:
        return conv, False

    conv = Conversation(
        workspace_id=workspace_id,
        channel_account_id=channel_account.id,
        contact_id=contact.id,
        sector_id=channel_account.sector_id,
    )
    db.add(conv)
    await db.flush()

    db.add(ConversationEvent(
        workspace_id=workspace_id,
        conversation_id=conv.id,
        type=ConvEventType.opened,
        actor_type="system",
        payload={},
    ))
    await db.flush()
    return conv, True


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

    # Increment unread count
    conversation.unread_agent_count += 1
    await db.flush()
    return msg


async def send_agent_message(
    db: AsyncSession,
    workspace_id: UUID,
    conversation: Conversation,
    agent_id: UUID,
    body: SendMessageRequest,
) -> Message:
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

    # Mark first reply time if not set
    if not conversation.first_replied_at and not body.is_note:
        conversation.first_replied_at = datetime.now(timezone.utc)

    await db.flush()
    return msg
