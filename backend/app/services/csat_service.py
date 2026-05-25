"""CSAT — Customer Satisfaction surveys triggered on conversation resolve.

Lifecycle:
1. When a conversation transitions to resolved, dispatch_csat creates a
   CsatSurvey row with a random token and tries to send via the conversation
   channel (template msg) or fallback link.
2. Customer responds either via channel reply or via public endpoint
   /public/csat/{token} → score saved → SLA ranking can read it.

This module exposes a helper `record_resolution_for_csat(conv)` that other
services (sla_service.update_conversation) can call.
"""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.conversation import Conversation
from app.models.stage9_extras import CsatSurvey
from app.services.notifier import dispatch

logger = logging.getLogger(__name__)


async def dispatch_csat(workspace_id: UUID, conversation_id: UUID) -> CsatSurvey | None:
    """Idempotent: if a survey already exists for the conversation, return it."""
    try:
        async with AsyncSessionLocal() as db:
            existing = (
                await db.execute(
                    select(CsatSurvey).where(CsatSurvey.conversation_id == conversation_id)
                )
            ).scalar_one_or_none()
            if existing:
                return existing
            conv = await db.get(Conversation, conversation_id)
            if not conv or conv.workspace_id != workspace_id:
                return None
            token = secrets.token_urlsafe(24)
            survey = CsatSurvey(
                workspace_id=workspace_id,
                conversation_id=conv.id,
                contact_id=conv.contact_id,
                assignee_id=conv.assignee_id,
                sector_id=conv.sector_id,
                token=token,
                delivery_status="sent",
                sent_at=datetime.now(timezone.utc),
            )
            db.add(survey)
            await db.commit()
            await db.refresh(survey)
        # Fan-out internal notification so notification channels (slack/email)
        # can know a CSAT was dispatched.
        await dispatch(
            workspace_id,
            event_type="csat.sent",
            title="CSAT survey sent",
            body=f"Conversation {conversation_id} closed; survey dispatched",
            payload={"conversation_id": str(conversation_id), "token": token},
        )
        return survey
    except SQLAlchemyError:
        logger.exception("dispatch_csat failed for conversation %s", conversation_id)
        return None


async def record_response(token: str, score: int, feedback: str | None) -> CsatSurvey | None:
    if not (1 <= score <= 5):
        return None
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(CsatSurvey).where(CsatSurvey.token == token))
        survey = result.scalar_one_or_none()
        if not survey or survey.responded_at is not None:
            return survey
        survey.score = score
        survey.feedback = feedback
        survey.responded_at = datetime.now(timezone.utc)
        survey.delivery_status = "responded"
        await db.commit()
        await db.refresh(survey)
    await dispatch(
        survey.workspace_id,
        event_type="csat.responded",
        title=f"CSAT response: {score}/5",
        body=feedback or "",
        payload={
            "conversation_id": str(survey.conversation_id),
            "score": score,
        },
    )
    return survey
