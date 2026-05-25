"""Workspace-level notifier with pluggable channels (in-app, email, Slack).

Usage from anywhere in the app:

    from app.services.notifier import dispatch
    await dispatch(workspace_id, event_type="sla.violated",
                   title="SLA violated", body="Conversation X is past deadline",
                   payload={"conversation_id": str(conv.id)})

For each NotificationChannel whose `events` array contains the event_type
(or is empty meaning "all"), a NotificationDelivery row is created and
attempted. In-app channels just persist for /notifications pull; email and
Slack are dispatched best-effort (errors are logged + delivery row marked
failed). For users mentioned, an inapp delivery is recorded directly.
"""
from __future__ import annotations

import json
import logging
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.stage9_extras import NotificationChannel, NotificationDelivery
from app.models.workspace import User
from app.websocket.manager import manager

logger = logging.getLogger(__name__)


async def dispatch(
    workspace_id: UUID,
    *,
    event_type: str,
    title: str,
    body: str | None = None,
    payload: dict | None = None,
    user_ids: list[UUID] | None = None,
) -> int:
    """Fan-out a notification to every matching channel + user_ids in-app.

    Returns the number of deliveries created.
    """
    payload = payload or {}
    created = 0
    try:
        async with AsyncSessionLocal() as db:
            channels = (
                await db.execute(
                    select(NotificationChannel).where(
                        NotificationChannel.workspace_id == workspace_id,
                        NotificationChannel.active.is_(True),
                    )
                )
            ).scalars().all()

            for channel in channels:
                if channel.events and event_type not in channel.events:
                    continue
                delivery = NotificationDelivery(
                    workspace_id=workspace_id,
                    channel_id=channel.id,
                    event_type=event_type,
                    title=title,
                    body=body,
                    payload=payload,
                    status="pending",
                )
                db.add(delivery)
                await db.flush()
                ok, err = await _deliver(channel, delivery, payload)
                delivery.status = "delivered" if ok else "failed"
                delivery.error_message = err
                created += 1

            # Per-user in-app deliveries (always created when user_ids set)
            for user_id in user_ids or []:
                db.add(
                    NotificationDelivery(
                        workspace_id=workspace_id,
                        user_id=user_id,
                        event_type=event_type,
                        title=title,
                        body=body,
                        payload=payload,
                        status="delivered",
                    )
                )
                created += 1
                await manager.broadcast(
                    str(workspace_id),
                    {
                        "type": "notification",
                        "event_type": event_type,
                        "title": title,
                        "user_id": str(user_id),
                    },
                )

            await db.commit()
    except SQLAlchemyError:
        logger.exception("notifier.dispatch persistence failed")
    return created


async def _deliver(
    channel: NotificationChannel, delivery: NotificationDelivery, payload: dict
) -> tuple[bool, str | None]:
    try:
        if channel.kind == "inapp":
            await manager.broadcast(
                str(channel.workspace_id),
                {
                    "type": "notification",
                    "event_type": delivery.event_type,
                    "title": delivery.title,
                    "channel_id": str(channel.id),
                },
            )
            return True, None
        if channel.kind == "slack_webhook":
            url = channel.config.get("url")
            if not url:
                return False, "missing url"
            text = f"*{delivery.title}*\n{delivery.body or ''}"
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json={"text": text})
                resp.raise_for_status()
            return True, None
        if channel.kind == "email":
            recipients = channel.config.get("recipients") or []
            if not recipients:
                return False, "no recipients"
            return _send_email(recipients, delivery.title, delivery.body or "")
        if channel.kind == "webhook":
            url = channel.config.get("url")
            if not url:
                return False, "missing url"
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    url,
                    json={
                        "event_type": delivery.event_type,
                        "title": delivery.title,
                        "body": delivery.body,
                        "payload": payload,
                    },
                )
                resp.raise_for_status()
            return True, None
        return False, f"unknown kind {channel.kind}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def _send_email(recipients: list[str], subject: str, body: str) -> tuple[bool, str | None]:
    host = getattr(settings, "smtp_host", None) or "localhost"
    port = int(getattr(settings, "smtp_port", 25) or 25)
    user = getattr(settings, "smtp_user", None)
    password = getattr(settings, "smtp_password", None)
    sender = getattr(settings, "smtp_sender", None) or "crm@localhost"
    try:
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            if user and password:
                smtp.starttls()
                smtp.login(user, password)
            smtp.send_message(msg)
        return True, None
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


async def mark_read(
    db: AsyncSession, workspace_id: UUID, user_id: UUID, ids: list[UUID] | None
) -> int:
    from sqlalchemy import update as sa_update

    stmt = (
        sa_update(NotificationDelivery)
        .where(
            NotificationDelivery.workspace_id == workspace_id,
            NotificationDelivery.user_id == user_id,
            NotificationDelivery.read_at.is_(None),
        )
        .values(read_at=datetime.now(timezone.utc))
    )
    if ids:
        stmt = stmt.where(NotificationDelivery.id.in_(ids))
    result = await db.execute(stmt)
    return result.rowcount or 0
