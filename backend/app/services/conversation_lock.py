"""Conversation locking — soft, TTL-based reservation that an agent is replying.

- acquire_lock: tries to lock; renews if same holder still holds; refuses if
  another holder owns it within TTL.
- release_lock: explicit release by the holder.
- expire_locks: cleanup job (cron'd by Celery beat).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stage9_extras import ConversationLock
from app.models.workspace import User
from app.websocket.manager import manager


async def get_lock(db: AsyncSession, conversation_id: UUID) -> ConversationLock | None:
    result = await db.execute(
        select(ConversationLock).where(ConversationLock.conversation_id == conversation_id)
    )
    return result.scalar_one_or_none()


async def acquire_lock(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    conversation_id: UUID,
    user_id: UUID,
    ttl_seconds: int = 90,
) -> tuple[ConversationLock | None, str | None]:
    """Returns (lock, error). error is None on success."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(seconds=max(15, min(ttl_seconds, 600)))
    existing = await get_lock(db, conversation_id)
    if existing:
        if existing.expires_at > now and existing.holder_user_id != user_id:
            return None, "locked_by_other"
        # Same holder OR expired — renew
        existing.holder_user_id = user_id
        existing.workspace_id = workspace_id
        existing.acquired_at = now
        existing.expires_at = expires
        await db.flush()
        await db.refresh(existing)
        await _broadcast_lock(workspace_id, existing)
        return existing, None
    lock = ConversationLock(
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        holder_user_id=user_id,
        acquired_at=now,
        expires_at=expires,
    )
    try:
        async with db.begin_nested():
            db.add(lock)
            await db.flush()
        await db.refresh(lock)
    except IntegrityError:
        return None, "race_condition"
    await _broadcast_lock(workspace_id, lock)
    return lock, None


async def release_lock(
    db: AsyncSession, conversation_id: UUID, user_id: UUID
) -> bool:
    lock = await get_lock(db, conversation_id)
    if not lock or lock.holder_user_id != user_id:
        return False
    workspace_id = lock.workspace_id
    await db.delete(lock)
    await manager.broadcast(
        str(workspace_id),
        {
            "type": "conversation.lock_released",
            "conversation_id": str(conversation_id),
        },
    )
    return True


async def expire_locks(db: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        sa_delete(ConversationLock).where(ConversationLock.expires_at <= now)
    )
    return result.rowcount or 0


async def _broadcast_lock(workspace_id: UUID, lock: ConversationLock) -> None:
    await manager.broadcast(
        str(workspace_id),
        {
            "type": "conversation.locked",
            "conversation_id": str(lock.conversation_id),
            "holder_user_id": str(lock.holder_user_id),
            "expires_at": lock.expires_at.isoformat(),
        },
    )
