"""Stage 9 extras periodic tasks."""
import logging

from app.workers.async_runner import run_async
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run(coro):
    return run_async(coro)


@celery_app.task(name="stage9.deliver_external_webhooks")
def deliver_external_webhooks(limit: int = 25) -> int:
    from app.services.external_webhooks import claim_pending_deliveries, deliver_one

    async def _do() -> int:
        ids = await claim_pending_deliveries(limit=limit)
        n = 0
        for delivery_id in ids:
            ok, _ = await deliver_one(delivery_id)
            if ok:
                n += 1
        return n

    n = _run(_do())
    if n:
        logger.info("external webhooks delivered: %d", n)
    return n


@celery_app.task(name="stage9.evaluate_idle")
def evaluate_idle_task() -> int:
    from app.services.presence_idle import evaluate_idle

    n = _run(evaluate_idle())
    if n:
        logger.info("idle worker flipped: %d agents", n)
    return n


@celery_app.task(name="stage9.expire_conversation_locks")
def expire_conversation_locks() -> int:
    from app.core.database import AsyncSessionLocal
    from app.services.conversation_lock import expire_locks

    async def _do() -> int:
        async with AsyncSessionLocal() as db:
            n = await expire_locks(db)
            await db.commit()
            return n

    n = _run(_do())
    if n:
        logger.info("expired %d conversation locks", n)
    return n
