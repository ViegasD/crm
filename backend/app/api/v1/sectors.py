from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_workspace_member
from app.models.workspace import Sector, SectorMember, User
from app.schemas.workspace import SectorCreate, SectorMemberAdd, SectorOut

router = APIRouter(prefix="/workspaces/{workspace_id}/sectors", tags=["sectors"])


@router.post("", response_model=SectorOut, status_code=201)
async def create_sector(
    workspace_id: UUID,
    body: SectorCreate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    sector = Sector(workspace_id=workspace_id, name=body.name, description=body.description)
    db.add(sector)
    await db.flush()
    return sector


@router.get("", response_model=list[SectorOut])
async def list_sectors(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Sector).where(Sector.workspace_id == workspace_id))
    return result.scalars().all()


@router.delete("/{sector_id}", status_code=204)
async def delete_sector(
    workspace_id: UUID,
    sector_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    sector = await db.get(Sector, sector_id)
    if not sector or sector.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Sector not found")
    await db.delete(sector)


@router.post("/{sector_id}/members", status_code=204)
async def add_member(
    workspace_id: UUID,
    sector_id: UUID,
    body: SectorMemberAdd,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    db.add(SectorMember(sector_id=sector_id, user_id=body.user_id, workspace_id=workspace_id))


@router.delete("/{sector_id}/members/{user_id}", status_code=204)
async def remove_member(
    workspace_id: UUID,
    sector_id: UUID,
    user_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(SectorMember).where(
            SectorMember.sector_id == sector_id,
            SectorMember.user_id == user_id,
        )
    )
    sm = result.scalar_one_or_none()
    if not sm:
        raise HTTPException(status_code=404, detail="Member not in sector")
    await db.delete(sm)
