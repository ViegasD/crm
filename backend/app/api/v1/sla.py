from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_workspace_member
from app.models.conversation import Conversation
from app.models.sla import (
    AgentCapacity,
    AgentPauseReason,
    AgentStatus,
    AutoResolveRule,
    BusinessHours,
    RoutingRule,
    SlaEscalationRule,
    SlaEvent,
    SlaPolicy,
)
from app.models.workspace import User
from app.schemas.sla import (
    AgentCapacityOut,
    AgentCapacitySet,
    AgentPauseReasonCreate,
    AgentPauseReasonOut,
    AgentStatusOut,
    AgentStatusSet,
    AssignmentRequest,
    AssignmentResult,
    BusinessHoursIn,
    BusinessHoursOut,
    RoutingRuleIn,
    RoutingRuleOut,
    SlaEscalationRuleIn,
    SlaEscalationRuleOut,
    SlaEventOut,
    SlaPolicyCreate,
    SlaPolicyOut,
    SlaPolicyUpdate,
    SupervisorOverview,
)
from app.services.sla_service import (
    assign_conversation_if_needed,
    evaluate_workspace_sla,
    set_agent_status,
    supervisor_overview,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/sla", tags=["sla"])


async def _agent_status_out(db: AsyncSession, status: AgentStatus) -> AgentStatusOut:
    user = await db.get(User, status.user_id)
    reason = await db.get(AgentPauseReason, status.reason_id) if status.reason_id else None
    return AgentStatusOut.model_validate(status).model_copy(
        update={
            "user_name": user.name if user else None,
            "user_email": user.email if user else None,
            "reason_label": reason.label if reason else None,
        }
    )


@router.post("/policies", response_model=SlaPolicyOut, status_code=201)
async def create_policy(
    workspace_id: UUID,
    body: SlaPolicyCreate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    policy = SlaPolicy(workspace_id=workspace_id, **body.model_dump())
    db.add(policy)
    await db.flush()
    return policy


@router.get("/policies", response_model=list[SlaPolicyOut])
async def list_policies(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(SlaPolicy)
        .where(SlaPolicy.workspace_id == workspace_id)
        .order_by(SlaPolicy.active.desc(), SlaPolicy.name.asc())
    )
    return result.scalars().all()


@router.patch("/policies/{policy_id}", response_model=SlaPolicyOut)
async def update_policy(
    workspace_id: UUID,
    policy_id: UUID,
    body: SlaPolicyUpdate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    policy = await db.get(SlaPolicy, policy_id)
    if not policy or policy.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Policy not found")
    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(policy, field, val)
    await db.flush()
    await db.refresh(policy)
    return policy


@router.delete("/policies/{policy_id}", status_code=204)
async def delete_policy(
    workspace_id: UUID,
    policy_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    policy = await db.get(SlaPolicy, policy_id)
    if not policy or policy.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Policy not found")
    await db.delete(policy)


@router.get("/policies/{policy_id}/escalations", response_model=list[SlaEscalationRuleOut])
async def list_escalations(
    workspace_id: UUID,
    policy_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    policy = await db.get(SlaPolicy, policy_id)
    if not policy or policy.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Policy not found")
    result = await db.execute(
        select(SlaEscalationRule)
        .where(SlaEscalationRule.workspace_id == workspace_id, SlaEscalationRule.policy_id == policy_id)
        .order_by(SlaEscalationRule.threshold_pct.asc(), SlaEscalationRule.position.asc())
    )
    return result.scalars().all()


@router.put("/policies/{policy_id}/escalations", response_model=list[SlaEscalationRuleOut])
async def replace_escalations(
    workspace_id: UUID,
    policy_id: UUID,
    body: list[SlaEscalationRuleIn],
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    policy = await db.get(SlaPolicy, policy_id)
    if not policy or policy.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Policy not found")
    await db.execute(
        sa_delete(SlaEscalationRule).where(
            SlaEscalationRule.workspace_id == workspace_id,
            SlaEscalationRule.policy_id == policy_id,
        )
    )
    rows = [
        SlaEscalationRule(
            workspace_id=workspace_id,
            policy_id=policy_id,
            **item.model_dump(),
        )
        for item in body[:3]
    ]
    db.add_all(rows)
    await db.flush()
    return rows


@router.put("/capacity", response_model=AgentCapacityOut)
async def set_capacity(
    workspace_id: UUID,
    body: AgentCapacitySet,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(AgentCapacity).where(
            AgentCapacity.workspace_id == workspace_id,
            AgentCapacity.user_id == body.user_id,
        )
    )
    cap = result.scalar_one_or_none()
    data = body.model_dump(exclude_unset=True)
    max_weight = data.pop("max_weight", None)
    priority_weights = data.pop("priority_weights", None)
    if cap:
        cap.max_conversations = body.max_conversations
        cap.sector_id = body.sector_id
        if max_weight is not None:
            cap.max_weight = max_weight
        if priority_weights is not None:
            cap.priority_weights = priority_weights
    else:
        cap = AgentCapacity(
            workspace_id=workspace_id,
            user_id=body.user_id,
            max_conversations=body.max_conversations,
            max_weight=max_weight if max_weight is not None else float(body.max_conversations),
            sector_id=body.sector_id,
            priority_weights=priority_weights or {},
        )
        db.add(cap)
    await db.flush()
    await db.refresh(cap)
    return cap


@router.get("/capacity", response_model=list[AgentCapacityOut])
async def list_capacity(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(AgentCapacity).where(AgentCapacity.workspace_id == workspace_id)
    )
    return result.scalars().all()


@router.get("/pause-reasons", response_model=list[AgentPauseReasonOut])
async def list_pause_reasons(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(AgentPauseReason)
        .where(AgentPauseReason.workspace_id == workspace_id)
        .order_by(AgentPauseReason.position.asc(), AgentPauseReason.label.asc())
    )
    return result.scalars().all()


@router.post("/pause-reasons", response_model=AgentPauseReasonOut, status_code=201)
async def create_pause_reason(
    workspace_id: UUID,
    body: AgentPauseReasonCreate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    reason = AgentPauseReason(workspace_id=workspace_id, **body.model_dump())
    db.add(reason)
    await db.flush()
    return reason


@router.get("/agent-status", response_model=list[AgentStatusOut])
async def list_agent_status(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(AgentStatus)
        .where(AgentStatus.workspace_id == workspace_id)
        .order_by(AgentStatus.updated_at.desc())
    )
    rows = result.scalars().all()
    return [await _agent_status_out(db, row) for row in rows]


@router.put("/agent-status/{user_id}", response_model=AgentStatusOut)
async def update_agent_status(
    workspace_id: UUID,
    user_id: UUID,
    body: AgentStatusSet,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.reason_id:
        reason = await db.get(AgentPauseReason, body.reason_id)
        if not reason or reason.workspace_id != workspace_id:
            raise HTTPException(status_code=400, detail="Invalid pause reason")
    row = await set_agent_status(
        db,
        workspace_id,
        user_id,
        body.status,
        body.reason_id,
        body.note,
        current_user.id,
    )
    return await _agent_status_out(db, row)


@router.get("/business-hours", response_model=list[BusinessHoursOut])
async def list_business_hours(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    sector_id: UUID | None = None,
):
    q = select(BusinessHours).where(BusinessHours.workspace_id == workspace_id)
    if sector_id:
        q = q.where(BusinessHours.sector_id == sector_id)
    result = await db.execute(q.order_by(BusinessHours.sector_id.asc(), BusinessHours.weekday.asc(), BusinessHours.start_minute.asc()))
    return result.scalars().all()


@router.post("/business-hours", response_model=BusinessHoursOut, status_code=201)
async def create_business_hours(
    workspace_id: UUID,
    body: BusinessHoursIn,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if body.weekday < 0 or body.weekday > 6:
        raise HTTPException(status_code=400, detail="weekday must be 0..6")
    if body.start_minute < 0 or body.end_minute > 24 * 60 or body.start_minute >= body.end_minute:
        raise HTTPException(status_code=400, detail="Invalid business hour interval")
    row = BusinessHours(workspace_id=workspace_id, **body.model_dump())
    db.add(row)
    await db.flush()
    return row


@router.delete("/business-hours/{hours_id}", status_code=204)
async def delete_business_hours(
    workspace_id: UUID,
    hours_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(BusinessHours, hours_id)
    if not row or row.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Business hours not found")
    await db.delete(row)


@router.get("/routing-rules", response_model=list[RoutingRuleOut])
async def list_routing_rules(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(RoutingRule)
        .where(RoutingRule.workspace_id == workspace_id)
        .order_by(RoutingRule.sector_id.asc())
    )
    return result.scalars().all()


@router.put("/routing-rules", response_model=RoutingRuleOut)
async def upsert_routing_rule(
    workspace_id: UUID,
    body: RoutingRuleIn,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(RoutingRule).where(
            RoutingRule.workspace_id == workspace_id,
            RoutingRule.sector_id == body.sector_id,
        )
    )
    rule = result.scalar_one_or_none()
    if rule:
        for field, value in body.model_dump().items():
            setattr(rule, field, value)
    else:
        rule = RoutingRule(workspace_id=workspace_id, **body.model_dump())
        db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return rule


@router.post("/assign-next", response_model=AssignmentResult)
async def assign_next(
    workspace_id: UUID,
    body: AssignmentRequest,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    conv = await db.get(Conversation, body.conversation_id)
    if not conv or conv.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if body.sector_id:
        conv.sector_id = body.sector_id
    conv, assigned, reason = await assign_conversation_if_needed(
        db,
        conv,
        method="manual_dispatch",
        assigned_by=current_user.id,
    )
    return AssignmentResult(
        conversation_id=conv.id,
        assignee_id=conv.assignee_id,
        assigned=assigned,
        reason=reason,
    )


@router.post("/evaluate", response_model=dict)
async def evaluate_sla(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    count = await evaluate_workspace_sla(db, workspace_id)
    return {"evaluated": count}


@router.get("/events", response_model=list[SlaEventOut])
async def list_sla_events(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conversation_id: UUID | None = None,
):
    q = select(SlaEvent).where(SlaEvent.workspace_id == workspace_id)
    if conversation_id:
        q = q.where(SlaEvent.conversation_id == conversation_id)
    result = await db.execute(q.order_by(SlaEvent.created_at.desc()).limit(200))
    return result.scalars().all()


@router.get("/supervisor/overview", response_model=SupervisorOverview)
async def get_supervisor_overview(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await supervisor_overview(db, workspace_id)


# ── Pause reason update/delete (POST/GET already exist) ─────────────────────

from app.schemas.stage9_extras import (
    AutoResolveRuleCreate,
    AutoResolveRuleOut,
    AutoResolveRuleUpdate,
    PauseReasonUpdate,
)


@router.patch("/pause-reasons/{reason_id}", response_model=AgentPauseReasonOut)
async def update_pause_reason(
    workspace_id: UUID,
    reason_id: UUID,
    body: PauseReasonUpdate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    reason = await db.get(AgentPauseReason, reason_id)
    if not reason or reason.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Pause reason not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(reason, field, value)
    await db.flush()
    await db.refresh(reason)
    return reason


@router.delete("/pause-reasons/{reason_id}", status_code=204)
async def delete_pause_reason(
    workspace_id: UUID,
    reason_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    reason = await db.get(AgentPauseReason, reason_id)
    if not reason or reason.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Pause reason not found")
    await db.delete(reason)


# ── Auto-resolve rules ─────────────────────────────────────────────────────

@router.get("/auto-resolve-rules", response_model=list[AutoResolveRuleOut])
async def list_auto_resolve(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(AutoResolveRule)
        .where(AutoResolveRule.workspace_id == workspace_id)
        .order_by(AutoResolveRule.sector_id.asc())
    )
    return result.scalars().all()


@router.post("/auto-resolve-rules", response_model=AutoResolveRuleOut, status_code=201)
async def create_auto_resolve(
    workspace_id: UUID,
    body: AutoResolveRuleCreate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rule = AutoResolveRule(workspace_id=workspace_id, **body.model_dump())
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return rule


@router.patch("/auto-resolve-rules/{rule_id}", response_model=AutoResolveRuleOut)
async def update_auto_resolve(
    workspace_id: UUID,
    rule_id: UUID,
    body: AutoResolveRuleUpdate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rule = await db.get(AutoResolveRule, rule_id)
    if not rule or rule.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Rule not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(rule, field, value)
    await db.flush()
    await db.refresh(rule)
    return rule


@router.delete("/auto-resolve-rules/{rule_id}", status_code=204)
async def delete_auto_resolve(
    workspace_id: UUID,
    rule_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rule = await db.get(AutoResolveRule, rule_id)
    if not rule or rule.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)


# ── Business hours bulk update (week grid editor) ──────────────────────────

@router.put("/business-hours", response_model=list[BusinessHoursOut])
async def replace_business_hours(
    workspace_id: UUID,
    body: list[BusinessHoursIn],
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    sector_id: UUID | None = None,
):
    """Replace the full business-hours grid for workspace or for a sector.

    Pass `?sector_id=...` to replace just that sector's rows; without it the
    rows where sector_id IS NULL are replaced (workspace default).
    """
    await db.execute(
        sa_delete(BusinessHours).where(
            BusinessHours.workspace_id == workspace_id,
            BusinessHours.sector_id == sector_id,
        )
    )
    rows: list[BusinessHours] = []
    for item in body:
        if item.weekday < 0 or item.weekday > 6:
            raise HTTPException(status_code=400, detail="weekday must be 0..6")
        if item.start_minute < 0 or item.end_minute > 24 * 60 or item.start_minute >= item.end_minute:
            raise HTTPException(status_code=400, detail="Invalid business hour interval")
        rows.append(
            BusinessHours(
                workspace_id=workspace_id,
                sector_id=sector_id,
                weekday=item.weekday,
                start_minute=item.start_minute,
                end_minute=item.end_minute,
                timezone=item.timezone,
                active=item.active,
            )
        )
    db.add_all(rows)
    await db.flush()
    return rows
