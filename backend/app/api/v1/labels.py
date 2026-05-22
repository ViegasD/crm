from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_workspace_member
from app.core.request_meta import client_ip, user_agent
from app.models.catalog import LabelCategory
from app.models.conversation import Conversation, ConversationEvent, ConversationLabel, Label
from app.models.enums import ConvEventType
from app.models.workspace import User
from app.schemas.label import (
    LabelAssign,
    LabelCategoryCreate,
    LabelCategoryOut,
    LabelCategoryUpdate,
    LabelCreate,
    LabelOut,
    LabelUpdate,
)
from app.services.security_audit_service import log_security_event

router = APIRouter(prefix="/workspaces/{workspace_id}/labels", tags=["labels"])


# ── Label categories ─────────────────────────────────────────────────────────

@router.get("/categories", response_model=list[LabelCategoryOut])
async def list_label_categories(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(LabelCategory)
        .where(LabelCategory.workspace_id == workspace_id)
        .order_by(LabelCategory.position.asc(), LabelCategory.name.asc())
    )
    return result.scalars().all()


@router.post("/categories", response_model=LabelCategoryOut, status_code=201)
async def create_label_category(
    workspace_id: UUID,
    body: LabelCategoryCreate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    cat = LabelCategory(workspace_id=workspace_id, **body.model_dump())
    db.add(cat)
    try:
        await db.flush()
        await db.refresh(cat)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Category name already exists")
    return cat


@router.patch("/categories/{category_id}", response_model=LabelCategoryOut)
async def update_label_category(
    workspace_id: UUID,
    category_id: UUID,
    body: LabelCategoryUpdate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    cat = await db.get(LabelCategory, category_id)
    if not cat or cat.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Category not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(cat, field, value)
    try:
        await db.flush()
        await db.refresh(cat)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Category name already exists")
    return cat


@router.delete("/categories/{category_id}", status_code=204)
async def delete_label_category(
    workspace_id: UUID,
    category_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    cat = await db.get(LabelCategory, category_id)
    if not cat or cat.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.delete(cat)


# ── Labels ───────────────────────────────────────────────────────────────────

@router.post("", response_model=LabelOut, status_code=201)
async def create_label(
    workspace_id: UUID,
    body: LabelCreate,
    request: Request,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    label = Label(workspace_id=workspace_id, **body.model_dump())
    db.add(label)
    try:
        await db.flush()
        await db.refresh(label)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Label name already exists")
    await log_security_event(
        action="label_created",
        workspace_id=workspace_id,
        user_id=current_user.id,
        target_type="label",
        target_id=label.id,
        new_value={"name": label.name, "color": label.color, "category_id": str(label.category_id) if label.category_id else None},
        ip_address=client_ip(request),
        user_agent=user_agent(request),
    )
    return label


@router.get("", response_model=list[LabelOut])
async def list_labels(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Label).where(Label.workspace_id == workspace_id).order_by(Label.name.asc())
    )
    return result.scalars().all()


@router.patch("/{label_id}", response_model=LabelOut)
async def update_label(
    workspace_id: UUID,
    label_id: UUID,
    body: LabelUpdate,
    request: Request,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    label = await db.get(Label, label_id)
    if not label or label.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Label not found")
    old = {"name": label.name, "color": label.color, "category_id": str(label.category_id) if label.category_id else None}
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(label, field, value)
    try:
        await db.flush()
        await db.refresh(label)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Label name already exists")
    await log_security_event(
        action="label_updated",
        workspace_id=workspace_id,
        user_id=current_user.id,
        target_type="label",
        target_id=label.id,
        old_value=old,
        new_value={"name": label.name, "color": label.color, "category_id": str(label.category_id) if label.category_id else None},
        ip_address=client_ip(request),
        user_agent=user_agent(request),
    )
    return label


@router.delete("/{label_id}", status_code=204)
async def delete_label(
    workspace_id: UUID,
    label_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    label = await db.get(Label, label_id)
    if not label or label.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Label not found")
    old = {"name": label.name, "color": label.color}
    await db.delete(label)
    await log_security_event(
        action="label_deleted",
        workspace_id=workspace_id,
        user_id=current_user.id,
        target_type="label",
        target_id=label_id,
        old_value=old,
        ip_address=client_ip(request),
        user_agent=user_agent(request),
    )


@router.post("/{label_id}/assign", status_code=204)
async def assign_label(
    workspace_id: UUID,
    label_id: UUID,
    body: LabelAssign,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    label = await db.get(Label, label_id)
    conv = await db.get(Conversation, body.conversation_id)
    if not label or label.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Label not found")
    if not conv or conv.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    existing = await db.execute(
        select(ConversationLabel).where(
            ConversationLabel.workspace_id == workspace_id,
            ConversationLabel.conversation_id == body.conversation_id,
            ConversationLabel.label_id == label_id,
        )
    )
    if existing.scalar_one_or_none():
        return
    db.add(
        ConversationLabel(
            workspace_id=workspace_id,
            conversation_id=body.conversation_id,
            label_id=label_id,
            assigned_by=current_user.id,
        )
    )
    db.add(
        ConversationEvent(
            workspace_id=workspace_id,
            conversation_id=body.conversation_id,
            type=ConvEventType.label_added,
            actor_id=current_user.id,
            actor_type="agent",
            payload={"label_id": str(label_id), "label_name": label.name, "color": label.color},
        )
    )


@router.delete("/{label_id}/assign/{conversation_id}", status_code=204)
async def unassign_label(
    workspace_id: UUID,
    label_id: UUID,
    conversation_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    label = await db.get(Label, label_id)
    conv = await db.get(Conversation, conversation_id)
    if not label or label.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Label not found")
    if not conv or conv.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.execute(
        sa_delete(ConversationLabel).where(
            ConversationLabel.workspace_id == workspace_id,
            ConversationLabel.conversation_id == conversation_id,
            ConversationLabel.label_id == label_id,
        )
    )
    db.add(
        ConversationEvent(
            workspace_id=workspace_id,
            conversation_id=conversation_id,
            type=ConvEventType.label_removed,
            actor_id=current_user.id,
            actor_type="agent",
            payload={"label_id": str(label_id), "label_name": label.name},
        )
    )
