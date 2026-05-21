"""Variable interpolation for canned response templates.

Supports the placeholder syntax `{{namespace.field}}` (case-insensitive on the
namespace). Unknown placeholders are kept verbatim so the agent can fix them
before sending.
"""
import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact, ContactEmail, ContactPhone
from app.models.conversation import Conversation
from app.models.workspace import User

_PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")


async def build_render_context(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    conversation_id: UUID | None,
    agent: User | None,
) -> dict[str, str]:
    ctx: dict[str, str] = {}
    if agent:
        ctx["agent.name"] = agent.name
        ctx["agent.email"] = agent.email
    if not conversation_id:
        return ctx
    conv = await db.get(Conversation, conversation_id)
    if not conv or conv.workspace_id != workspace_id:
        return ctx
    ctx["conversation.id"] = str(conv.id)
    ctx["conversation.protocol"] = str(conv.id)[:8].upper()
    ctx["conversation.status"] = conv.status.value if hasattr(conv.status, "value") else str(conv.status)

    if conv.contact_id:
        contact = await db.get(Contact, conv.contact_id)
        if contact:
            ctx["contact.name"] = contact.name or ""
            phone = (await db.execute(
                select(ContactPhone)
                .where(ContactPhone.contact_id == contact.id)
                .order_by(ContactPhone.is_primary.desc(), ContactPhone.created_at.asc())
                .limit(1)
            )).scalar_one_or_none()
            if phone:
                ctx["contact.phone"] = phone.phone
            email = (await db.execute(
                select(ContactEmail)
                .where(ContactEmail.contact_id == contact.id)
                .order_by(ContactEmail.is_primary.desc(), ContactEmail.created_at.asc())
                .limit(1)
            )).scalar_one_or_none()
            if email:
                ctx["contact.email"] = email.email
    if conv.assignee_id:
        assignee = await db.get(User, conv.assignee_id)
        if assignee:
            ctx.setdefault("assignee.name", assignee.name)
    return ctx


def render_template(template: str, context: dict[str, str]) -> str:
    def _replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        if key in context:
            return context[key]
        # case-insensitive fallback
        lower = key.lower()
        for k, v in context.items():
            if k.lower() == lower:
                return v
        return match.group(0)

    return _PLACEHOLDER.sub(_replace, template)
