"""Per-agent × hour-of-day occupancy heatmap.

For the last N days, counts ConversationAssignment intervals (between
assigned_at and unassigned_at-or-now) and totalises minutes assigned per
agent per hour of day. Returns a 24-column grid per agent.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sla import ConversationAssignment
from app.models.workspace import User


async def build_heatmap(db: AsyncSession, workspace_id: UUID, days: int = 7) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        await db.execute(
            select(ConversationAssignment, User)
            .join(User, User.id == ConversationAssignment.user_id)
            .where(
                ConversationAssignment.workspace_id == workspace_id,
                ConversationAssignment.assigned_at >= since,
            )
        )
    ).all()

    # cells[user_id][hour] = {minutes, conversations}
    cells: dict[UUID, dict] = {}
    user_names: dict[UUID, str] = {}
    for assignment, user in rows:
        if not assignment.user_id:
            continue
        user_names[assignment.user_id] = user.name
        end = assignment.unassigned_at or datetime.now(timezone.utc)
        start = max(assignment.assigned_at, since)
        if end <= start:
            continue
        user_bucket = cells.setdefault(assignment.user_id, {})
        cursor = start
        while cursor < end:
            hour = cursor.hour
            next_hour = (cursor.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
            slot_end = min(end, next_hour)
            minutes = int((slot_end - cursor).total_seconds() / 60)
            cell = user_bucket.setdefault(hour, {"minutes": 0, "conversations": 0})
            cell["minutes"] += minutes
            cell["conversations"] += 1
            cursor = slot_end

    out_cells = []
    for user_id, hours in cells.items():
        for hour, agg in hours.items():
            out_cells.append(
                {
                    "user_id": user_id,
                    "user_name": user_names.get(user_id, ""),
                    "hour": hour,
                    "minutes_assigned": agg["minutes"],
                    "conversations": agg["conversations"],
                }
            )
    return {"days": days, "cells": out_cells}
