"""Detect @mentions in note text and resolve them to workspace users."""
import re
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import User, UserWorkspaceMembership

_MENTION = re.compile(r"@([A-Za-z0-9_.\-]+)")


async def resolve_mentions(
    db: AsyncSession, workspace_id: UUID, text: str | None
) -> list[User]:
    """Match @handles in `text` against the workspace member list.

    Matching is case-insensitive against the user's display name's first token,
    full name (spaces removed) and email local-part. Duplicates are dropped.
    """
    if not text:
        return []
    handles = {h.lower() for h in _MENTION.findall(text)}
    if not handles:
        return []
    result = await db.execute(
        select(User)
        .join(UserWorkspaceMembership, UserWorkspaceMembership.user_id == User.id)
        .where(UserWorkspaceMembership.workspace_id == workspace_id)
    )
    members = result.scalars().all()
    matched: dict[UUID, User] = {}
    for user in members:
        name_tokens = (user.name or "").lower().split()
        candidates = set(name_tokens)
        if name_tokens:
            candidates.add("".join(name_tokens))
        if user.email:
            candidates.add(user.email.split("@", 1)[0].lower())
        if candidates & handles:
            matched[user.id] = user
    return list(matched.values())
