"""Shared read/write visibility rule for user-facing conversation operations.

Being an administrator does not bypass private-conversation visibility. System
workers use their own trusted queries; user-facing callers must supply an actor.
"""
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, ConversationParticipant
from app.models.workspace import UserWorkspaceMembership


def conversation_access_clause(workspace_id: UUID, user_id: UUID):
    membership = exists(select(UserWorkspaceMembership.id).where(
        UserWorkspaceMembership.workspace_id == workspace_id,
        UserWorkspaceMembership.user_id == user_id,
    ))
    participant = exists(select(ConversationParticipant.id).where(
        ConversationParticipant.workspace_id == workspace_id,
        ConversationParticipant.conversation_id == Conversation.id,
        ConversationParticipant.user_id == user_id,
    ))
    return and_(
        Conversation.workspace_id == workspace_id,
        membership,
        or_(Conversation.is_private.is_(False), Conversation.assignee_id == user_id, participant),
    )


async def require_conversation(db: AsyncSession, workspace_id: UUID, conversation_id: UUID, user_id: UUID):
    conv = await db.scalar(select(Conversation).where(
        Conversation.id == conversation_id,
        conversation_access_clause(workspace_id, user_id),
    ))
    if conv is None:
        # Do not distinguish a hidden record from a missing one.
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


async def require_conversations(db: AsyncSession, workspace_id: UUID, conversation_ids: list[UUID], user_id: UUID):
    requested = set(conversation_ids)
    visible = set((await db.scalars(select(Conversation.id).where(
        Conversation.id.in_(requested), conversation_access_clause(workspace_id, user_id),
    ))).all())
    if requested != visible:
        raise HTTPException(status_code=404, detail="Conversation not found")


async def require_workspace_user(db: AsyncSession, workspace_id: UUID, user_id: UUID):
    member = await db.scalar(select(UserWorkspaceMembership.id).where(
        UserWorkspaceMembership.workspace_id == workspace_id,
        UserWorkspaceMembership.user_id == user_id,
    ))
    if member is None:
        raise HTTPException(status_code=404, detail="Workspace member not found")
