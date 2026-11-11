"""Periodic SLA and routing operations."""
import logging

from app.core.database import AsyncSessionLocal
from app.services.sla_service import auto_resolve_inactive_conversations, evaluate_workspace_sla
from app.workers.async_runner import run_async
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run(coro):
    return run_async(coro)


@celery_app.task(name="sla.evaluate")
def evaluate_sla() -> int:
    async def _inner() -> int:
        async with AsyncSessionLocal() as db:
            count = await evaluate_workspace_sla(db)
            await db.commit()
            return count

    count = _run(_inner())
    if count:
        logger.info("SLA evaluation processed %d conversations", count)
    return count


@celery_app.task(name="sla.auto_resolve")
def auto_resolve() -> int:
    async def _inner() -> int:
        async with AsyncSessionLocal() as db:
            count = await auto_resolve_inactive_conversations(db)
            await db.commit()
            return count

    count = _run(_inner())
    if count:
        logger.info("Auto-resolved %d inactive conversations", count)
    return count
