"""Stage 9 extras endpoints: holidays, SLA override, conversation locks,
notification channels, outbound webhooks, CSAT, idle rules, heatmap."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles, require_workspace_member
from app.core.encryption import encrypt_payload
from app.core.request_meta import client_ip, user_agent
from app.models.conversation import Conversation
from app.models.sla import SlaPolicy
from app.models.stage9_extras import (
    BusinessHoliday,
    ExternalWebhookDelivery,
    ExternalWebhookSubscription,
    IdleRule,
    NotificationChannel,
    NotificationDelivery,
)
from app.models.workspace import User
from app.schemas.stage9_extras import (
    BusinessHolidayCreate,
    BusinessHolidayOut,
    ConversationLockOut,
    ConversationLockRequest,
    ConversationSlaOverrideRequest,
    ExternalWebhookDeliveryOut,
    ExternalWebhookSubscriptionIn,
    ExternalWebhookSubscriptionOut,
    HeatmapOut,
    IdleRuleIn,
    IdleRuleOut,
    NotificationChannelIn,
    NotificationChannelOut,
    NotificationDeliveryOut,
)
from app.services.conversation_lock import acquire_lock, get_lock, release_lock
from app.services.heatmap_service import build_heatmap
from app.services.security_audit_service import log_security_event

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["stage9-extras"])


# ── Business holidays ──────────────────────────────────────────────────────

@router.get("/business-holidays", response_model=list[BusinessHolidayOut])
async def list_holidays(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(BusinessHoliday)
        .where(BusinessHoliday.workspace_id == workspace_id)
        .order_by(BusinessHoliday.holiday_date.asc())
    )
    return result.scalars().all()


@router.post("/business-holidays", response_model=BusinessHolidayOut, status_code=201)
async def create_holiday(
    workspace_id: UUID,
    body: BusinessHolidayCreate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    holiday = BusinessHoliday(workspace_id=workspace_id, **body.model_dump())
    db.add(holiday)
    await db.flush()
    await db.refresh(holiday)
    return holiday


@router.delete("/business-holidays/{holiday_id}", status_code=204)
async def delete_holiday(
    workspace_id: UUID,
    holiday_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    holiday = await db.get(BusinessHoliday, holiday_id)
    if not holiday or holiday.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Holiday not found")
    await db.delete(holiday)


# ── SLA override per conversation ──────────────────────────────────────────

@router.put("/conversations/{conversation_id}/sla-override")
async def set_conversation_sla_override(
    workspace_id: UUID,
    conversation_id: UUID,
    body: ConversationSlaOverrideRequest,
    request: Request,
    current_user: Annotated[User, Depends(require_roles("admin", "supervisor"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    conv = await db.get(Conversation, conversation_id)
    if not conv or conv.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if body.sla_policy_override_id:
        policy = await db.get(SlaPolicy, body.sla_policy_override_id)
        if not policy or policy.workspace_id != workspace_id or not policy.active:
            raise HTTPException(status_code=400, detail="Invalid policy")
    conv.sla_policy_override_id = body.sla_policy_override_id
    await db.flush()
    await log_security_event(
        action="conversation_sla_override",
        workspace_id=workspace_id,
        user_id=current_user.id,
        target_type="conversation",
        target_id=conv.id,
        new_value={"override_id": str(body.sla_policy_override_id) if body.sla_policy_override_id else None},
        ip_address=client_ip(request),
        user_agent=user_agent(request),
    )
    return {"ok": True, "override_id": body.sla_policy_override_id}


# ── Conversation locks ─────────────────────────────────────────────────────

@router.get("/conversations/{conversation_id}/lock", response_model=ConversationLockOut | None)
async def fetch_lock(
    workspace_id: UUID,
    conversation_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    lock = await get_lock(db, conversation_id)
    if not lock:
        return None
    if lock.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    holder = await db.get(User, lock.holder_user_id)
    return ConversationLockOut.model_validate(lock).model_copy(
        update={"holder_name": holder.name if holder else None}
    )


@router.post("/conversations/{conversation_id}/lock", response_model=ConversationLockOut)
async def acquire_conversation_lock(
    workspace_id: UUID,
    conversation_id: UUID,
    body: ConversationLockRequest,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    conv = await db.get(Conversation, conversation_id)
    if not conv or conv.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    lock, err = await acquire_lock(
        db,
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        user_id=current_user.id,
        ttl_seconds=body.ttl_seconds,
    )
    if not lock:
        raise HTTPException(status_code=409, detail=err or "locked")
    return ConversationLockOut.model_validate(lock).model_copy(
        update={"holder_name": current_user.name}
    )


@router.delete("/conversations/{conversation_id}/lock", status_code=204)
async def release_conversation_lock(
    workspace_id: UUID,
    conversation_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    lock = await get_lock(db, conversation_id)
    if lock and lock.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await release_lock(db, conversation_id, current_user.id)


# ── Idle rules ─────────────────────────────────────────────────────────────

@router.get("/idle-rule", response_model=IdleRuleOut | None)
async def get_idle_rule(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(IdleRule).where(IdleRule.workspace_id == workspace_id)
    )
    return result.scalar_one_or_none()


@router.put("/idle-rule", response_model=IdleRuleOut)
async def upsert_idle_rule(
    workspace_id: UUID,
    body: IdleRuleIn,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(IdleRule).where(IdleRule.workspace_id == workspace_id)
    )
    rule = result.scalar_one_or_none()
    if rule:
        for field, value in body.model_dump().items():
            setattr(rule, field, value)
    else:
        rule = IdleRule(workspace_id=workspace_id, **body.model_dump())
        db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return rule


# ── Notification channels ──────────────────────────────────────────────────

@router.get("/notification-channels", response_model=list[NotificationChannelOut])
async def list_notification_channels(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin", "supervisor"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(NotificationChannel)
        .where(NotificationChannel.workspace_id == workspace_id)
        .order_by(NotificationChannel.name.asc())
    )
    return result.scalars().all()


@router.post("/notification-channels", response_model=NotificationChannelOut, status_code=201)
async def create_notification_channel(
    workspace_id: UUID,
    body: NotificationChannelIn,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = NotificationChannel(workspace_id=workspace_id, **body.model_dump())
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


@router.patch("/notification-channels/{channel_id}", response_model=NotificationChannelOut)
async def update_notification_channel(
    workspace_id: UUID,
    channel_id: UUID,
    body: NotificationChannelIn,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(NotificationChannel, channel_id)
    if not row or row.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Channel not found")
    for field, value in body.model_dump().items():
        setattr(row, field, value)
    await db.flush()
    await db.refresh(row)
    return row


@router.delete("/notification-channels/{channel_id}", status_code=204)
async def delete_notification_channel(
    workspace_id: UUID,
    channel_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(NotificationChannel, channel_id)
    if not row or row.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Channel not found")
    await db.delete(row)


# ── Per-user in-app notification inbox ─────────────────────────────────────

@router.get("/notifications", response_model=dict)
async def list_notifications(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    unread: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    q = select(NotificationDelivery).where(
        NotificationDelivery.workspace_id == workspace_id,
        NotificationDelivery.user_id == current_user.id,
    )
    if unread is True:
        q = q.where(NotificationDelivery.read_at.is_(None))
    q = q.order_by(NotificationDelivery.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(q)).scalars().all()
    unread_q = await db.execute(
        select(NotificationDelivery).where(
            NotificationDelivery.workspace_id == workspace_id,
            NotificationDelivery.user_id == current_user.id,
            NotificationDelivery.read_at.is_(None),
        )
    )
    return {
        "items": [NotificationDeliveryOut.model_validate(item) for item in items],
        "unread_count": len(unread_q.scalars().all()),
    }


@router.post("/notifications/read", status_code=204)
async def mark_notifications_read(
    workspace_id: UUID,
    body: dict,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.notifier import mark_read

    ids = body.get("ids")
    await mark_read(db, workspace_id, current_user.id, ids)


# ── Outbound webhook subscriptions ─────────────────────────────────────────

@router.get("/api-webhooks", response_model=list[ExternalWebhookSubscriptionOut])
async def list_external_subs(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(ExternalWebhookSubscription)
        .where(ExternalWebhookSubscription.workspace_id == workspace_id)
        .order_by(ExternalWebhookSubscription.name.asc())
    )
    return result.scalars().all()


@router.post("/api-webhooks", response_model=ExternalWebhookSubscriptionOut, status_code=201)
async def create_external_sub(
    workspace_id: UUID,
    body: ExternalWebhookSubscriptionIn,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    import secrets

    secret = body.secret or secrets.token_urlsafe(32)
    sub = ExternalWebhookSubscription(
        workspace_id=workspace_id,
        name=body.name,
        url=body.url,
        secret=encrypt_payload({"secret": secret}),
        events=body.events,
        active=body.active,
    )
    db.add(sub)
    await db.flush()
    await db.refresh(sub)
    return sub


@router.delete("/api-webhooks/{sub_id}", status_code=204)
async def delete_external_sub(
    workspace_id: UUID,
    sub_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    sub = await db.get(ExternalWebhookSubscription, sub_id)
    if not sub or sub.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Subscription not found")
    await db.delete(sub)


@router.get("/api-webhooks/{sub_id}/deliveries", response_model=list[ExternalWebhookDeliveryOut])
async def list_external_deliveries(
    workspace_id: UUID,
    sub_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(50, ge=1, le=200),
):
    sub = await db.get(ExternalWebhookSubscription, sub_id)
    if not sub or sub.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Subscription not found")
    result = await db.execute(
        select(ExternalWebhookDelivery)
        .where(ExternalWebhookDelivery.subscription_id == sub_id)
        .order_by(ExternalWebhookDelivery.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


# ── CSAT ───────────────────────────────────────────────────────────────────

@router.get("/csat", response_model=dict)
async def list_csat(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin", "supervisor"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    only_responded: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    from app.models.stage9_extras import CsatSurvey

    q = select(CsatSurvey).where(CsatSurvey.workspace_id == workspace_id)
    if only_responded:
        q = q.where(CsatSurvey.score.is_not(None))
    q = q.order_by(CsatSurvey.sent_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(q)).scalars().all()
    avg = None
    if items:
        scored = [it.score for it in items if it.score is not None]
        if scored:
            avg = round(sum(scored) / len(scored), 2)
    return {
        "items": [
            {
                "id": str(it.id),
                "conversation_id": str(it.conversation_id),
                "assignee_id": str(it.assignee_id) if it.assignee_id else None,
                "score": it.score,
                "feedback": it.feedback,
                "sent_at": it.sent_at.isoformat(),
                "responded_at": it.responded_at.isoformat() if it.responded_at else None,
            }
            for it in items
        ],
        "average_score": avg,
    }


# ── Supervisor heatmap ─────────────────────────────────────────────────────

@router.get("/supervisor/heatmap", response_model=HeatmapOut)
async def heatmap(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin", "supervisor"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(7, ge=1, le=90),
):
    data = await build_heatmap(db, workspace_id, days=days)
    return HeatmapOut(days=data["days"], cells=data["cells"])
