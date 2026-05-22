"""Background helper that deletes expired snoozes so conversations resurface."""
from datetime import datetime, timezone

from sqlalchemy import delete as sa_delete

from app.core.database import AsyncSessionLocal
from app.models.catalog import ConversationSnooze


async def expire_snoozes() -> int:
    """Delete all ConversationSnooze rows whose `until` is in the past.

    Returns the number of rows removed. Safe to call from any scheduler/cron.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            sa_delete(ConversationSnooze).where(
                ConversationSnooze.until <= datetime.now(timezone.utc)
            )
        )
        await db.commit()
        return result.rowcount or 0
