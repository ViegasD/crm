"""CRUD endpoints for the reopen / new-protocol policy.

A policy row with ``sector_id=NULL`` is the workspace default. A row with a
sector_id overrides that default for the given sector. Each (workspace_id,
sector_id) tuple is unique.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles, require_workspace_member
from app.models.conversation import ConversationPolicy
from app.models.workspace import User
from app.schemas.conversation_policy import (
    ConversationPolicyIn,
    ConversationPolicyOut,
    ResolvedPolicyOut,
)
from app.services.timeline_service import resolve_policy

router = APIRouter(
    prefix="/workspaces/{workspace_id}/conversation-policies",
    tags=["conversation-policies"],
)


@router.get("", response_model=list[ConversationPolicyOut])
async def list_policies(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (
        await db.execute(
            select(ConversationPolicy)
            .where(ConversationPolicy.workspace_id == workspace_id)
            .order_by(ConversationPolicy.sector_id.is_(None).desc())
        )
    ).scalars().all()
    return rows


@router.get("/effective", response_model=ResolvedPolicyOut)
async def get_effective_policy(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    sector_id: UUID | None = None,
):
    """Return the policy that would actually apply for a given sector after
    falling back through sector → workspace → hard default."""
    return await resolve_policy(db, workspace_id, sector_id)


@router.put("", response_model=ConversationPolicyOut)
async def upsert_policy(
    workspace_id: UUID,
    body: ConversationPolicyIn,
    current_user: Annotated[User, Depends(require_roles("admin", "supervisor"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create or update the policy for (workspace, sector). sector_id=NULL is
    the workspace default."""
    existing = (
        await db.execute(
            select(ConversationPolicy).where(
                ConversationPolicy.workspace_id == workspace_id,
                ConversationPolicy.sector_id.is_(body.sector_id)
                if body.sector_id is None
                else ConversationPolicy.sector_id == body.sector_id,
            )
        )
    ).scalar_one_or_none()

    if existing:
        existing.reopen_mode = body.reopen_mode
        existing.reopen_window_hours = body.reopen_window_hours
        existing.inherit_assignee_on_new = body.inherit_assignee_on_new
        await db.flush()
        await db.refresh(existing)
        return existing

    row = ConversationPolicy(
        workspace_id=workspace_id,
        sector_id=body.sector_id,
        reopen_mode=body.reopen_mode,
        reopen_window_hours=body.reopen_window_hours,
        inherit_assignee_on_new=body.inherit_assignee_on_new,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


@router.delete("/{policy_id}", status_code=204)
async def delete_policy(
    workspace_id: UUID,
    policy_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin", "supervisor"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(ConversationPolicy, policy_id)
    if not row or row.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    await db.delete(row)
