from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import require_workspace_member
from app.core.request_meta import client_ip, user_agent
from app.models.enums import CannedVisibility
from app.models.macros import Macro, MacroAction
from app.models.workspace import SectorMember, User
from app.schemas.macros import (
    MacroCreate,
    MacroOut,
    MacroRunRequest,
    MacroRunResult,
    MacroUpdate,
)
from app.services.macro_executor import run_macro
from app.services.security_audit_service import log_security_event

router = APIRouter(prefix="/workspaces/{workspace_id}/macros", tags=["macros"])


async def _user_sectors(db: AsyncSession, workspace_id: UUID, user_id: UUID) -> list[UUID]:
    result = await db.execute(
        select(SectorMember.sector_id).where(
            SectorMember.workspace_id == workspace_id,
            SectorMember.user_id == user_id,
        )
    )
    return [row[0] for row in result.all()]


@router.post("", response_model=MacroOut, status_code=201)
async def create_macro(
    workspace_id: UUID,
    body: MacroCreate,
    request: Request,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user_id = current_user.id if body.visibility == CannedVisibility.user else None
    macro = Macro(
        workspace_id=workspace_id,
        user_id=user_id,
        sector_id=body.sector_id,
        name=body.name,
        description=body.description,
        visibility=body.visibility,
        active=body.active,
    )
    db.add(macro)
    await db.flush()
    for action_in in body.actions:
        db.add(MacroAction(
            macro_id=macro.id,
            position=action_in.position,
            action_type=action_in.action_type,
            params=action_in.params,
        ))
    await db.flush()
    await db.refresh(macro, attribute_names=["actions"])
    await log_security_event(
        action="macro_created",
        workspace_id=workspace_id,
        user_id=current_user.id,
        target_type="macro",
        target_id=macro.id,
        new_value={"name": macro.name, "visibility": macro.visibility.value, "actions": len(body.actions)},
        ip_address=client_ip(request),
        user_agent=user_agent(request),
    )
    return macro


@router.get("", response_model=list[MacroOut])
async def list_macros(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    sectors = await _user_sectors(db, workspace_id, current_user.id)
    visible_filter = or_(
        Macro.visibility == CannedVisibility.workspace,
        (Macro.visibility == CannedVisibility.user) & (Macro.user_id == current_user.id),
        (Macro.visibility == CannedVisibility.sector) & (Macro.sector_id.in_(sectors) if sectors else False),
    )
    q = (
        select(Macro)
        .where(Macro.workspace_id == workspace_id, visible_filter, Macro.active.is_(True))
        .options(selectinload(Macro.actions))
        .order_by(Macro.name.asc())
    )
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{macro_id}", response_model=MacroOut)
async def get_macro(
    workspace_id: UUID,
    macro_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    q = (
        select(Macro)
        .where(Macro.id == macro_id, Macro.workspace_id == workspace_id)
        .options(selectinload(Macro.actions))
    )
    macro = (await db.execute(q)).scalar_one_or_none()
    if not macro:
        raise HTTPException(status_code=404, detail="Macro not found")
    return macro


@router.patch("/{macro_id}", response_model=MacroOut)
async def update_macro(
    workspace_id: UUID,
    macro_id: UUID,
    body: MacroUpdate,
    request: Request,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    macro = await db.get(Macro, macro_id)
    if not macro or macro.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Macro not found")
    if macro.visibility == CannedVisibility.user and macro.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot edit another user's macro")

    payload = body.model_dump(exclude_none=True)
    actions = payload.pop("actions", None)
    for field, value in payload.items():
        setattr(macro, field, value)
    if actions is not None:
        from sqlalchemy import delete as sa_delete
        await db.execute(sa_delete(MacroAction).where(MacroAction.macro_id == macro.id))
        for action_in in actions:
            db.add(MacroAction(
                macro_id=macro.id,
                position=action_in.get("position", 0),
                action_type=action_in["action_type"],
                params=action_in.get("params", {}),
            ))
    await db.flush()
    q = (
        select(Macro)
        .where(Macro.id == macro.id)
        .options(selectinload(Macro.actions))
    )
    macro = (await db.execute(q)).scalar_one()
    await log_security_event(
        action="macro_updated",
        workspace_id=workspace_id,
        user_id=current_user.id,
        target_type="macro",
        target_id=macro.id,
        new_value={"name": macro.name},
        ip_address=client_ip(request),
        user_agent=user_agent(request),
    )
    return macro


@router.delete("/{macro_id}", status_code=204)
async def delete_macro(
    workspace_id: UUID,
    macro_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    macro = await db.get(Macro, macro_id)
    if not macro or macro.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Macro not found")
    if macro.visibility == CannedVisibility.user and macro.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete another user's macro")
    await db.delete(macro)
    await log_security_event(
        action="macro_deleted",
        workspace_id=workspace_id,
        user_id=current_user.id,
        target_type="macro",
        target_id=macro_id,
        ip_address=client_ip(request),
        user_agent=user_agent(request),
    )


@router.post("/{macro_id}/run", response_model=MacroRunResult)
async def run_macro_endpoint(
    workspace_id: UUID,
    macro_id: UUID,
    body: MacroRunRequest,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    q = (
        select(Macro)
        .where(Macro.id == macro_id, Macro.workspace_id == workspace_id)
        .options(selectinload(Macro.actions))
    )
    macro = (await db.execute(q)).scalar_one_or_none()
    if not macro or not macro.active:
        raise HTTPException(status_code=404, detail="Macro not found")
    result = await run_macro(
        db,
        workspace_id=workspace_id,
        macro=macro,
        conversation_id=body.conversation_id,
        actor=current_user,
    )
    return MacroRunResult(executed=result.executed, skipped=result.skipped, errors=result.errors)
