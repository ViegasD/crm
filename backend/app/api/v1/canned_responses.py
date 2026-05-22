from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_workspace_member
from app.core.request_meta import client_ip, user_agent
from app.models.catalog import CannedResponseCategory
from app.models.conversation import CannedResponse
from app.models.enums import CannedVisibility
from app.models.workspace import User, UserWorkspaceMembership
from app.schemas.canned_response import (
    CannedCategoryCreate,
    CannedCategoryOut,
    CannedCategoryUpdate,
    CannedResponseCreate,
    CannedResponseOut,
    CannedResponseUpdate,
)
from app.services.canned_response_service import build_render_context, render_template
from app.services.security_audit_service import log_security_event

router = APIRouter(prefix="/workspaces/{workspace_id}/canned-responses", tags=["canned-responses"])


# ── Categories ───────────────────────────────────────────────────────────────

@router.get("/categories", response_model=list[CannedCategoryOut])
async def list_categories(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(CannedResponseCategory)
        .where(CannedResponseCategory.workspace_id == workspace_id)
        .order_by(CannedResponseCategory.position.asc(), CannedResponseCategory.name.asc())
    )
    return result.scalars().all()


@router.post("/categories", response_model=CannedCategoryOut, status_code=201)
async def create_category(
    workspace_id: UUID,
    body: CannedCategoryCreate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    cat = CannedResponseCategory(workspace_id=workspace_id, **body.model_dump())
    db.add(cat)
    try:
        await db.flush()
        await db.refresh(cat)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Category name already exists")
    return cat


@router.patch("/categories/{category_id}", response_model=CannedCategoryOut)
async def update_category(
    workspace_id: UUID,
    category_id: UUID,
    body: CannedCategoryUpdate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    cat = await db.get(CannedResponseCategory, category_id)
    if not cat or cat.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Category not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(cat, field, value)
    try:
        await db.flush()
        await db.refresh(cat)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Category name already exists")
    return cat


@router.delete("/categories/{category_id}", status_code=204)
async def delete_category(
    workspace_id: UUID,
    category_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    cat = await db.get(CannedResponseCategory, category_id)
    if not cat or cat.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.delete(cat)


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _user_sectors(db: AsyncSession, workspace_id: UUID, user_id: UUID) -> list[UUID]:
    """Return sector_ids the user belongs to (for visibility filtering)."""
    from app.models.workspace import SectorMember
    result = await db.execute(
        select(SectorMember.sector_id).where(
            SectorMember.workspace_id == workspace_id,
            SectorMember.user_id == user_id,
        )
    )
    return [row[0] for row in result.all()]


def _shortcut_conflict_filter(
    workspace_id: UUID,
    shortcut: str,
    visibility: CannedVisibility,
    user_id: UUID | None,
    sector_id: UUID | None,
):
    """Build a WHERE for detecting a shortcut already in use in the same scope."""
    base = [
        CannedResponse.workspace_id == workspace_id,
        CannedResponse.shortcut == shortcut,
    ]
    if visibility == CannedVisibility.user and user_id:
        base.append(CannedResponse.visibility == CannedVisibility.user)
        base.append(CannedResponse.user_id == user_id)
    elif visibility == CannedVisibility.sector and sector_id:
        base.append(CannedResponse.visibility == CannedVisibility.sector)
        base.append(CannedResponse.sector_id == sector_id)
    else:
        base.append(CannedResponse.visibility == CannedVisibility.workspace)
    return base


# ── Canned responses ─────────────────────────────────────────────────────────

@router.post("", response_model=CannedResponseOut, status_code=201)
async def create_canned_response(
    workspace_id: UUID,
    body: CannedResponseCreate,
    request: Request,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user_id = current_user.id if body.visibility == CannedVisibility.user else None
    # Conflict check inside scope
    conflict = await db.execute(
        select(CannedResponse.id).where(
            *_shortcut_conflict_filter(workspace_id, body.shortcut, body.visibility, user_id, body.sector_id)
        )
    )
    if conflict.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Shortcut already in use in this scope")

    data = body.model_dump()
    data["attachments"] = [a if isinstance(a, dict) else a.model_dump() for a in body.attachments]
    response = CannedResponse(workspace_id=workspace_id, user_id=user_id, **data)
    db.add(response)
    await db.flush()
    await db.refresh(response)
    await log_security_event(
        action="canned_response_created",
        workspace_id=workspace_id,
        user_id=current_user.id,
        target_type="canned_response",
        target_id=response.id,
        new_value={"shortcut": response.shortcut, "title": response.title, "visibility": response.visibility.value},
        ip_address=client_ip(request),
        user_agent=user_agent(request),
    )
    return response


@router.get("", response_model=list[CannedResponseOut])
async def list_canned_responses(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    active: bool | None = Query(True),
    category_id: UUID | None = Query(None),
    scope: str | None = Query(None, description="all | workspace | sector | personal"),
):
    sectors = await _user_sectors(db, workspace_id, current_user.id)

    visible_filter = or_(
        CannedResponse.visibility == CannedVisibility.workspace,
        (CannedResponse.visibility == CannedVisibility.user) & (CannedResponse.user_id == current_user.id),
        (CannedResponse.visibility == CannedVisibility.sector) & (CannedResponse.sector_id.in_(sectors) if sectors else False),
    )
    q = select(CannedResponse).where(CannedResponse.workspace_id == workspace_id, visible_filter)
    if active is not None:
        q = q.where(CannedResponse.active.is_(active))
    if category_id:
        q = q.where(CannedResponse.category_id == category_id)
    if scope == "workspace":
        q = q.where(CannedResponse.visibility == CannedVisibility.workspace)
    elif scope == "sector":
        q = q.where(CannedResponse.visibility == CannedVisibility.sector)
    elif scope == "personal":
        q = q.where(CannedResponse.visibility == CannedVisibility.user)

    q = q.order_by(CannedResponse.shortcut.asc())
    result = await db.execute(q)
    return result.scalars().all()


@router.patch("/{response_id}", response_model=CannedResponseOut)
async def update_canned_response(
    workspace_id: UUID,
    response_id: UUID,
    body: CannedResponseUpdate,
    request: Request,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    response = await db.get(CannedResponse, response_id)
    if not response or response.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Canned response not found")
    # Owner check for personal responses
    if response.visibility == CannedVisibility.user and response.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot edit another user's personal response")

    old = {"shortcut": response.shortcut, "title": response.title, "active": response.active}
    payload = body.model_dump(exclude_none=True)
    if "attachments" in payload and payload["attachments"] is not None:
        payload["attachments"] = [
            a if isinstance(a, dict) else a.model_dump() for a in payload["attachments"]
        ]
    for field, value in payload.items():
        setattr(response, field, value)
    try:
        await db.flush()
        await db.refresh(response)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Shortcut already in use")
    await log_security_event(
        action="canned_response_updated",
        workspace_id=workspace_id,
        user_id=current_user.id,
        target_type="canned_response",
        target_id=response.id,
        old_value=old,
        new_value={"shortcut": response.shortcut, "title": response.title, "active": response.active},
        ip_address=client_ip(request),
        user_agent=user_agent(request),
    )
    return response


@router.delete("/{response_id}", status_code=204)
async def delete_canned_response(
    workspace_id: UUID,
    response_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    response = await db.get(CannedResponse, response_id)
    if not response or response.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Canned response not found")
    if response.visibility == CannedVisibility.user and response.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete another user's personal response")
    old = {"shortcut": response.shortcut, "title": response.title}
    await db.delete(response)
    await log_security_event(
        action="canned_response_deleted",
        workspace_id=workspace_id,
        user_id=current_user.id,
        target_type="canned_response",
        target_id=response_id,
        old_value=old,
        ip_address=client_ip(request),
        user_agent=user_agent(request),
    )


class RenderRequest(BaseModel):
    conversation_id: UUID | None = None


class RenderResponse(BaseModel):
    content: str
    context: dict[str, str]


@router.post("/{response_id}/render", response_model=RenderResponse)
async def render_canned(
    workspace_id: UUID,
    response_id: UUID,
    body: RenderRequest,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    response = await db.get(CannedResponse, response_id)
    if not response or response.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Canned response not found")
    context = await build_render_context(
        db,
        workspace_id=workspace_id,
        conversation_id=body.conversation_id,
        agent=current_user,
    )
    return RenderResponse(content=render_template(response.content, context), context=context)
