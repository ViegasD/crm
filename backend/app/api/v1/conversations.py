from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import require_workspace_member
from app.core.request_meta import client_ip, user_agent
from app.models.contact import Contact, ContactPhone
from app.models.conversation import (
    Conversation,
    ConversationEvent,
    ConversationLabel,
    ConversationParticipant,
    Label,
    Message,
)
from app.models.enums import ConvEventType
from app.models.workspace import User
from app.schemas.conversation import (
    ConversationBulkLabel,
    ConversationBulkStatus,
    ConversationBulkTransfer,
    ConversationEventOut,
    ConversationListFilters,
    ConversationOut,
    ConversationParticipantAdd,
    ConversationParticipantOut,
    ConversationTransfer,
    ConversationUpdate,
    LabelInline,
    UserInline,
)
from app.services.conversation_service import (
    get_conversation_or_404,
    list_conversations,
    transfer_conversation,
    update_conversation,
)
from app.services.security_audit_service import log_security_event

router = APIRouter(prefix="/workspaces/{workspace_id}/conversations", tags=["conversations"])


async def _conversation_out(db: AsyncSession, conv: Conversation) -> ConversationOut:
    contact = await db.get(Contact, conv.contact_id)
    phone_result = await db.execute(
        select(ContactPhone)
        .where(ContactPhone.workspace_id == conv.workspace_id, ContactPhone.contact_id == conv.contact_id)
        .order_by(ContactPhone.is_primary.desc(), ContactPhone.created_at.asc())
        .limit(1)
    )
    phone = phone_result.scalar_one_or_none()
    message_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    last_message = message_result.scalar_one_or_none()

    assignee_name: str | None = None
    if conv.assignee_id:
        assignee = await db.get(User, conv.assignee_id)
        if assignee:
            assignee_name = assignee.name

    labels_q = await db.execute(
        select(Label)
        .join(ConversationLabel, ConversationLabel.label_id == Label.id)
        .where(ConversationLabel.conversation_id == conv.id)
        .order_by(Label.name.asc())
    )
    labels = [LabelInline.model_validate(label) for label in labels_q.scalars().all()]

    return ConversationOut.model_validate(conv).model_copy(
        update={
            "contact_name": contact.name if contact else None,
            "contact_phone": phone.phone if phone else None,
            "last_message": last_message.content if last_message else None,
            "last_message_at": last_message.created_at if last_message else None,
            "assignee_name": assignee_name,
            "labels": labels,
        }
    )


@router.get("", response_model=dict)
async def list_convs(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = Query(None),
    assignee_id: UUID | None = Query(None),
    sector_id: UUID | None = Query(None),
    channel_account_id: UUID | None = Query(None),
    label_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
):
    filters = ConversationListFilters(
        status=status,
        assignee_id=assignee_id,
        sector_id=sector_id,
        channel_account_id=channel_account_id,
        label_id=label_id,
        page=page,
        page_size=page_size,
    )
    items, total = await list_conversations(db, workspace_id, filters)
    return {
        "items": [await _conversation_out(db, item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{conversation_id}", response_model=ConversationOut)
async def get_conv(
    workspace_id: UUID,
    conversation_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    conv = await get_conversation_or_404(db, workspace_id, conversation_id)
    return await _conversation_out(db, conv)


@router.patch("/{conversation_id}", response_model=ConversationOut)
async def update_conv(
    workspace_id: UUID,
    conversation_id: UUID,
    body: ConversationUpdate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    conv = await update_conversation(db, workspace_id, conversation_id, body, current_user.id)
    await _broadcast_update(workspace_id, conv)
    return await _conversation_out(db, conv)


@router.post("/{conversation_id}/transfer", response_model=ConversationOut)
async def transfer_conv(
    workspace_id: UUID,
    conversation_id: UUID,
    body: ConversationTransfer,
    request: Request,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    conv = await transfer_conversation(db, workspace_id, conversation_id, body, current_user.id)
    await _broadcast_update(workspace_id, conv)
    await log_security_event(
        action="conversation_transferred",
        workspace_id=workspace_id,
        user_id=current_user.id,
        target_type="conversation",
        target_id=conv.id,
        new_value={
            "assignee_id": str(body.assignee_id) if body.assignee_id else None,
            "sector_id": str(body.sector_id) if body.sector_id else None,
            "note": body.note,
        },
        ip_address=client_ip(request),
        user_agent=user_agent(request),
    )
    return await _conversation_out(db, conv)


@router.get("/{conversation_id}/events", response_model=list[ConversationEventOut])
async def list_events(
    workspace_id: UUID,
    conversation_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await get_conversation_or_404(db, workspace_id, conversation_id)
    result = await db.execute(
        select(ConversationEvent, User)
        .outerjoin(User, User.id == ConversationEvent.actor_id)
        .where(
            ConversationEvent.workspace_id == workspace_id,
            ConversationEvent.conversation_id == conversation_id,
        )
        .order_by(ConversationEvent.created_at.asc())
    )
    output: list[ConversationEventOut] = []
    for event, actor in result.all():
        output.append(
            ConversationEventOut.model_validate(event).model_copy(
                update={"actor_name": actor.name if actor else None}
            )
        )
    return output


@router.get("/{conversation_id}/participants", response_model=list[ConversationParticipantOut])
async def list_participants(
    workspace_id: UUID,
    conversation_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await get_conversation_or_404(db, workspace_id, conversation_id)
    result = await db.execute(
        select(ConversationParticipant, User)
        .join(User, User.id == ConversationParticipant.user_id)
        .where(
            ConversationParticipant.workspace_id == workspace_id,
            ConversationParticipant.conversation_id == conversation_id,
        )
        .order_by(User.name.asc())
    )
    output: list[ConversationParticipantOut] = []
    for participant, user in result.all():
        output.append(
            ConversationParticipantOut.model_validate(participant).model_copy(
                update={"user": UserInline.model_validate(user)}
            )
        )
    return output


@router.post("/{conversation_id}/participants", response_model=ConversationParticipantOut)
async def add_participant(
    workspace_id: UUID,
    conversation_id: UUID,
    body: ConversationParticipantAdd,
    response: Response,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await get_conversation_or_404(db, workspace_id, conversation_id)
    result = await db.execute(
        select(ConversationParticipant).where(
            ConversationParticipant.workspace_id == workspace_id,
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == body.user_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        response.status_code = 200
        user = await db.get(User, existing.user_id)
        return ConversationParticipantOut.model_validate(existing).model_copy(
            update={"user": UserInline.model_validate(user) if user else None}
        )

    participant = ConversationParticipant(
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        user_id=body.user_id,
    )
    db.add(participant)
    await db.flush()
    db.add(
        ConversationEvent(
            workspace_id=workspace_id,
            conversation_id=conversation_id,
            type=ConvEventType.participant_added,
            actor_id=current_user.id,
            actor_type="agent",
            payload={"user_id": str(body.user_id)},
        )
    )
    await db.flush()
    response.status_code = 201
    user = await db.get(User, participant.user_id)
    return ConversationParticipantOut.model_validate(participant).model_copy(
        update={"user": UserInline.model_validate(user) if user else None}
    )


@router.delete("/{conversation_id}/participants/{user_id}", status_code=204)
async def remove_participant(
    workspace_id: UUID,
    conversation_id: UUID,
    user_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await get_conversation_or_404(db, workspace_id, conversation_id)
    result = await db.execute(
        select(ConversationParticipant).where(
            ConversationParticipant.workspace_id == workspace_id,
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user_id,
        )
    )
    participant = result.scalar_one_or_none()
    if participant:
        await db.delete(participant)
        db.add(
            ConversationEvent(
                workspace_id=workspace_id,
                conversation_id=conversation_id,
                type=ConvEventType.participant_removed,
                actor_id=current_user.id,
                actor_type="agent",
                payload={"user_id": str(user_id)},
            )
        )


# ── Bulk actions ─────────────────────────────────────────────────────────────

@router.post("/bulk/label", status_code=204)
async def bulk_label(
    workspace_id: UUID,
    body: ConversationBulkLabel,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    label = await db.get(Label, body.label_id)
    if not label or label.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Label not found")
    for conv_id in body.conversation_ids:
        conv = await db.get(Conversation, conv_id)
        if not conv or conv.workspace_id != workspace_id:
            continue
        existing = await db.execute(
            select(ConversationLabel).where(
                ConversationLabel.workspace_id == workspace_id,
                ConversationLabel.conversation_id == conv_id,
                ConversationLabel.label_id == body.label_id,
            )
        )
        if existing.scalar_one_or_none():
            continue
        db.add(
            ConversationLabel(
                workspace_id=workspace_id,
                conversation_id=conv_id,
                label_id=body.label_id,
                assigned_by=current_user.id,
            )
        )
        db.add(
            ConversationEvent(
                workspace_id=workspace_id,
                conversation_id=conv_id,
                type=ConvEventType.label_added,
                actor_id=current_user.id,
                actor_type="agent",
                payload={"label_id": str(body.label_id), "label_name": label.name},
            )
        )


@router.post("/bulk/transfer", status_code=204)
async def bulk_transfer(
    workspace_id: UUID,
    body: ConversationBulkTransfer,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if body.assignee_id is None and body.sector_id is None:
        raise HTTPException(status_code=400, detail="Either assignee_id or sector_id is required")
    transfer = ConversationTransfer(
        assignee_id=body.assignee_id, sector_id=body.sector_id, note=body.note
    )
    for conv_id in body.conversation_ids:
        try:
            await transfer_conversation(db, workspace_id, conv_id, transfer, current_user.id)
        except HTTPException:
            continue


@router.post("/bulk/status", status_code=204)
async def bulk_status(
    workspace_id: UUID,
    body: ConversationBulkStatus,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    update = ConversationUpdate(status=body.status)
    for conv_id in body.conversation_ids:
        try:
            await update_conversation(db, workspace_id, conv_id, update, current_user.id)
        except HTTPException:
            continue


async def _broadcast_update(workspace_id: UUID, conv) -> None:
    from app.websocket.manager import manager
    await manager.broadcast(
        str(workspace_id),
        {"type": "conversation.updated", "conversation_id": str(conv.id), "status": conv.status},
    )
