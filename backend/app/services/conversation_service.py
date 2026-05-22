from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import ConversationSnooze, MentionInbox
from app.models.contact import Contact, ContactPhone
from app.models.conversation import Conversation, ConversationEvent, ConversationLabel, Message
from app.models.enums import ConvEventType, ConversationStatus
from app.schemas.conversation import ConversationListFilters, ConversationTransfer, ConversationUpdate


async def get_conversation_or_404(
    db: AsyncSession, workspace_id: UUID, conversation_id: UUID
) -> Conversation:
    conv = await db.get(Conversation, conversation_id)
    if not conv or conv.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv


async def list_conversations(
    db: AsyncSession,
    workspace_id: UUID,
    filters: ConversationListFilters,
    current_user=None,
) -> tuple[list[Conversation], int]:
    q = select(Conversation).where(Conversation.workspace_id == workspace_id)
    if filters.status:
        q = q.where(Conversation.status == filters.status)
    if filters.assignee_id:
        q = q.where(Conversation.assignee_id == filters.assignee_id)
    if filters.sector_id:
        q = q.where(Conversation.sector_id == filters.sector_id)
    if filters.channel_account_id:
        q = q.where(Conversation.channel_account_id == filters.channel_account_id)
    if filters.priority:
        q = q.where(Conversation.priority == filters.priority)
    if filters.is_private is not None:
        q = q.where(Conversation.is_private.is_(filters.is_private))
    if filters.label_id:
        q = q.where(
            Conversation.id.in_(
                select(ConversationLabel.conversation_id).where(
                    ConversationLabel.workspace_id == workspace_id,
                    ConversationLabel.label_id == filters.label_id,
                )
            )
        )
    if filters.snoozed is True:
        q = q.where(
            Conversation.id.in_(
                select(ConversationSnooze.conversation_id).where(
                    ConversationSnooze.workspace_id == workspace_id,
                    ConversationSnooze.until > datetime.now(timezone.utc),
                )
            )
        )
    elif filters.snoozed is False:
        q = q.where(
            ~Conversation.id.in_(
                select(ConversationSnooze.conversation_id).where(
                    ConversationSnooze.workspace_id == workspace_id,
                    ConversationSnooze.until > datetime.now(timezone.utc),
                )
            )
        )
    if filters.mentions_for_user_id:
        q = q.where(
            Conversation.id.in_(
                select(MentionInbox.conversation_id).where(
                    MentionInbox.workspace_id == workspace_id,
                    MentionInbox.user_id == filters.mentions_for_user_id,
                    MentionInbox.read_at.is_(None),
                )
            )
        )
    if filters.search:
        like = f"%{filters.search}%"
        q = q.where(
            Conversation.id.in_(
                select(Contact.id)
                .where(Contact.workspace_id == workspace_id)
                .where(or_(Contact.name.ilike(like), Contact.document.ilike(like) if False else Contact.name.ilike(like)))
            )
            | Conversation.id.in_(
                select(ContactPhone.contact_id).where(
                    ContactPhone.workspace_id == workspace_id,
                    ContactPhone.phone.ilike(like),
                )
            )
            | Conversation.id.in_(
                select(Message.conversation_id).where(
                    Message.workspace_id == workspace_id,
                    Message.content.ilike(like),
                )
            )
        )

    # Hide private conversations unless assignee/participant
    if current_user is not None:
        from app.models.conversation import ConversationParticipant

        q = q.where(
            (Conversation.is_private.is_(False))
            | (Conversation.assignee_id == current_user.id)
            | Conversation.id.in_(
                select(ConversationParticipant.conversation_id).where(
                    ConversationParticipant.workspace_id == workspace_id,
                    ConversationParticipant.user_id == current_user.id,
                )
            )
        )

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()

    offset = (filters.page - 1) * filters.page_size
    q = q.order_by(Conversation.updated_at.desc()).offset(offset).limit(filters.page_size)
    result = await db.execute(q)
    return result.scalars().all(), total


async def update_conversation(
    db: AsyncSession,
    workspace_id: UUID,
    conversation_id: UUID,
    body: ConversationUpdate,
    actor_id: UUID,
) -> Conversation:
    conv = await get_conversation_or_404(db, workspace_id, conversation_id)

    if "assignee_id" in body.model_fields_set:
        old_assignee = conv.assignee_id
        conv.assignee_id = body.assignee_id
        event_type = ConvEventType.assigned if body.assignee_id else ConvEventType.unassigned
        db.add(ConversationEvent(
            workspace_id=workspace_id,
            conversation_id=conv.id,
            type=event_type,
            actor_id=actor_id,
            actor_type="agent",
            payload={"from": str(old_assignee), "to": str(body.assignee_id)},
        ))

    if "sector_id" in body.model_fields_set:
        conv.sector_id = body.sector_id

    if "is_private" in body.model_fields_set and body.is_private is not None:
        conv.is_private = body.is_private

    if "service_reason_id" in body.model_fields_set:
        conv.service_reason_id = body.service_reason_id

    if "resolve_note" in body.model_fields_set:
        conv.resolve_note = body.resolve_note

    if "status" in body.model_fields_set and body.status is not None:
        conv.status = body.status
        if body.status == ConversationStatus.resolved:
            conv.resolved_at = datetime.now(timezone.utc)
            db.add(ConversationEvent(
                workspace_id=workspace_id,
                conversation_id=conv.id,
                type=ConvEventType.resolved,
                actor_id=actor_id,
                actor_type="agent",
                payload={
                    "service_reason_id": str(body.service_reason_id) if body.service_reason_id else None,
                    "note": body.resolve_note,
                },
            ))
        elif body.status in (ConversationStatus.open, ConversationStatus.in_progress) and conv.resolved_at:
            conv.resolved_at = None
            db.add(ConversationEvent(
                workspace_id=workspace_id,
                conversation_id=conv.id,
                type=ConvEventType.reopened,
                actor_id=actor_id,
                actor_type="agent",
                payload={"note": body.resolve_note},
            ))

    if "priority" in body.model_fields_set and body.priority is not None:
        conv.priority = body.priority

    await db.flush()
    await db.refresh(conv)
    return conv


async def transfer_conversation(
    db: AsyncSession,
    workspace_id: UUID,
    conversation_id: UUID,
    body: ConversationTransfer,
    actor_id: UUID,
) -> Conversation:
    conv = await get_conversation_or_404(db, workspace_id, conversation_id)
    old_assignee = conv.assignee_id
    old_sector = conv.sector_id

    if "assignee_id" in body.model_fields_set:
        conv.assignee_id = body.assignee_id
    if "sector_id" in body.model_fields_set:
        conv.sector_id = body.sector_id

    db.add(ConversationEvent(
        workspace_id=workspace_id,
        conversation_id=conv.id,
        type=ConvEventType.transferred,
        actor_id=actor_id,
        actor_type="agent",
        payload={
            "from_agent": str(old_assignee) if old_assignee else None,
            "to_agent": str(body.assignee_id) if body.assignee_id else None,
            "from_sector": str(old_sector) if old_sector else None,
            "to_sector": str(body.sector_id) if body.sector_id else None,
            "note": body.note,
            "transfer_reason_id": str(body.transfer_reason_id) if body.transfer_reason_id else None,
        },
    ))
    await db.flush()
    await db.refresh(conv)
    return conv
