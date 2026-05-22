"""Variable interpolation for canned response templates.

Syntax:
- `{{namespace.field}}` - simple variable
- `{{date.today}}` / `{{date.tomorrow}}` / `{{date.now}}` - date helpers
- `{{#if contact.vip}}…{{/if}}` - conditional block (truthy on context value)

Unknown placeholders are kept verbatim so the agent can fix them before sending.
"""
import re
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact, ContactEmail, ContactPhone
from app.models.conversation import Conversation
from app.models.workspace import User

_PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")
_CONDITIONAL = re.compile(
    r"\{\{\s*#if\s+([a-zA-Z0-9_.]+)\s*\}\}(.*?)\{\{\s*/if\s*\}\}",
    re.DOTALL,
)


def _date_helpers(now: datetime | None = None) -> dict[str, str]:
    now = now or datetime.now(timezone.utc)
    return {
        "date.today": now.strftime("%d/%m/%Y"),
        "date.tomorrow": (now + timedelta(days=1)).strftime("%d/%m/%Y"),
        "date.yesterday": (now - timedelta(days=1)).strftime("%d/%m/%Y"),
        "date.now": now.strftime("%d/%m/%Y %H:%M"),
        "date.weekday": now.strftime("%A"),
    }


async def build_render_context(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    conversation_id: UUID | None,
    agent: User | None,
) -> dict[str, str]:
    ctx: dict[str, str] = {}
    ctx.update(_date_helpers())
    if agent:
        ctx["agent.name"] = agent.name
        ctx["agent.email"] = agent.email
        ctx["agent.first_name"] = agent.name.split()[0] if agent.name else ""
    if not conversation_id:
        return ctx
    conv = await db.get(Conversation, conversation_id)
    if not conv or conv.workspace_id != workspace_id:
        return ctx
    ctx["conversation.id"] = str(conv.id)
    ctx["conversation.protocol"] = str(conv.id)[:8].upper()
    ctx["conversation.status"] = conv.status.value if hasattr(conv.status, "value") else str(conv.status)
    ctx["conversation.priority"] = conv.priority.value if hasattr(conv.priority, "value") else str(conv.priority)

    if conv.contact_id:
        contact = await db.get(Contact, conv.contact_id)
        if contact:
            ctx["contact.name"] = contact.name or ""
            ctx["contact.first_name"] = (contact.name or "").split()[0] if contact.name else ""
            if hasattr(contact, "priority") and contact.priority:
                ctx["contact.vip"] = "1"
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
            ctx.setdefault("assignee.first_name", assignee.name.split()[0] if assignee.name else "")
    return ctx


def _resolve_value(context: dict[str, str], key: str) -> str | None:
    if key in context:
        return context[key]
    lower = key.lower()
    for k, v in context.items():
        if k.lower() == lower:
            return v
    return None


def render_template(template: str, context: dict[str, str]) -> str:
    # Conditional blocks first
    def _cond(match: re.Match[str]) -> str:
        key = match.group(1)
        body = match.group(2)
        value = _resolve_value(context, key)
        if value and value not in ("0", "false", "False", ""):
            return body
        return ""

    rendered = _CONDITIONAL.sub(_cond, template)

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        value = _resolve_value(context, key)
        return value if value is not None else match.group(0)

    return _PLACEHOLDER.sub(_replace, rendered)
