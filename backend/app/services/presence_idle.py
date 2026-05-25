"""Auto-flip agent presence based on inactivity.

- WebSocket connect/disconnect updates `agent_status.since_at` indirectly
  via heartbeats (in websocket layer — see manager).
- This module runs from Celery: each minute it loads idle_rules per workspace
  and flips any agent whose last activity is older than idle_minutes →
  status='away', and older than offline_minutes → status='offline'.

`last activity` is approximated by max(updated_at, last sent message). The
WebSocket handler should also call `mark_agent_active(workspace_id, user_id)`
on every inbound socket frame.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.redis import get_redis
from app.models.sla import AgentStatus
from app.models.stage9_extras import IdleRule
from app.services.sla_service import set_agent_status

logger = logging.getLogger(__name__)

_REDIS_KEY = "presence:last_active:{workspace}:{user}"


async def mark_agent_active(workspace_id: UUID, user_id: UUID) -> None:
    redis = await get_redis()
    key = _REDIS_KEY.format(workspace=workspace_id, user=user_id)
    await redis.set(key, datetime.now(timezone.utc).isoformat(), ex=7 * 24 * 3600)


async def _last_active(workspace_id: UUID, user_id: UUID) -> datetime | None:
    redis = await get_redis()
    key = _REDIS_KEY.format(workspace=workspace_id, user=user_id)
    raw = await redis.get(key)
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.decode() if isinstance(raw, bytes) else raw)
    except Exception:  # noqa: BLE001
        return None


async def evaluate_idle() -> int:
    """For each workspace with an active IdleRule, flip stale agents."""
    flips = 0
    async with AsyncSessionLocal() as db:
        rules = (
            await db.execute(select(IdleRule).where(IdleRule.active.is_(True)))
        ).scalars().all()
        for rule in rules:
            statuses = (
                await db.execute(
                    select(AgentStatus).where(
                        AgentStatus.workspace_id == rule.workspace_id,
                        AgentStatus.status.in_(["online", "away"]),
                    )
                )
            ).scalars().all()
            for status in statuses:
                last = await _last_active(rule.workspace_id, status.user_id)
                if last is None:
                    continue
                now = datetime.now(timezone.utc)
                age_minutes = (now - last).total_seconds() / 60
                if status.status == "online" and age_minutes >= rule.idle_minutes:
                    await set_agent_status(
                        db, rule.workspace_id, status.user_id, "away",
                        None, "Auto: idle", None,
                    )
                    await _emit_presence_event(rule.workspace_id, status.user_id, "agent.idle", age_minutes)
                    flips += 1
                elif age_minutes >= rule.offline_minutes:
                    await set_agent_status(
                        db, rule.workspace_id, status.user_id, "offline",
                        None, "Auto: offline", None,
                    )
                    await _emit_presence_event(rule.workspace_id, status.user_id, "agent.offline", age_minutes)
                    flips += 1
        if flips:
            await db.commit()
    return flips


async def _emit_presence_event(
    workspace_id: UUID, user_id: UUID, event_type: str, age_minutes: float
) -> None:
    payload = {
        "user_id": str(user_id),
        "age_minutes": round(age_minutes, 2),
    }
    try:
        from app.services.external_webhooks import emit_event

        await emit_event(workspace_id, event_type, payload)
    except Exception:  # noqa: BLE001
        logger.exception("failed to enqueue presence webhook")
    try:
        from app.services.notifier import dispatch

        await dispatch(
            workspace_id,
            event_type=event_type,
            title="Agent went idle" if event_type == "agent.idle" else "Agent went offline",
            payload=payload,
        )
    except Exception:  # noqa: BLE001
        logger.exception("failed to dispatch presence notification")
