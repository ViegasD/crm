"""Periodic Celery tasks for webhook_events retry, retention and alerting."""
import logging

from app.workers.async_runner import run_async
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run(coro):
    """Run an async function from a sync Celery task safely."""
    return run_async(coro)


@celery_app.task(name="webhook.retry_pending")
def retry_pending_events(limit: int = 25) -> int:
    """Pick up to `limit` failed/received events and try to process them."""
    from app.services.webhook_retry import claim_pending_events, reprocess_event

    async def _do() -> int:
        ids = await claim_pending_events(limit=limit)
        processed = 0
        for event_id in ids:
            ok, _ = await reprocess_event(event_id)
            if ok:
                processed += 1
        return processed

    count = _run(_do())
    if count:
        logger.info("webhook retry processed %d events", count)
    return count


@celery_app.task(name="webhook.purge_old_events")
def purge_old_events(days: int = 30) -> int:
    """Delete processed/ignored webhook events older than `days`.

    `failed` and `dead_letter` are kept indefinitely (until manually resolved
    or moved by a workspace policy).
    """
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import delete as sa_delete

    from app.core.database import AsyncSessionLocal
    from app.models.enums import WebhookEventStatus
    from app.models.webhook import WebhookEvent

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    async def _do() -> int:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                sa_delete(WebhookEvent).where(
                    WebhookEvent.status.in_(
                        [WebhookEventStatus.processed, WebhookEventStatus.ignored]
                    ),
                    WebhookEvent.created_at < cutoff,
                )
            )
            await db.commit()
            return result.rowcount or 0

    n = _run(_do())
    if n:
        logger.info("webhook retention deleted %d events older than %dd", n, days)
    return n


@celery_app.task(name="webhook.snooze_expire")
def snooze_expire() -> int:
    """Delete expired conversation snoozes so conversations resurface."""
    from app.services.snooze_worker import expire_snoozes

    n = _run(expire_snoozes())
    if n:
        logger.info("snooze expiry removed %d rows", n)
    return n


@celery_app.task(name="webhook.alert_check")
def alert_check(window_minutes: int = 5, threshold: float = 0.05) -> int:
    """Check failure rate per channel_account; raise a security audit event
    when ratio > threshold (default 5%). Logs once per window/channel."""
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import case, func, select

    from app.core.database import AsyncSessionLocal
    from app.models.enums import WebhookEventStatus
    from app.models.webhook import WebhookEvent

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

    async def _do() -> int:
        from app.services.security_audit_service import log_security_event

        triggered = 0
        async with AsyncSessionLocal() as db:
            q = (
                select(
                    WebhookEvent.channel_account_id,
                    WebhookEvent.workspace_id,
                    func.count().label("total"),
                    func.sum(
                        case(
                            (
                                WebhookEvent.status.in_(
                                    [WebhookEventStatus.failed, WebhookEventStatus.dead_letter]
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ).label("failed"),
                )
                .where(WebhookEvent.created_at >= cutoff)
                .group_by(WebhookEvent.channel_account_id, WebhookEvent.workspace_id)
            )
            for channel_account_id, workspace_id, total, failed in (await db.execute(q)).all():
                if not total or total < 5:
                    continue
                ratio = (failed or 0) / total
                if ratio >= threshold:
                    await log_security_event(
                        action="webhook_failure_rate_alert",
                        workspace_id=workspace_id,
                        target_type="channel_account",
                        target_id=channel_account_id,
                        new_value={
                            "window_minutes": window_minutes,
                            "total": int(total),
                            "failed": int(failed or 0),
                            "ratio": round(ratio, 3),
                            "threshold": threshold,
                        },
                    )
                    triggered += 1
        return triggered

    return _run(_do())
