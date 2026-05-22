"""Workspace catalog endpoints: transfer/service reasons, snooze, views, mentions."""
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from sqlalchemy import or_, select, update as sa_update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_workspace_member
from app.core.request_meta import client_ip, user_agent
from app.models.catalog import (
    ConversationSnooze,
    ConversationView,
    MentionInbox,
    ServiceReason,
    TransferReason,
)
from app.models.enums import ViewVisibility
from app.models.workspace import SectorMember, User
from app.schemas.catalog import (
    ConversationViewCreate,
    ConversationViewOut,
    ConversationViewUpdate,
    MentionMarkRead,
    MentionOut,
    ServiceReasonCreate,
    ServiceReasonOut,
    ServiceReasonUpdate,
    SnoozeOut,
    SnoozeRequest,
    TransferReasonCreate,
    TransferReasonOut,
    TransferReasonUpdate,
)
from app.services.conversation_service import get_conversation_or_404
from app.services.security_audit_service import log_security_event

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["catalog"])


# ── Transfer reasons ────────────────────────────────────────────────────────

@router.get("/transfer-reasons", response_model=list[TransferReasonOut])
async def list_transfer_reasons(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    active: bool | None = Query(None),
):
    q = select(TransferReason).where(TransferReason.workspace_id == workspace_id)
    if active is not None:
        q = q.where(TransferReason.active.is_(active))
    q = q.order_by(TransferReason.label.asc())
    return (await db.execute(q)).scalars().all()


@router.post("/transfer-reasons", response_model=TransferReasonOut, status_code=201)
async def create_transfer_reason(
    workspace_id: UUID,
    body: TransferReasonCreate,
    request: Request,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    reason = TransferReason(workspace_id=workspace_id, **body.model_dump())
    db.add(reason)
    try:
        await db.flush()
        await db.refresh(reason)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Reason already exists")
    await log_security_event(
        action="transfer_reason_created",
        workspace_id=workspace_id,
        user_id=current_user.id,
        target_type="transfer_reason",
        target_id=reason.id,
        new_value={"label": reason.label, "required": reason.required},
        ip_address=client_ip(request),
        user_agent=user_agent(request),
    )
    return reason


@router.patch("/transfer-reasons/{reason_id}", response_model=TransferReasonOut)
async def update_transfer_reason(
    workspace_id: UUID,
    reason_id: UUID,
    body: TransferReasonUpdate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    reason = await db.get(TransferReason, reason_id)
    if not reason or reason.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Reason not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(reason, field, value)
    await db.flush()
    await db.refresh(reason)
    return reason


@router.delete("/transfer-reasons/{reason_id}", status_code=204)
async def delete_transfer_reason(
    workspace_id: UUID,
    reason_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    reason = await db.get(TransferReason, reason_id)
    if not reason or reason.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Reason not found")
    await db.delete(reason)


# ── Service reasons ─────────────────────────────────────────────────────────

@router.get("/service-reasons", response_model=list[ServiceReasonOut])
async def list_service_reasons(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    active: bool | None = Query(None),
):
    q = select(ServiceReason).where(ServiceReason.workspace_id == workspace_id)
    if active is not None:
        q = q.where(ServiceReason.active.is_(active))
    q = q.order_by(ServiceReason.position.asc(), ServiceReason.label.asc())
    return (await db.execute(q)).scalars().all()


@router.post("/service-reasons", response_model=ServiceReasonOut, status_code=201)
async def create_service_reason(
    workspace_id: UUID,
    body: ServiceReasonCreate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    reason = ServiceReason(workspace_id=workspace_id, **body.model_dump())
    db.add(reason)
    try:
        await db.flush()
        await db.refresh(reason)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Reason already exists")
    return reason


@router.patch("/service-reasons/{reason_id}", response_model=ServiceReasonOut)
async def update_service_reason(
    workspace_id: UUID,
    reason_id: UUID,
    body: ServiceReasonUpdate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    reason = await db.get(ServiceReason, reason_id)
    if not reason or reason.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Reason not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(reason, field, value)
    await db.flush()
    await db.refresh(reason)
    return reason


@router.delete("/service-reasons/{reason_id}", status_code=204)
async def delete_service_reason(
    workspace_id: UUID,
    reason_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    reason = await db.get(ServiceReason, reason_id)
    if not reason or reason.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Reason not found")
    await db.delete(reason)


# ── Snooze ──────────────────────────────────────────────────────────────────

@router.post("/conversations/{conversation_id}/snooze", response_model=SnoozeOut)
async def snooze_conversation(
    workspace_id: UUID,
    conversation_id: UUID,
    body: SnoozeRequest,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await get_conversation_or_404(db, workspace_id, conversation_id)
    if body.until <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="`until` must be in the future")

    existing = await db.execute(
        select(ConversationSnooze).where(ConversationSnooze.conversation_id == conversation_id)
    )
    snooze = existing.scalar_one_or_none()
    if snooze:
        snooze.until = body.until
        snooze.reason = body.reason
        snooze.snoozed_by = current_user.id
    else:
        snooze = ConversationSnooze(
            workspace_id=workspace_id,
            conversation_id=conversation_id,
            until=body.until,
            reason=body.reason,
            snoozed_by=current_user.id,
        )
        db.add(snooze)
    await db.flush()
    await db.refresh(snooze)
    return snooze


@router.delete("/conversations/{conversation_id}/snooze", status_code=204)
async def unsnooze_conversation(
    workspace_id: UUID,
    conversation_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(ConversationSnooze).where(
            ConversationSnooze.workspace_id == workspace_id,
            ConversationSnooze.conversation_id == conversation_id,
        )
    )
    snooze = result.scalar_one_or_none()
    if snooze:
        await db.delete(snooze)


@router.get("/conversations/{conversation_id}/snooze", response_model=SnoozeOut | None)
async def get_snooze(
    workspace_id: UUID,
    conversation_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(ConversationSnooze).where(
            ConversationSnooze.workspace_id == workspace_id,
            ConversationSnooze.conversation_id == conversation_id,
        )
    )
    return result.scalar_one_or_none()


# ── Custom views ────────────────────────────────────────────────────────────

@router.get("/views", response_model=list[ConversationViewOut])
async def list_views(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    sectors_q = await db.execute(
        select(SectorMember.sector_id).where(
            SectorMember.workspace_id == workspace_id,
            SectorMember.user_id == current_user.id,
        )
    )
    sectors = [r[0] for r in sectors_q.all()]
    visible_filter = or_(
        ConversationView.visibility == ViewVisibility.workspace,
        (ConversationView.visibility == ViewVisibility.personal) & (ConversationView.user_id == current_user.id),
        (ConversationView.visibility == ViewVisibility.sector) & (ConversationView.sector_id.in_(sectors) if sectors else False),
    )
    q = (
        select(ConversationView)
        .where(ConversationView.workspace_id == workspace_id, visible_filter)
        .order_by(ConversationView.position.asc(), ConversationView.name.asc())
    )
    return (await db.execute(q)).scalars().all()


@router.post("/views", response_model=ConversationViewOut, status_code=201)
async def create_view(
    workspace_id: UUID,
    body: ConversationViewCreate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user_id = current_user.id if body.visibility == ViewVisibility.personal else None
    view = ConversationView(
        workspace_id=workspace_id,
        user_id=user_id,
        sector_id=body.sector_id,
        visibility=body.visibility,
        name=body.name,
        icon=body.icon,
        filters=body.filters,
        pinned=body.pinned,
        position=body.position,
    )
    db.add(view)
    await db.flush()
    await db.refresh(view)
    return view


@router.patch("/views/{view_id}", response_model=ConversationViewOut)
async def update_view(
    workspace_id: UUID,
    view_id: UUID,
    body: ConversationViewUpdate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    view = await db.get(ConversationView, view_id)
    if not view or view.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="View not found")
    if view.visibility == ViewVisibility.personal and view.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot edit another user's view")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(view, field, value)
    await db.flush()
    await db.refresh(view)
    return view


@router.delete("/views/{view_id}", status_code=204)
async def delete_view(
    workspace_id: UUID,
    view_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    view = await db.get(ConversationView, view_id)
    if not view or view.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="View not found")
    if view.visibility == ViewVisibility.personal and view.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete another user's view")
    await db.delete(view)


# ── Mention inbox ───────────────────────────────────────────────────────────

@router.get("/mentions", response_model=dict)
async def list_mentions(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    unread: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    q = select(MentionInbox).where(
        MentionInbox.workspace_id == workspace_id,
        MentionInbox.user_id == current_user.id,
    )
    if unread is True:
        q = q.where(MentionInbox.read_at.is_(None))
    elif unread is False:
        q = q.where(MentionInbox.read_at.is_not(None))
    q = q.order_by(MentionInbox.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(q)).scalars().all()
    unread_count_q = await db.execute(
        select(MentionInbox).where(
            MentionInbox.workspace_id == workspace_id,
            MentionInbox.user_id == current_user.id,
            MentionInbox.read_at.is_(None),
        )
    )
    unread_count = len(unread_count_q.scalars().all())
    return {
        "items": [MentionOut.model_validate(m) for m in items],
        "unread_count": unread_count,
        "page": page,
        "page_size": page_size,
    }


@router.post("/mentions/read", status_code=204)
async def mark_mentions_read(
    workspace_id: UUID,
    body: Annotated[MentionMarkRead, Body()],
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = (
        sa_update(MentionInbox)
        .where(
            MentionInbox.workspace_id == workspace_id,
            MentionInbox.user_id == current_user.id,
            MentionInbox.read_at.is_(None),
        )
        .values(read_at=datetime.now(timezone.utc))
    )
    if body.mention_ids:
        stmt = stmt.where(MentionInbox.id.in_(body.mention_ids))
    await db.execute(stmt)
