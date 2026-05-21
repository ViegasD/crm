from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_workspace_member
from app.core.request_meta import client_ip, user_agent
from app.models.conversation import CannedResponse
from app.models.workspace import User
from app.schemas.canned_response import (
    CannedResponseCreate,
    CannedResponseOut,
    CannedResponseUpdate,
)
from app.services.canned_response_service import build_render_context, render_template
from app.services.security_audit_service import log_security_event

router = APIRouter(prefix="/workspaces/{workspace_id}/canned-responses", tags=["canned-responses"])


@router.post("", response_model=CannedResponseOut, status_code=201)
async def create_canned_response(
    workspace_id: UUID,
    body: CannedResponseCreate,
    request: Request,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    response = CannedResponse(workspace_id=workspace_id, **body.model_dump())
    db.add(response)
    try:
        await db.flush()
        await db.refresh(response)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Canned response shortcut already exists")
    await log_security_event(
        action="canned_response_created",
        workspace_id=workspace_id,
        user_id=current_user.id,
        target_type="canned_response",
        target_id=response.id,
        new_value={"shortcut": response.shortcut, "title": response.title},
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
):
    q = select(CannedResponse).where(CannedResponse.workspace_id == workspace_id)
    if active is not None:
        q = q.where(CannedResponse.active.is_(active))
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
    old = {"shortcut": response.shortcut, "title": response.title, "active": response.active}
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(response, field, value)
    try:
        await db.flush()
        await db.refresh(response)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Canned response shortcut already exists")
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
