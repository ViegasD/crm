from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.conversation import ConversationLabel, Label
from app.models.workspace import User
from app.schemas.label import LabelAssign, LabelCreate, LabelOut

router = APIRouter(prefix="/workspaces/{workspace_id}/labels", tags=["labels"])


@router.post("", response_model=LabelOut, status_code=201)
async def create_label(
    workspace_id: UUID,
    body: LabelCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    label = Label(workspace_id=workspace_id, name=body.name, color=body.color)
    db.add(label)
    await db.flush()
    return label


@router.get("", response_model=list[LabelOut])
async def list_labels(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Label).where(Label.workspace_id == workspace_id))
    return result.scalars().all()


@router.delete("/{label_id}", status_code=204)
async def delete_label(
    workspace_id: UUID,
    label_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    label = await db.get(Label, label_id)
    if not label or label.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Label not found")
    await db.delete(label)


# Conversation-label assignment
@router.post("/{label_id}/assign", status_code=204)
async def assign_label(
    workspace_id: UUID,
    label_id: UUID,
    body: LabelAssign,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    db.add(ConversationLabel(conversation_id=body.conversation_id, label_id=label_id))


@router.delete("/{label_id}/assign/{conversation_id}", status_code=204)
async def unassign_label(
    workspace_id: UUID,
    label_id: UUID,
    conversation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.execute(
        sa_delete(ConversationLabel).where(
            ConversationLabel.conversation_id == conversation_id,
            ConversationLabel.label_id == label_id,
        )
    )
