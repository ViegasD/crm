from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.workspace import User
from app.schemas.conversation import (
    ConversationListFilters,
    ConversationOut,
    ConversationTransfer,
    ConversationUpdate,
)
from app.services.conversation_service import (
    get_conversation_or_404,
    list_conversations,
    transfer_conversation,
    update_conversation,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/conversations", tags=["conversations"])


@router.get("", response_model=dict)
async def list_convs(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = Query(None),
    assignee_id: UUID | None = Query(None),
    sector_id: UUID | None = Query(None),
    channel_account_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
):
    filters = ConversationListFilters(
        status=status,
        assignee_id=assignee_id,
        sector_id=sector_id,
        channel_account_id=channel_account_id,
        page=page,
        page_size=page_size,
    )
    items, total = await list_conversations(db, workspace_id, filters)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{conversation_id}", response_model=ConversationOut)
async def get_conv(
    workspace_id: UUID,
    conversation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await get_conversation_or_404(db, workspace_id, conversation_id)


@router.patch("/{conversation_id}", response_model=ConversationOut)
async def update_conv(
    workspace_id: UUID,
    conversation_id: UUID,
    body: ConversationUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    conv = await update_conversation(db, workspace_id, conversation_id, body, current_user.id)
    await _broadcast_update(workspace_id, conv)
    return conv


@router.post("/{conversation_id}/transfer", response_model=ConversationOut)
async def transfer_conv(
    workspace_id: UUID,
    conversation_id: UUID,
    body: ConversationTransfer,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    conv = await transfer_conversation(db, workspace_id, conversation_id, body, current_user.id)
    await _broadcast_update(workspace_id, conv)
    return conv


async def _broadcast_update(workspace_id: UUID, conv) -> None:
    from app.websocket.manager import manager
    await manager.broadcast(
        str(workspace_id),
        {"type": "conversation.updated", "conversation_id": str(conv.id), "status": conv.status},
    )
