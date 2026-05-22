"""Execute a Macro on a conversation: applies each action sequentially.

Each action is best-effort; failure of one does not abort the rest.
Returns a structured report so the UI can surface what happened.
"""
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import (
    CannedResponse,
    Conversation,
    ConversationEvent,
    ConversationLabel,
    ConversationParticipant,
    Label,
)
from app.models.enums import (
    ConvEventType,
    ConversationStatus,
    ConvPriority,
    MacroActionType,
    MessageOrigin,
    MessageType,
    SenderType,
)
from app.models.macros import Macro
from app.models.workspace import User
from app.schemas.conversation import ConversationTransfer, ConversationUpdate
from app.schemas.message import SendMessageRequest
from app.services.canned_response_service import build_render_context, render_template
from app.services.conversation_service import (
    get_conversation_or_404,
    transfer_conversation,
    update_conversation,
)
from app.services.message_service import send_agent_message

logger = logging.getLogger(__name__)


class MacroExecutionResult:
    def __init__(self) -> None:
        self.executed: list[str] = []
        self.skipped: list[str] = []
        self.errors: list[str] = []


async def run_macro(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    macro: Macro,
    conversation_id: UUID,
    actor: User,
) -> MacroExecutionResult:
    result = MacroExecutionResult()
    conv = await get_conversation_or_404(db, workspace_id, conversation_id)

    for action in macro.actions:
        try:
            await _run_action(db, workspace_id, action.action_type, action.params, conv, actor)
            result.executed.append(action.action_type.value)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Macro action failed: %s", action.action_type)
            result.errors.append(f"{action.action_type.value}: {exc}")
    return result


async def _run_action(
    db: AsyncSession,
    workspace_id: UUID,
    action_type: MacroActionType,
    params: dict,
    conv: Conversation,
    actor: User,
) -> None:
    if action_type == MacroActionType.send_message:
        body = SendMessageRequest(
            content=params.get("content", ""),
            type=MessageType.text,
            attachments=params.get("attachments", []) or [],
            is_note=False,
        )
        await send_agent_message(db, workspace_id, conv, actor.id, body)
    elif action_type == MacroActionType.send_canned:
        canned_id = params.get("canned_response_id")
        if not canned_id:
            raise ValueError("canned_response_id required")
        canned = await db.get(CannedResponse, UUID(canned_id))
        if not canned or canned.workspace_id != workspace_id:
            raise ValueError("canned not found")
        context = await build_render_context(
            db, workspace_id=workspace_id, conversation_id=conv.id, agent=actor
        )
        content = render_template(canned.content, context)
        body = SendMessageRequest(content=content, type=MessageType.text, attachments=canned.attachments or [])
        await send_agent_message(db, workspace_id, conv, actor.id, body)
    elif action_type == MacroActionType.apply_label:
        label_id = UUID(params["label_id"])
        label = await db.get(Label, label_id)
        if not label or label.workspace_id != workspace_id:
            raise ValueError("label not found")
        existing = await db.execute(
            select(ConversationLabel).where(
                ConversationLabel.workspace_id == workspace_id,
                ConversationLabel.conversation_id == conv.id,
                ConversationLabel.label_id == label_id,
            )
        )
        if existing.scalar_one_or_none():
            return
        db.add(
            ConversationLabel(
                workspace_id=workspace_id,
                conversation_id=conv.id,
                label_id=label_id,
                assigned_by=actor.id,
            )
        )
        db.add(
            ConversationEvent(
                workspace_id=workspace_id,
                conversation_id=conv.id,
                type=ConvEventType.label_added,
                actor_id=actor.id,
                actor_type="agent",
                payload={"label_id": str(label_id), "label_name": label.name, "via": "macro"},
            )
        )
    elif action_type == MacroActionType.remove_label:
        from sqlalchemy import delete as sa_delete

        label_id = UUID(params["label_id"])
        await db.execute(
            sa_delete(ConversationLabel).where(
                ConversationLabel.workspace_id == workspace_id,
                ConversationLabel.conversation_id == conv.id,
                ConversationLabel.label_id == label_id,
            )
        )
        db.add(
            ConversationEvent(
                workspace_id=workspace_id,
                conversation_id=conv.id,
                type=ConvEventType.label_removed,
                actor_id=actor.id,
                actor_type="agent",
                payload={"label_id": str(label_id), "via": "macro"},
            )
        )
    elif action_type == MacroActionType.transfer:
        transfer = ConversationTransfer(
            assignee_id=UUID(params["assignee_id"]) if params.get("assignee_id") else None,
            sector_id=UUID(params["sector_id"]) if params.get("sector_id") else None,
            note=params.get("note"),
            transfer_reason_id=UUID(params["transfer_reason_id"]) if params.get("transfer_reason_id") else None,
        )
        await transfer_conversation(db, workspace_id, conv.id, transfer, actor.id)
    elif action_type == MacroActionType.assign:
        update = ConversationUpdate(assignee_id=UUID(params["assignee_id"]) if params.get("assignee_id") else None)
        await update_conversation(db, workspace_id, conv.id, update, actor.id)
    elif action_type == MacroActionType.add_note:
        body = SendMessageRequest(content=params.get("content", ""), type=MessageType.text, is_note=True)
        await send_agent_message(db, workspace_id, conv, actor.id, body)
    elif action_type == MacroActionType.set_status:
        status_val = params.get("status")
        update = ConversationUpdate(status=ConversationStatus(status_val))
        await update_conversation(db, workspace_id, conv.id, update, actor.id)
    elif action_type == MacroActionType.set_priority:
        update = ConversationUpdate(priority=ConvPriority(params.get("priority")))
        await update_conversation(db, workspace_id, conv.id, update, actor.id)
    elif action_type == MacroActionType.add_participant:
        user_id = UUID(params["user_id"])
        existing = await db.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.workspace_id == workspace_id,
                ConversationParticipant.conversation_id == conv.id,
                ConversationParticipant.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none():
            return
        db.add(
            ConversationParticipant(
                workspace_id=workspace_id, conversation_id=conv.id, user_id=user_id
            )
        )
        db.add(
            ConversationEvent(
                workspace_id=workspace_id,
                conversation_id=conv.id,
                type=ConvEventType.participant_added,
                actor_id=actor.id,
                actor_type="agent",
                payload={"user_id": str(user_id), "via": "macro"},
            )
        )
    else:
        raise ValueError(f"Unknown action_type: {action_type}")
