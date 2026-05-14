from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.conversation import Message, MessageIdentity
from app.models.enums import SenderType
from app.models.workspace import User
from app.schemas.message import MessageOut, SendMessageRequest
from app.services.conversation_service import get_conversation_or_404
from app.services.message_service import send_agent_message

router = APIRouter(
    prefix="/workspaces/{workspace_id}/conversations/{conversation_id}/messages",
    tags=["messages"],
)


@router.get("", response_model=dict)
async def list_messages(
    workspace_id: UUID,
    conversation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    await get_conversation_or_404(db, workspace_id, conversation_id)
    q = select(Message).where(Message.conversation_id == conversation_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    q = q.order_by(Message.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(q)).scalars().all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=MessageOut, status_code=201)
async def send_message(
    workspace_id: UUID,
    conversation_id: UUID,
    body: SendMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    conv = await get_conversation_or_404(db, workspace_id, conversation_id)
    msg = await send_agent_message(db, conv, current_user.id, body)
    from app.websocket.manager import manager
    await manager.broadcast(
        str(workspace_id),
        {"type": "message.new", "conversation_id": str(conversation_id), "message_id": str(msg.id)},
    )
    return msg


@router.post("/read", status_code=204)
async def mark_read(
    workspace_id: UUID,
    conversation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await get_conversation_or_404(db, workspace_id, conversation_id)
    await db.execute(
        sa_update(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.sender_type != SenderType.agent,
            Message.is_read.is_(False),
        )
        .values(is_read=True)
    )
