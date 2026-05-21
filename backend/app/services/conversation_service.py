from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, ConversationEvent, ConversationLabel
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
    db: AsyncSession, workspace_id: UUID, filters: ConversationListFilters
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
    if filters.label_id:
        q = q.where(
            Conversation.id.in_(
                select(ConversationLabel.conversation_id).where(
                    ConversationLabel.workspace_id == workspace_id,
                    ConversationLabel.label_id == filters.label_id,
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
                payload={},
            ))
        elif body.status in (ConversationStatus.open, ConversationStatus.in_progress) and conv.resolved_at:
            conv.resolved_at = None
            db.add(ConversationEvent(
                workspace_id=workspace_id,
                conversation_id=conv.id,
                type=ConvEventType.reopened,
                actor_id=actor_id,
                actor_type="agent",
                payload={},
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
        },
    ))
    await db.flush()
    await db.refresh(conv)
    return conv
