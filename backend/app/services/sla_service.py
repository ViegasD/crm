from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import ConversationSnooze
from app.models.contact import Contact
from app.models.conversation import Conversation, ConversationEvent, Message
from app.models.enums import (
    ConvEventType,
    ConversationStatus,
    SenderType,
    SlaEventType,
    SlaStatus,
    UserStatus,
    WorkspaceRole,
)
from app.models.sla import (
    AgentCapacity,
    AgentPauseReason,
    AgentStatus,
    AgentStatusLog,
    BusinessHours,
    ConversationAssignment,
    RoutingRule,
    SlaEscalationRule,
    SlaEvent,
    SlaPolicy,
)
from app.models.stage9_extras import BusinessHoliday
from app.models.workspace import Sector, SectorMember, User, UserWorkspaceMembership
from app.websocket.manager import manager

ASSIGNABLE_STATUSES = {"online"}
REDISTRIBUTE_STATUSES = {"away", "on_break", "offline", "invisible"}
ACTIVE_CONVERSATION_STATUSES = [ConversationStatus.open, ConversationStatus.in_progress]
DEFAULT_PRIORITY_WEIGHTS = {"low": 0.75, "medium": 1.0, "high": 1.5, "urgent": 2.0}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _enum_value(value) -> str:
    return getattr(value, "value", str(value))


def _conversation_weight(conv: Conversation, weights: dict | None = None) -> float:
    merged = {**DEFAULT_PRIORITY_WEIGHTS, **(weights or {})}
    weight = float(merged.get(_enum_value(conv.priority), 1.0))
    if conv.status == ConversationStatus.pending:
        weight *= 0.5
    return weight


async def _broadcast(workspace_id: UUID, payload: dict) -> None:
    await manager.broadcast(str(workspace_id), payload)


async def _get_routing_rule(
    db: AsyncSession, workspace_id: UUID, sector_id: UUID | None
) -> RoutingRule | None:
    if sector_id:
        result = await db.execute(
            select(RoutingRule).where(
                RoutingRule.workspace_id == workspace_id,
                RoutingRule.sector_id == sector_id,
            )
        )
        rule = result.scalar_one_or_none()
        if rule:
            return rule
    result = await db.execute(
        select(RoutingRule).where(
            RoutingRule.workspace_id == workspace_id,
            RoutingRule.sector_id.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def reopen_recent_resolved_conversation(
    db: AsyncSession,
    workspace_id: UUID,
    channel_account_id: UUID,
    contact_id: UUID,
    sector_id: UUID | None,
) -> Conversation | None:
    rule = await _get_routing_rule(db, workspace_id, sector_id)
    reopen_hours = rule.reopen_window_hours if rule else 24
    since = _now() - timedelta(hours=reopen_hours)
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.workspace_id == workspace_id,
            Conversation.channel_account_id == channel_account_id,
            Conversation.contact_id == contact_id,
            Conversation.status == ConversationStatus.resolved,
            Conversation.resolved_at.is_not(None),
            Conversation.resolved_at >= since,
        )
        .order_by(Conversation.resolved_at.desc())
        .limit(1)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        return None

    conv.status = ConversationStatus.open
    conv.resolved_at = None
    conv.resolve_note = None
    db.add(
        ConversationEvent(
            workspace_id=workspace_id,
            conversation_id=conv.id,
            type=ConvEventType.reopened,
            actor_type="system",
            payload={"reason": "inbound_within_reopen_window", "window_hours": reopen_hours},
        )
    )
    await db.flush()
    return conv


async def _agent_candidates(
    db: AsyncSession,
    workspace_id: UUID,
    sector_id: UUID | None,
    exclude_user_id: UUID | None = None,
) -> list[dict]:
    result = await db.execute(
        select(User, UserWorkspaceMembership, AgentStatus, AgentPauseReason, AgentCapacity)
        .join(UserWorkspaceMembership, UserWorkspaceMembership.user_id == User.id)
        .outerjoin(
            AgentStatus,
            (AgentStatus.workspace_id == workspace_id) & (AgentStatus.user_id == User.id),
        )
        .outerjoin(AgentPauseReason, AgentPauseReason.id == AgentStatus.reason_id)
        .outerjoin(
            AgentCapacity,
            (AgentCapacity.workspace_id == workspace_id) & (AgentCapacity.user_id == User.id),
        )
        .where(
            UserWorkspaceMembership.workspace_id == workspace_id,
            UserWorkspaceMembership.role.in_([WorkspaceRole.agent, WorkspaceRole.supervisor]),
        )
    )
    rows = result.all()

    sector_members: set[UUID] | None = None
    if sector_id:
        member_result = await db.execute(
            select(SectorMember.user_id).where(
                SectorMember.workspace_id == workspace_id,
                SectorMember.sector_id == sector_id,
            )
        )
        sector_members = {row[0] for row in member_result.all()}

    conversations = (
        await db.execute(
            select(Conversation).where(
                Conversation.workspace_id == workspace_id,
                Conversation.assignee_id.is_not(None),
                Conversation.status.in_(ACTIVE_CONVERSATION_STATUSES),
            )
        )
    ).scalars().all()
    by_agent: dict[UUID, list[Conversation]] = defaultdict(list)
    for conv in conversations:
        if conv.assignee_id:
            by_agent[conv.assignee_id].append(conv)

    candidates: list[dict] = []
    for user, membership, status, reason, capacity in rows:
        if exclude_user_id and user.id == exclude_user_id:
            continue
        if sector_members is not None and user.id not in sector_members:
            continue
        effective_status = status.status if status else _enum_value(user.status)
        if effective_status not in ASSIGNABLE_STATUSES:
            continue
        if capacity and capacity.sector_id and sector_id and capacity.sector_id != sector_id:
            continue

        max_conversations = capacity.max_conversations if capacity else 10
        max_weight = capacity.max_weight if capacity else float(max_conversations)
        weights = capacity.priority_weights if capacity else {}
        assigned = by_agent.get(user.id, [])
        weighted_load = sum(_conversation_weight(conv, weights) for conv in assigned)
        if len(assigned) >= max_conversations or weighted_load >= max_weight:
            continue

        candidates.append(
            {
                "user": user,
                "role": membership.role,
                "status": status,
                "reason": reason,
                "capacity": capacity,
                "assigned_count": len(assigned),
                "weighted_load": weighted_load,
                "max_conversations": max_conversations,
                "max_weight": max_weight,
            }
        )
    return candidates


async def _sticky_candidate(
    db: AsyncSession,
    conversation: Conversation,
    candidates: list[dict],
    sticky_hours: int,
) -> dict | None:
    if not candidates or sticky_hours <= 0:
        return None
    candidate_ids = {c["user"].id for c in candidates}
    since = _now() - timedelta(hours=sticky_hours)
    result = await db.execute(
        select(ConversationAssignment.user_id)
        .join(Conversation, Conversation.id == ConversationAssignment.conversation_id)
        .where(
            Conversation.workspace_id == conversation.workspace_id,
            Conversation.contact_id == conversation.contact_id,
            ConversationAssignment.user_id.in_(candidate_ids),
            ConversationAssignment.assigned_at >= since,
        )
        .order_by(ConversationAssignment.assigned_at.desc())
        .limit(1)
    )
    sticky_user_id = result.scalar_one_or_none()
    if not sticky_user_id:
        return None
    return next((c for c in candidates if c["user"].id == sticky_user_id), None)


async def _round_robin_candidate(db: AsyncSession, candidates: list[dict]) -> dict | None:
    if not candidates:
        return None
    candidate_ids = [c["user"].id for c in candidates]
    result = await db.execute(
        select(ConversationAssignment.user_id, func.max(ConversationAssignment.assigned_at))
        .where(ConversationAssignment.user_id.in_(candidate_ids))
        .group_by(ConversationAssignment.user_id)
    )
    last_by_user = {user_id: assigned_at for user_id, assigned_at in result.all()}
    distant_past = datetime(1970, 1, 1, tzinfo=timezone.utc)
    return min(candidates, key=lambda c: last_by_user.get(c["user"].id, distant_past))


async def choose_agent_for_conversation(
    db: AsyncSession,
    conversation: Conversation,
    exclude_user_id: UUID | None = None,
) -> tuple[User | None, str]:
    rule = await _get_routing_rule(db, conversation.workspace_id, conversation.sector_id)
    strategy = rule.strategy if rule else "least_busy"
    if strategy == "manual":
        return None, "manual_routing"

    candidates = await _agent_candidates(
        db,
        conversation.workspace_id,
        conversation.sector_id,
        exclude_user_id=exclude_user_id,
    )
    if not candidates:
        return None, "no_available_agent"

    if strategy == "sticky_agent":
        sticky = await _sticky_candidate(db, conversation, candidates, rule.sticky_hours if rule else 24)
        if sticky:
            return sticky["user"], "sticky_agent"
        return min(candidates, key=lambda c: (c["weighted_load"], c["assigned_count"]))["user"], "sticky_fallback"

    if strategy == "round_robin":
        candidate = await _round_robin_candidate(db, candidates)
        return candidate["user"], "round_robin"

    return min(candidates, key=lambda c: (c["weighted_load"], c["assigned_count"]))["user"], "least_busy"


async def assign_conversation_if_needed(
    db: AsyncSession,
    conversation: Conversation,
    method: str = "auto",
    assigned_by: UUID | None = None,
    exclude_user_id: UUID | None = None,
) -> tuple[Conversation, bool, str | None]:
    if conversation.assignee_id:
        return conversation, False, "already_assigned"

    user, reason = await choose_agent_for_conversation(db, conversation, exclude_user_id=exclude_user_id)
    if not user:
        return conversation, False, reason

    result = await db.execute(
        sa_update(Conversation)
        .where(
            Conversation.id == conversation.id,
            Conversation.workspace_id == conversation.workspace_id,
            Conversation.assignee_id.is_(None),
        )
        .values(assignee_id=user.id, status=ConversationStatus.in_progress)
        .returning(Conversation.id)
        .execution_options(synchronize_session=False)
    )
    if not result.scalar_one_or_none():
        await db.refresh(conversation)
        return conversation, False, "already_claimed"

    await db.refresh(conversation)
    now = _now()
    db.add(
        ConversationAssignment(
            workspace_id=conversation.workspace_id,
            conversation_id=conversation.id,
            user_id=user.id,
            sector_id=conversation.sector_id,
            assigned_by=assigned_by,
            assigned_at=now,
            method=method,
            reason=reason,
        )
    )
    db.add(
        ConversationEvent(
            workspace_id=conversation.workspace_id,
            conversation_id=conversation.id,
            type=ConvEventType.assigned,
            actor_id=assigned_by,
            actor_type="system" if assigned_by is None else "agent",
            payload={"to": str(user.id), "method": method, "reason": reason},
        )
    )
    await db.flush()
    await _broadcast(
        conversation.workspace_id,
        {
            "type": "conversation.assigned",
            "conversation_id": str(conversation.id),
            "assignee_id": str(user.id),
            "method": method,
        },
    )
    return conversation, True, reason


async def record_manual_assignment(
    db: AsyncSession,
    conversation: Conversation,
    user_id: UUID | None,
    assigned_by: UUID | None,
    method: str,
    reason: str | None = None,
) -> None:
    now = _now()
    await db.execute(
        sa_update(ConversationAssignment)
        .where(
            ConversationAssignment.conversation_id == conversation.id,
            ConversationAssignment.unassigned_at.is_(None),
        )
        .values(unassigned_at=now)
        .execution_options(synchronize_session=False)
    )
    if user_id:
        db.add(
            ConversationAssignment(
                workspace_id=conversation.workspace_id,
                conversation_id=conversation.id,
                user_id=user_id,
                sector_id=conversation.sector_id,
                assigned_by=assigned_by,
                assigned_at=now,
                method=method,
                reason=reason,
            )
        )


async def set_agent_status(
    db: AsyncSession,
    workspace_id: UUID,
    user_id: UUID,
    status: str,
    reason_id: UUID | None,
    note: str | None,
    changed_by: UUID | None,
) -> AgentStatus:
    now = _now()
    result = await db.execute(
        select(AgentStatus).where(
            AgentStatus.workspace_id == workspace_id,
            AgentStatus.user_id == user_id,
        )
    )
    row = result.scalar_one_or_none()
    if row:
        changed = row.status != status or row.reason_id != reason_id or row.note != note
        row.status = status
        row.reason_id = reason_id
        row.note = note
        row.updated_by = changed_by
        if changed:
            row.since_at = now
    else:
        row = AgentStatus(
            workspace_id=workspace_id,
            user_id=user_id,
            status=status,
            reason_id=reason_id,
            note=note,
            since_at=now,
            updated_by=changed_by,
        )
        db.add(row)

    user = await db.get(User, user_id)
    if user:
        try:
            user.status = UserStatus(status)
        except ValueError:
            pass

    db.add(
        AgentStatusLog(
            workspace_id=workspace_id,
            user_id=user_id,
            status=status,
            reason_id=reason_id,
            note=note,
            changed_by=changed_by,
            changed_at=now,
        )
    )
    await db.flush()
    await _broadcast(workspace_id, {"type": "agent.status.updated", "user_id": str(user_id), "status": status})

    if status in REDISTRIBUTE_STATUSES:
        await redistribute_agent_conversations(db, workspace_id, user_id, reason=f"agent_{status}")
    return row


async def redistribute_agent_conversations(
    db: AsyncSession,
    workspace_id: UUID,
    user_id: UUID,
    reason: str,
) -> int:
    result = await db.execute(
        select(Conversation).where(
            Conversation.workspace_id == workspace_id,
            Conversation.assignee_id == user_id,
            Conversation.status.in_(ACTIVE_CONVERSATION_STATUSES),
        )
    )
    conversations = result.scalars().all()
    count = 0
    for conv in conversations:
        old = conv.assignee_id
        conv.assignee_id = None
        db.add(
            ConversationEvent(
                workspace_id=workspace_id,
                conversation_id=conv.id,
                type=ConvEventType.unassigned,
                actor_type="system",
                payload={"from": str(old), "reason": reason},
            )
        )
        await record_manual_assignment(db, conv, None, None, "auto_reassign", reason)
        await db.flush()
        await assign_conversation_if_needed(db, conv, method="auto_reassign", exclude_user_id=user_id)
        count += 1
    if count:
        await _broadcast(workspace_id, {"type": "supervisor.metrics.updated", "reason": reason})
    return count


async def _business_hours_rows(
    db: AsyncSession, workspace_id: UUID, sector_id: UUID | None
) -> list[BusinessHours]:
    if sector_id:
        result = await db.execute(
            select(BusinessHours).where(
                BusinessHours.workspace_id == workspace_id,
                BusinessHours.sector_id == sector_id,
                BusinessHours.active.is_(True),
            )
        )
        rows = result.scalars().all()
        if rows:
            return rows
    result = await db.execute(
        select(BusinessHours).where(
            BusinessHours.workspace_id == workspace_id,
            BusinessHours.sector_id.is_(None),
            BusinessHours.active.is_(True),
        )
    )
    rows = result.scalars().all()
    if rows:
        return rows

    rows = []
    for weekday in range(5):
        rows.append(
            BusinessHours(
                workspace_id=workspace_id,
                sector_id=None,
                weekday=weekday,
                start_minute=9 * 60,
                end_minute=18 * 60,
                timezone="America/Sao_Paulo",
                active=True,
            )
        )
    return rows


async def _business_holidays_rows(
    db: AsyncSession, workspace_id: UUID, sector_id: UUID | None
) -> list[BusinessHoliday]:
    q = select(BusinessHoliday).where(BusinessHoliday.workspace_id == workspace_id)
    if sector_id:
        q = q.where((BusinessHoliday.sector_id == sector_id) | (BusinessHoliday.sector_id.is_(None)))
    else:
        q = q.where(BusinessHoliday.sector_id.is_(None))
    result = await db.execute(q)
    return result.scalars().all()


def _hours_by_weekday(rows: list[BusinessHours]) -> tuple[str, dict[int, list[tuple[int, int]]]]:
    timezone_name = rows[0].timezone if rows else "America/Sao_Paulo"
    grouped: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row in rows:
        if row.active and row.end_minute > row.start_minute:
            grouped[row.weekday].append((row.start_minute, row.end_minute))
    for day in grouped:
        grouped[day].sort()
    return timezone_name, grouped


def _holiday_for_day(
    holidays: list[BusinessHoliday] | None,
    day: date,
    sector_id: UUID | None,
) -> BusinessHoliday | None:
    if not holidays:
        return None
    sector_match = None
    workspace_match = None
    for holiday in holidays:
        if holiday.holiday_date != day:
            continue
        if sector_id and holiday.sector_id == sector_id:
            sector_match = holiday
        elif holiday.sector_id is None:
            workspace_match = holiday
    return sector_match or workspace_match


def _apply_holiday(
    intervals: list[tuple[int, int]],
    holiday: BusinessHoliday | None,
) -> list[tuple[int, int]]:
    if not holiday:
        return intervals
    if holiday.treat_as == "closed":
        return []
    if holiday.treat_as == "custom":
        if holiday.custom_start_minute is None or holiday.custom_end_minute is None:
            return []
        if holiday.custom_end_minute <= holiday.custom_start_minute:
            return []
        return [(holiday.custom_start_minute, holiday.custom_end_minute)]
    if holiday.treat_as == "half_day" and intervals:
        start_minute = intervals[0][0]
        end_minute = intervals[-1][1]
        midpoint = start_minute + max((end_minute - start_minute) // 2, 1)
        return [(start_minute, midpoint)]
    return intervals


def add_business_minutes(
    start: datetime,
    minutes: int,
    rows: list[BusinessHours],
    business_only: bool,
    holidays: list[BusinessHoliday] | None = None,
    sector_id: UUID | None = None,
) -> datetime:
    if not business_only or minutes <= 0:
        return start + timedelta(minutes=max(minutes, 0))

    timezone_name, grouped = _hours_by_weekday(rows)
    tz = ZoneInfo(timezone_name)
    current = start.astimezone(tz)
    remaining = minutes

    for _ in range(370):
        holiday = _holiday_for_day(holidays, current.date(), sector_id)
        day_intervals = _apply_holiday(grouped.get(current.weekday(), []), holiday)
        minute_of_day = current.hour * 60 + current.minute
        for start_minute, end_minute in day_intervals:
            if minute_of_day > end_minute:
                continue
            if minute_of_day < start_minute:
                current = current.replace(
                    hour=start_minute // 60,
                    minute=start_minute % 60,
                    second=0,
                    microsecond=0,
                )
                minute_of_day = start_minute
            if start_minute <= minute_of_day < end_minute:
                available = end_minute - minute_of_day
                if remaining <= available:
                    return (current + timedelta(minutes=remaining)).astimezone(timezone.utc)
                remaining -= available
                current = current.replace(
                    hour=end_minute // 60,
                    minute=end_minute % 60,
                    second=0,
                    microsecond=0,
                )
                minute_of_day = end_minute
        next_day = (current + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        current = next_day
    return (start + timedelta(minutes=minutes)).astimezone(timezone.utc)


async def _select_policy(db: AsyncSession, conv: Conversation) -> SlaPolicy | None:
    if conv.sla_policy_override_id:
        override = await db.get(SlaPolicy, conv.sla_policy_override_id)
        if override and override.workspace_id == conv.workspace_id and override.active:
            return override

    result = await db.execute(
        select(SlaPolicy).where(
            SlaPolicy.workspace_id == conv.workspace_id,
            SlaPolicy.active.is_(True),
        )
    )
    policies = result.scalars().all()
    priority = _enum_value(conv.priority)

    matches = []
    for policy in policies:
        if policy.sector_id and policy.sector_id != conv.sector_id:
            continue
        if policy.channel_account_id and policy.channel_account_id != conv.channel_account_id:
            continue
        if policy.priority and policy.priority != priority:
            continue
        score = int(policy.sector_id is not None) + int(policy.channel_account_id is not None) + int(policy.priority is not None)
        matches.append((score, policy))
    if not matches:
        return None
    matches.sort(key=lambda item: item[0], reverse=True)
    return matches[0][1]


async def _latest_message(db: AsyncSession, conv_id: UUID) -> Message | None:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _latest_contact_message(db: AsyncSession, conv_id: UUID) -> Message | None:
    result = await db.execute(
        select(Message)
        .where(
            Message.conversation_id == conv_id,
            Message.sender_type == SenderType.contact,
        )
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _next_agent_reply_after(
    db: AsyncSession, conv_id: UUID, after: datetime
) -> Message | None:
    result = await db.execute(
        select(Message)
        .where(
            Message.conversation_id == conv_id,
            Message.sender_type == SenderType.agent,
            Message.created_at >= after,
        )
        .order_by(Message.created_at.asc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _first_agent_reply(db: AsyncSession, conv_id: UUID) -> Message | None:
    result = await db.execute(
        select(Message)
        .where(
            Message.conversation_id == conv_id,
            Message.sender_type == SenderType.agent,
        )
        .order_by(Message.created_at.asc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _latest_reopen_event(db: AsyncSession, conv_id: UUID) -> ConversationEvent | None:
    result = await db.execute(
        select(ConversationEvent)
        .where(
            ConversationEvent.conversation_id == conv_id,
            ConversationEvent.type == ConvEventType.reopened,
        )
        .order_by(ConversationEvent.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _record_sla_state(
    db: AsyncSession,
    conv: Conversation,
    policy: SlaPolicy,
    step: SlaEventType,
    start_at: datetime,
    target_minutes: int,
    achieved_at: datetime | None,
    rows: list[BusinessHours],
    holidays: list[BusinessHoliday] | None = None,
) -> SlaStatus:
    deadline_at = add_business_minutes(
        start_at,
        target_minutes,
        rows,
        policy.business_hours_only,
        holidays,
        conv.sector_id,
    )
    threshold_minutes = max(1, int(target_minutes * (policy.at_risk_threshold_pct / 100)))
    at_risk_at = add_business_minutes(
        start_at,
        threshold_minutes,
        rows,
        policy.business_hours_only,
        holidays,
        conv.sector_id,
    )
    now = _now()

    if achieved_at and achieved_at <= deadline_at:
        status = SlaStatus.ok
    elif achieved_at and achieved_at > deadline_at:
        status = SlaStatus.violated
    elif now >= deadline_at:
        status = SlaStatus.violated
    elif now >= at_risk_at:
        status = SlaStatus.at_risk
    else:
        status = SlaStatus.ok

    result = await db.execute(
        select(SlaEvent)
        .where(
            SlaEvent.workspace_id == conv.workspace_id,
            SlaEvent.conversation_id == conv.id,
            SlaEvent.policy_id == policy.id,
            SlaEvent.type == step,
            SlaEvent.achieved_at.is_(None),
        )
        .order_by(SlaEvent.created_at.desc())
        .limit(1)
    )
    event = result.scalar_one_or_none()
    if not event:
        event = SlaEvent(
            workspace_id=conv.workspace_id,
            conversation_id=conv.id,
            policy_id=policy.id,
            type=step,
            status=status,
            deadline_at=deadline_at,
            achieved_at=achieved_at,
            violated_at=now if status == SlaStatus.violated else None,
            metadata_={},
        )
        db.add(event)
    else:
        event.status = status
        event.deadline_at = deadline_at
        event.achieved_at = achieved_at
        if status == SlaStatus.violated and not event.violated_at:
            event.violated_at = now

    event.metadata_ = {
        **(event.metadata_ or {}),
        "start_at": start_at.isoformat(),
        "target_minutes": target_minutes,
        "at_risk_threshold_pct": policy.at_risk_threshold_pct,
    }

    if status in (SlaStatus.at_risk, SlaStatus.violated):
        await _apply_escalations(db, conv, policy, event, status)
    return status


async def _apply_escalations(
    db: AsyncSession,
    conv: Conversation,
    policy: SlaPolicy,
    event: SlaEvent,
    status: SlaStatus,
) -> None:
    result = await db.execute(
        select(SlaEscalationRule)
        .where(
            SlaEscalationRule.workspace_id == conv.workspace_id,
            SlaEscalationRule.policy_id == policy.id,
            SlaEscalationRule.active.is_(True),
        )
        .order_by(SlaEscalationRule.threshold_pct.asc(), SlaEscalationRule.position.asc())
    )
    rules = result.scalars().all()
    if not rules:
        rules = [
            SlaEscalationRule(
                workspace_id=conv.workspace_id,
                policy_id=policy.id,
                threshold_pct=policy.at_risk_threshold_pct,
                action="notify",
                target_role="agent",
                position=0,
                active=True,
            ),
            SlaEscalationRule(
                workspace_id=conv.workspace_id,
                policy_id=policy.id,
                threshold_pct=100,
                action="notify",
                target_role="supervisor",
                position=1,
                active=True,
            ),
            SlaEscalationRule(
                workspace_id=conv.workspace_id,
                policy_id=policy.id,
                threshold_pct=150,
                action="reassign",
                target_role="agent",
                position=2,
                active=True,
            ),
        ]

    metadata = event.metadata_ or {}
    try:
        start_at = datetime.fromisoformat(str(metadata.get("start_at")))
        target_minutes = max(float(metadata.get("target_minutes") or 1), 1.0)
        progress_pct = int(((_now() - start_at).total_seconds() / 60.0 / target_minutes) * 100)
    except (TypeError, ValueError):
        progress_pct = 100 if status == SlaStatus.violated else policy.at_risk_threshold_pct
    escalations = set(metadata.get("escalations", []))
    for rule in rules[:3]:
        if progress_pct < rule.threshold_pct:
            continue
        key = f"{rule.threshold_pct}:{rule.action}:{rule.target_role or rule.target_user_id or 'default'}"
        if key in escalations:
            continue
        escalations.add(key)

        event_type = ConvEventType.sla_violated if status == SlaStatus.violated else ConvEventType.sla_at_risk
        db.add(
            ConversationEvent(
                workspace_id=conv.workspace_id,
                conversation_id=conv.id,
                type=ConvEventType.sla_escalated if rule.action == "reassign" else event_type,
                actor_type="system",
                payload={
                    "sla_event_id": str(event.id),
                    "step": _enum_value(event.type),
                    "status": _enum_value(status),
                    "threshold_pct": rule.threshold_pct,
                    "action": rule.action,
                    "target_role": rule.target_role,
                    "target_user_id": str(rule.target_user_id) if rule.target_user_id else None,
                },
            )
        )

        if rule.action == "reassign" and conv.assignee_id:
            previous = conv.assignee_id
            conv.assignee_id = None
            await record_manual_assignment(db, conv, None, None, "sla_escalation", "sla_threshold")
            await db.flush()
            await assign_conversation_if_needed(
                db,
                conv,
                method="sla_escalation",
                exclude_user_id=previous,
            )

        await _notify_escalation(db, conv, policy, event, status, rule, progress_pct)
        await _broadcast(
            conv.workspace_id,
            {
                "type": "sla.escalated",
                "conversation_id": str(conv.id),
                "status": _enum_value(status),
                "step": _enum_value(event.type),
                "action": rule.action,
                "threshold_pct": rule.threshold_pct,
            },
        )
    metadata["escalations"] = sorted(escalations)
    event.metadata_ = metadata


async def _notify_escalation(
    db: AsyncSession,
    conv: Conversation,
    policy: SlaPolicy,
    event: SlaEvent,
    status: SlaStatus,
    rule: SlaEscalationRule,
    progress_pct: int,
) -> None:
    event_type = "sla.violated" if status == SlaStatus.violated else "sla.at_risk"
    payload = {
        "conversation_id": str(conv.id),
        "policy_id": str(policy.id),
        "sla_event_id": str(event.id),
        "step": _enum_value(event.type),
        "status": _enum_value(status),
        "threshold_pct": rule.threshold_pct,
        "progress_pct": progress_pct,
        "action": rule.action,
        "target_role": rule.target_role,
        "target_user_id": str(rule.target_user_id) if rule.target_user_id else None,
    }

    try:
        from app.services.external_webhooks import emit_event

        await emit_event(conv.workspace_id, event_type, payload)
    except Exception:  # noqa: BLE001
        pass

    if rule.action not in {"notify", "reassign"}:
        return

    user_ids: list[UUID] = []
    if rule.target_user_id:
        user_ids.append(rule.target_user_id)
    elif rule.target_role == "agent" and conv.assignee_id:
        user_ids.append(conv.assignee_id)
    elif rule.target_role == "supervisor":
        rows = await db.execute(
            select(UserWorkspaceMembership.user_id).where(
                UserWorkspaceMembership.workspace_id == conv.workspace_id,
                UserWorkspaceMembership.role.in_([WorkspaceRole.supervisor, WorkspaceRole.admin]),
            )
        )
        user_ids = [row[0] for row in rows.all()]

    if not user_ids and conv.assignee_id:
        user_ids = [conv.assignee_id]

    try:
        from app.services.notifier import dispatch

        await dispatch(
            conv.workspace_id,
            event_type=event_type,
            title="SLA violated" if status == SlaStatus.violated else "SLA at risk",
            body=f"Conversation {conv.id} is {_enum_value(status)} on {_enum_value(event.type)}.",
            payload=payload,
            user_ids=user_ids,
        )
    except Exception:  # noqa: BLE001
        pass


def _worst_status(statuses: list[SlaStatus]) -> SlaStatus:
    if SlaStatus.violated in statuses:
        return SlaStatus.violated
    if SlaStatus.at_risk in statuses:
        return SlaStatus.at_risk
    return SlaStatus.ok


async def evaluate_conversation_sla(db: AsyncSession, conv: Conversation) -> SlaStatus | None:
    if conv.status == ConversationStatus.resolved:
        return None
    policy = await _select_policy(db, conv)
    if not policy:
        return None

    rows = await _business_hours_rows(db, conv.workspace_id, conv.sector_id)
    holidays = await _business_holidays_rows(db, conv.workspace_id, conv.sector_id)
    statuses: list[SlaStatus] = []
    first_reply = await _first_agent_reply(db, conv.id)
    statuses.append(
        await _record_sla_state(
            db,
            conv,
            policy,
            SlaEventType.first_response,
            conv.created_at,
            policy.first_response_minutes,
            first_reply.created_at if first_reply else None,
            rows,
            holidays,
        )
    )
    statuses.append(
        await _record_sla_state(
            db,
            conv,
            policy,
            SlaEventType.resolution,
            conv.created_at,
            policy.resolution_minutes,
            conv.resolved_at,
            rows,
            holidays,
        )
    )

    latest_contact = await _latest_contact_message(db, conv.id)
    if policy.next_response_minutes and latest_contact:
        next_agent = await _next_agent_reply_after(db, conv.id, latest_contact.created_at)
        statuses.append(
            await _record_sla_state(
                db,
                conv,
                policy,
                SlaEventType.next_response,
                latest_contact.created_at,
                policy.next_response_minutes,
                next_agent.created_at if next_agent else None,
                rows,
                holidays,
            )
        )

    latest_reopen = await _latest_reopen_event(db, conv.id)
    if policy.reopen_response_minutes and latest_reopen:
        reopen_reply = await _next_agent_reply_after(db, conv.id, latest_reopen.created_at)
        statuses.append(
            await _record_sla_state(
                db,
                conv,
                policy,
                SlaEventType.reopen_response,
                latest_reopen.created_at,
                policy.reopen_response_minutes,
                reopen_reply.created_at if reopen_reply else None,
                rows,
                holidays,
            )
        )

    status = _worst_status(statuses)
    if conv.sla_status != status:
        conv.sla_status = status
        await _broadcast(
            conv.workspace_id,
            {"type": "sla.updated", "conversation_id": str(conv.id), "sla_status": _enum_value(status)},
        )
    return status


async def evaluate_workspace_sla(db: AsyncSession, workspace_id: UUID | None = None) -> int:
    q = select(Conversation).where(Conversation.status != ConversationStatus.resolved)
    if workspace_id:
        q = q.where(Conversation.workspace_id == workspace_id)
    conversations = (await db.execute(q)).scalars().all()
    count = 0
    for conv in conversations:
        if await evaluate_conversation_sla(db, conv):
            count += 1
    if workspace_id:
        await _broadcast(workspace_id, {"type": "supervisor.metrics.updated", "reason": "sla_evaluation"})
    return count


async def auto_resolve_inactive_conversations(db: AsyncSession) -> int:
    # Minimal Tier 1 automation hook: only acts on enabled rules.
    from app.models.sla import AutoResolveRule

    rules = (await db.execute(select(AutoResolveRule).where(AutoResolveRule.active.is_(True)))).scalars().all()
    total = 0
    for rule in rules:
        cutoff = _now() - timedelta(hours=rule.inactivity_hours)
        statuses = rule.status_from or ["open", "pending"]
        q = (
            select(Conversation)
            .where(
                Conversation.workspace_id == rule.workspace_id,
                Conversation.status.in_(statuses),
                Conversation.updated_at <= cutoff,
            )
        )
        if rule.sector_id:
            q = q.where(Conversation.sector_id == rule.sector_id)
        conversations = (await db.execute(q)).scalars().all()
        for conv in conversations:
            conv.status = ConversationStatus.resolved
            conv.resolved_at = _now()
            db.add(
                ConversationEvent(
                    workspace_id=conv.workspace_id,
                    conversation_id=conv.id,
                    type=ConvEventType.resolved,
                    actor_type="system",
                    payload={"reason": "auto_resolve_inactivity", "inactivity_hours": rule.inactivity_hours},
                )
            )
            total += 1
    return total


async def supervisor_overview(db: AsyncSession, workspace_id: UUID) -> dict:
    conversations = (
        await db.execute(
            select(Conversation).where(
                Conversation.workspace_id == workspace_id,
                Conversation.status != ConversationStatus.resolved,
            )
        )
    ).scalars().all()
    sectors = (await db.execute(select(Sector).where(Sector.workspace_id == workspace_id))).scalars().all()
    sector_names = {sector.id: sector.name for sector in sectors}

    sector_metrics: dict[UUID | None, dict] = defaultdict(
        lambda: {"queued": 0, "active": 0, "at_risk": 0, "violated": 0}
    )
    for conv in conversations:
        bucket = sector_metrics[conv.sector_id]
        if conv.assignee_id:
            bucket["active"] += 1
        else:
            bucket["queued"] += 1
        if conv.sla_status == SlaStatus.at_risk:
            bucket["at_risk"] += 1
        elif conv.sla_status == SlaStatus.violated:
            bucket["violated"] += 1

    members = (
        await db.execute(
            select(User, UserWorkspaceMembership, AgentStatus, AgentPauseReason, AgentCapacity)
            .join(UserWorkspaceMembership, UserWorkspaceMembership.user_id == User.id)
            .outerjoin(
                AgentStatus,
                (AgentStatus.workspace_id == workspace_id) & (AgentStatus.user_id == User.id),
            )
            .outerjoin(AgentPauseReason, AgentPauseReason.id == AgentStatus.reason_id)
            .outerjoin(
                AgentCapacity,
                (AgentCapacity.workspace_id == workspace_id) & (AgentCapacity.user_id == User.id),
            )
            .where(
                UserWorkspaceMembership.workspace_id == workspace_id,
                UserWorkspaceMembership.role.in_([WorkspaceRole.agent, WorkspaceRole.supervisor]),
            )
            .order_by(User.name.asc())
        )
    ).all()

    convs_by_agent: dict[UUID, list[Conversation]] = defaultdict(list)
    for conv in conversations:
        if conv.assignee_id:
            convs_by_agent[conv.assignee_id].append(conv)

    agent_metrics = []
    for user, membership, status, reason, capacity in members:
        assigned = convs_by_agent.get(user.id, [])
        weights = capacity.priority_weights if capacity else {}
        max_conversations = capacity.max_conversations if capacity else 10
        max_weight = capacity.max_weight if capacity else float(max_conversations)
        weighted = sum(_conversation_weight(conv, weights) for conv in assigned)
        agent_metrics.append(
            {
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "role": _enum_value(membership.role),
                "sector_id": capacity.sector_id if capacity else None,
                "status": status.status if status else _enum_value(user.status),
                "reason": reason.label if reason else None,
                "since_at": status.since_at if status else None,
                "max_conversations": max_conversations,
                "max_weight": max_weight,
                "assigned_open": len(assigned),
                "weighted_load": round(weighted, 2),
                "available_slots": round(max(max_weight - weighted, 0), 2),
                "at_risk": sum(1 for conv in assigned if conv.sla_status == SlaStatus.at_risk),
                "violated": sum(1 for conv in assigned if conv.sla_status == SlaStatus.violated),
            }
        )

    alert_convs = sorted(
        [conv for conv in conversations if conv.sla_status in (SlaStatus.at_risk, SlaStatus.violated)],
        key=lambda conv: (0 if conv.sla_status == SlaStatus.violated else 1, conv.updated_at),
    )[:20]
    contacts = {}
    if alert_convs:
        contact_ids = [conv.contact_id for conv in alert_convs]
        rows = (await db.execute(select(Contact).where(Contact.id.in_(contact_ids)))).scalars().all()
        contacts = {contact.id: contact for contact in rows}

    alerts = []
    for conv in alert_convs:
        latest = await _latest_message(db, conv.id)
        alerts.append(
            {
                "conversation_id": conv.id,
                "contact_name": contacts.get(conv.contact_id).name if contacts.get(conv.contact_id) else None,
                "assignee_id": conv.assignee_id,
                "sector_id": conv.sector_id,
                "sla_status": _enum_value(conv.sla_status),
                "priority": _enum_value(conv.priority),
                "last_message_at": latest.created_at if latest else None,
            }
        )

    totals = {
        "queued": sum(1 for conv in conversations if not conv.assignee_id),
        "active": sum(1 for conv in conversations if conv.assignee_id),
        "at_risk": sum(1 for conv in conversations if conv.sla_status == SlaStatus.at_risk),
        "violated": sum(1 for conv in conversations if conv.sla_status == SlaStatus.violated),
        "agents_online": sum(1 for agent in agent_metrics if agent["status"] == "online"),
        "capacity_used": round(sum(agent["weighted_load"] for agent in agent_metrics), 2),
        "capacity_total": round(sum(agent["max_weight"] for agent in agent_metrics), 2),
    }

    sector_rows = []
    for sector_id, values in sector_metrics.items():
        sector_rows.append(
            {
                "sector_id": sector_id,
                "sector_name": sector_names.get(sector_id, "Workspace queue" if sector_id is None else "Unknown sector"),
                **values,
            }
        )
    return {"totals": totals, "sectors": sector_rows, "agents": agent_metrics, "alerts": alerts}
