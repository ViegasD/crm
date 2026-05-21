from uuid import UUID

import logging
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import AsyncSessionLocal
from app.models.audit import SecurityAuditLog

logger = logging.getLogger(__name__)


async def log_security_event(
    *,
    action: str,
    workspace_id: UUID | None = None,
    user_id: UUID | None = None,
    target_type: str | None = None,
    target_id: UUID | None = None,
    old_value: dict | None = None,
    new_value: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Persist security audit events independently from request rollback."""
    try:
        async with AsyncSessionLocal() as db:
            db.add(
                SecurityAuditLog(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    action=action,
                    target_type=target_type,
                    target_id=target_id,
                    old_value=old_value,
                    new_value=new_value,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            )
            await db.commit()
    except SQLAlchemyError:
        logger.exception("Failed to persist security audit event: %s", action)
