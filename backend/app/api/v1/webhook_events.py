"""Admin endpoints for inspecting and replaying durable webhook events."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles, require_workspace_member
from app.models.enums import WebhookEventStatus
from app.models.webhook import WebhookEvent
from app.models.workspace import User
from app.schemas.webhook import WebhookEventDetail, WebhookEventOut, WebhookRetryResult
from app.services.webhook_retry import manual_retry

router = APIRouter(prefix="/workspaces/{workspace_id}/webhook-events", tags=["webhook-events"])


@router.get("", response_model=dict)
async def list_events(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin", "supervisor"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: WebhookEventStatus | None = Query(None),
    provider: str | None = Query(None),
    channel_account_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    q = select(WebhookEvent).where(WebhookEvent.workspace_id == workspace_id)
    if status:
        q = q.where(WebhookEvent.status == status)
    if provider:
        q = q.where(WebhookEvent.provider == provider)
    if channel_account_id:
        q = q.where(WebhookEvent.channel_account_id == channel_account_id)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    q = q.order_by(WebhookEvent.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(q)).scalars().all()
    return {
        "items": [WebhookEventOut.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/stats", response_model=dict)
async def stats(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin", "supervisor"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    q = (
        select(WebhookEvent.status, func.count())
        .where(WebhookEvent.workspace_id == workspace_id)
        .group_by(WebhookEvent.status)
    )
    rows = (await db.execute(q)).all()
    out = {s.value: 0 for s in WebhookEventStatus}
    for status_val, count in rows:
        out[status_val.value if hasattr(status_val, "value") else str(status_val)] = int(count)
    return out


@router.get("/{event_id}", response_model=WebhookEventDetail)
async def get_event(
    workspace_id: UUID,
    event_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin", "supervisor"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    event = await db.get(WebhookEvent, event_id)
    if not event or event.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("/{event_id}/retry", response_model=WebhookRetryResult)
async def retry_event(
    workspace_id: UUID,
    event_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin", "supervisor"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    event = await db.get(WebhookEvent, event_id)
    if not event or event.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Event not found")
    ok, err = await manual_retry(event_id)
    return WebhookRetryResult(success=ok, error=err)
