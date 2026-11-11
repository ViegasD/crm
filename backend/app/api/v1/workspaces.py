from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_workspace_member, require_roles
from app.models.workspace import User, UserWorkspaceMembership, Workspace
from app.schemas.workspace import MembershipOut, MembershipUserInline, WorkspaceCreate, WorkspaceOut

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceOut, status_code=201)
async def create_workspace(
    body: WorkspaceCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    existing = await db.execute(select(Workspace).where(Workspace.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already taken")
    ws = Workspace(name=body.name, slug=body.slug)
    db.add(ws)
    await db.flush()
    db.add(UserWorkspaceMembership(user_id=current_user.id, workspace_id=ws.id, role="admin"))
    return ws


@router.get("", response_model=list[WorkspaceOut])
async def list_workspaces(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Workspace)
        .join(UserWorkspaceMembership, UserWorkspaceMembership.workspace_id == Workspace.id)
        .where(UserWorkspaceMembership.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/{workspace_id}", response_model=WorkspaceOut)
async def get_workspace(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ws = await db.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return ws


@router.get("/{workspace_id}/members", response_model=list[MembershipOut])
async def list_members(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(UserWorkspaceMembership, User)
        .join(User, User.id == UserWorkspaceMembership.user_id)
        .where(UserWorkspaceMembership.workspace_id == workspace_id)
        .order_by(User.name.asc())
    )
    output: list[MembershipOut] = []
    for membership, user in result.all():
        output.append(
            MembershipOut.model_validate(membership).model_copy(
                update={"user": MembershipUserInline.model_validate(user)}
            )
        )
    return output


@router.delete("/{workspace_id}/members/{user_id}", status_code=204)
async def remove_member(
    workspace_id: UUID,
    user_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Serialize administrator removals within a workspace so two simultaneous
    # requests cannot both remove what each believed was the penultimate admin.
    await db.execute(select(Workspace.id).where(Workspace.id == workspace_id).with_for_update())
    result = await db.execute(
        select(UserWorkspaceMembership).where(
            UserWorkspaceMembership.workspace_id == workspace_id,
            UserWorkspaceMembership.user_id == user_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=404, detail="Member not found")
    if membership.role == "admin":
        admins = (await db.execute(select(UserWorkspaceMembership.id).where(
            UserWorkspaceMembership.workspace_id == workspace_id,
            UserWorkspaceMembership.role == "admin",
        ))).scalars().all()
        if len(admins) <= 1:
            raise HTTPException(status_code=409, detail="Cannot remove the last workspace administrator")
    await db.delete(membership)
