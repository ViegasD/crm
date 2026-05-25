"""Timeline + reopen-policy service (Stage 3 final task).

Two responsibilities:

1. Read side: ``get_contact_timeline`` returns the historical timeline for a
   contact across every conversation/protocol they ever had, with messages and
   events folded together and the active conversation explicitly marked.

2. Write side: ``resolve_inbound_conversation`` decides — given an inbound
   message arriving for a (contact, channel_account) pair — whether to attach
   it to an existing open conversation, reopen the most recent resolved one,
   or open a brand-new protocol. The decision is governed by the workspace's
   ConversationPolicy (optionally overridden per sector).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable
from uuid import UUID

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import (
    Conversation,
    ConversationEvent,
    ConversationPolicy,
    Message,
)
from app.models.enums import (
    ConversationStatus,
    ConvEventType,
    MessageOrigin,
    ReopenMode,
    SenderType,
)


# ---------------------------------------------------------------------------
# Policy resolution
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class ResolvedPolicy:
    reopen_mode: ReopenMode
    reopen_window_hours: int
    inherit_assignee_on_new: bool
    source: str  # "sector" | "workspace" | "default"


_DEFAULT_POLICY = ResolvedPolicy(
    reopen_mode=ReopenMode.window,
    reopen_window_hours=24,
    inherit_assignee_on_new=False,
    source="default",
)


async def resolve_policy(
    db: AsyncSession,
    workspace_id: UUID,
    sector_id: UUID | None,
) -> ResolvedPolicy:
    """Return the effective ConversationPolicy for (workspace, sector).

    Lookup order: sector-specific row → workspace default row → hard default.
    """
    rows = (
        await db.execute(
            select(ConversationPolicy).where(
                ConversationPolicy.workspace_id == workspace_id,
                or_(
                    ConversationPolicy.sector_id == sector_id if sector_id else False,
                    ConversationPolicy.sector_id.is_(None),
                ),
            )
        )
    ).scalars().all()

    sector_row = next((p for p in rows if p.sector_id == sector_id and sector_id is not None), None)
    ws_row = next((p for p in rows if p.sector_id is None), None)
    chosen = sector_row or ws_row
    if chosen is None:
        return _DEFAULT_POLICY
    return ResolvedPolicy(
        reopen_mode=chosen.reopen_mode,
        reopen_window_hours=chosen.reopen_window_hours,
        inherit_assignee_on_new=chosen.inherit_assignee_on_new,
        source="sector" if chosen.sector_id else "workspace",
    )


# ---------------------------------------------------------------------------
# Inbound conversation resolver
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class InboundResolution:
    conversation: Conversation
    action: str  # "existing" | "reopened" | "new"


async def resolve_inbound_conversation(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    contact_id: UUID,
    channel_account_id: UUID,
    sector_id_hint: UUID | None = None,
    now: datetime | None = None,
) -> InboundResolution:
    """Return the conversation that an inbound message should belong to.

    Decision tree:

    1. If the contact has any non-resolved conversation on the same channel_account,
       reuse it.
    2. Else, look up the most recent resolved conversation on the same channel
       and apply the policy:
       - ``always_reopen``: reopen it
       - ``window``: reopen if ``resolved_at`` is within ``reopen_window_hours``
       - ``always_new``: always create a new conversation/protocol
    3. Else create a brand-new conversation and emit ``new_protocol_created``.

    Callers must commit the session themselves.
    """
    now = now or datetime.now(timezone.utc)

    # 1. Look for an already-open conversation on this channel
    open_conv = (
        await db.execute(
            select(Conversation).where(
                Conversation.workspace_id == workspace_id,
                Conversation.contact_id == contact_id,
                Conversation.channel_account_id == channel_account_id,
                Conversation.status != ConversationStatus.resolved,
            ).order_by(desc(Conversation.updated_at)).limit(1)
        )
    ).scalar_one_or_none()
    if open_conv:
        return InboundResolution(conversation=open_conv, action="existing")

    # 2. Look for the most recent resolved conversation
    last_resolved = (
        await db.execute(
            select(Conversation).where(
                Conversation.workspace_id == workspace_id,
                Conversation.contact_id == contact_id,
                Conversation.channel_account_id == channel_account_id,
                Conversation.status == ConversationStatus.resolved,
            ).order_by(desc(Conversation.resolved_at)).limit(1)
        )
    ).scalar_one_or_none()

    sector_for_policy = sector_id_hint or (last_resolved.sector_id if last_resolved else None)
    policy = await resolve_policy(db, workspace_id, sector_for_policy)

    if last_resolved is not None:
        should_reopen = False
        if policy.reopen_mode == ReopenMode.always_reopen:
            should_reopen = True
        elif policy.reopen_mode == ReopenMode.window:
            if last_resolved.resolved_at:
                resolved_at = last_resolved.resolved_at
                if resolved_at.tzinfo is None:
                    resolved_at = resolved_at.replace(tzinfo=timezone.utc)
                if now - resolved_at <= timedelta(hours=policy.reopen_window_hours):
                    should_reopen = True

        if should_reopen:
            last_resolved.status = ConversationStatus.open
            last_resolved.resolved_at = None
            db.add(
                ConversationEvent(
                    workspace_id=workspace_id,
                    conversation_id=last_resolved.id,
                    type=ConvEventType.auto_reopened,
                    actor_id=None,
                    actor_type="system",
                    payload={
                        "policy_mode": policy.reopen_mode.value,
                        "policy_source": policy.source,
                        "window_hours": policy.reopen_window_hours,
                    },
                )
            )
            await db.flush()
            return InboundResolution(conversation=last_resolved, action="reopened")

    # 3. Brand-new protocol
    new_conv = Conversation(
        workspace_id=workspace_id,
        channel_account_id=channel_account_id,
        contact_id=contact_id,
        sector_id=last_resolved.sector_id if last_resolved else None,
        assignee_id=(
            last_resolved.assignee_id
            if last_resolved and policy.inherit_assignee_on_new
            else None
        ),
        status=ConversationStatus.open,
    )
    db.add(new_conv)
    await db.flush()

    db.add(
        ConversationEvent(
            workspace_id=workspace_id,
            conversation_id=new_conv.id,
            type=ConvEventType.new_protocol_created,
            actor_id=None,
            actor_type="system",
            payload={
                "previous_conversation_id": str(last_resolved.id) if last_resolved else None,
                "policy_mode": policy.reopen_mode.value if last_resolved else "first_contact",
                "policy_source": policy.source,
            },
        )
    )
    db.add(
        ConversationEvent(
            workspace_id=workspace_id,
            conversation_id=new_conv.id,
            type=ConvEventType.opened,
            actor_id=None,
            actor_type="system",
            payload={},
        )
    )
    return InboundResolution(conversation=new_conv, action="new")


# ---------------------------------------------------------------------------
# Read side — contact timeline
# ---------------------------------------------------------------------------


async def get_contact_timeline(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    contact_id: UUID,
    channel_account_id: UUID | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    statuses: Iterable[ConversationStatus] | None = None,
    limit_per_conversation: int = 200,
    active_conversation_id: UUID | None = None,
) -> dict:
    """Return the consolidated history for a contact.

    Output structure::

        {
          "contact_id": "...",
          "conversations": [
            {
              "id": "...",
              "channel_account_id": "...",
              "sector_id": "...",
              "status": "resolved",
              "is_active": false,
              "opened_at": "...",
              "resolved_at": "...",
              "items": [
                {"kind": "message", "ts": "...", ...},
                {"kind": "event",   "ts": "...", ...},
                ...
              ]
            },
            ...
          ]
        }
    """
    q = select(Conversation).where(
        Conversation.workspace_id == workspace_id,
        Conversation.contact_id == contact_id,
    )
    if channel_account_id:
        q = q.where(Conversation.channel_account_id == channel_account_id)
    if statuses:
        q = q.where(Conversation.status.in_(list(statuses)))
    q = q.order_by(desc(Conversation.created_at))
    conversations = (await db.execute(q)).scalars().all()

    if not conversations:
        return {"contact_id": str(contact_id), "conversations": []}

    conv_ids = [c.id for c in conversations]

    # Fetch messages
    msg_q = select(Message).where(
        Message.workspace_id == workspace_id,
        Message.conversation_id.in_(conv_ids),
    )
    if since:
        msg_q = msg_q.where(Message.created_at >= since)
    if until:
        msg_q = msg_q.where(Message.created_at <= until)
    msg_q = msg_q.order_by(Message.conversation_id, Message.created_at)
    messages = (await db.execute(msg_q)).scalars().all()

    # Fetch events
    ev_q = select(ConversationEvent).where(
        ConversationEvent.workspace_id == workspace_id,
        ConversationEvent.conversation_id.in_(conv_ids),
    )
    if since:
        ev_q = ev_q.where(ConversationEvent.created_at >= since)
    if until:
        ev_q = ev_q.where(ConversationEvent.created_at <= until)
    ev_q = ev_q.order_by(ConversationEvent.conversation_id, ConversationEvent.created_at)
    events = (await db.execute(ev_q)).scalars().all()

    # Group by conversation
    by_conv: dict[UUID, list] = {cid: [] for cid in conv_ids}
    for m in messages:
        by_conv[m.conversation_id].append(
            {
                "kind": "message",
                "ts": m.created_at.isoformat() if m.created_at else None,
                "id": str(m.id),
                "direction": (
                    "outbound" if m.origin == MessageOrigin.agent else "inbound"
                ),
                "sender_type": m.sender_type.value if m.sender_type else None,
                "sender_id": str(m.sender_id) if m.sender_id else None,
                "type": m.type.value if m.type else None,
                "content": m.content,
                "attachments": m.attachments,
            }
        )
    for e in events:
        by_conv[e.conversation_id].append(
            {
                "kind": "event",
                "ts": e.created_at.isoformat() if e.created_at else None,
                "id": str(e.id),
                "type": e.type.value if e.type else None,
                "actor_id": str(e.actor_id) if e.actor_id else None,
                "actor_type": e.actor_type,
                "payload": e.payload or {},
            }
        )

    # Sort items inside each conversation by timestamp and apply per-conv limit
    out_convs = []
    for c in conversations:
        items = sorted(by_conv.get(c.id, []), key=lambda i: i["ts"] or "")
        if limit_per_conversation and len(items) > limit_per_conversation:
            items = items[-limit_per_conversation:]
        out_convs.append(
            {
                "id": str(c.id),
                "channel_account_id": str(c.channel_account_id),
                "sector_id": str(c.sector_id) if c.sector_id else None,
                "assignee_id": str(c.assignee_id) if c.assignee_id else None,
                "status": c.status.value if c.status else None,
                "priority": c.priority.value if c.priority else None,
                "is_active": (
                    c.id == active_conversation_id
                    if active_conversation_id
                    else c.status != ConversationStatus.resolved
                ),
                "opened_at": c.created_at.isoformat() if c.created_at else None,
                "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
                "resolve_note": c.resolve_note,
                "items": items,
            }
        )

    return {"contact_id": str(contact_id), "conversations": out_convs}


# ---------------------------------------------------------------------------
# Convenience helpers used by webhooks / message_service
# ---------------------------------------------------------------------------


async def log_message_event(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    conversation_id: UUID,
    direction: str,
    message_id: UUID | None = None,
    template_name: str | None = None,
    actor_id: UUID | None = None,
    actor_type: str | None = None,
) -> None:
    """Append a lightweight timeline marker for a message.

    The full message text is already persisted in ``messages``; this row is a
    cheap timeline anchor that lets us render eventually-paginated message
    activity without joining heavy tables in every timeline query.
    """
    if direction == "inbound":
        ev_type = ConvEventType.message_inbound
    elif direction == "outbound":
        ev_type = ConvEventType.message_outbound
    elif direction == "template":
        ev_type = ConvEventType.template_sent
    else:
        return

    payload: dict = {}
    if message_id is not None:
        payload["message_id"] = str(message_id)
    if template_name:
        payload["template_name"] = template_name

    db.add(
        ConversationEvent(
            workspace_id=workspace_id,
            conversation_id=conversation_id,
            type=ev_type,
            actor_id=actor_id,
            actor_type=actor_type,
            payload=payload,
        )
    )
