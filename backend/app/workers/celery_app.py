from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "crm_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.tasks.media",
        "app.workers.tasks.webhook_retry",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "webhook-retry-every-30s": {
            "task": "webhook.retry_pending",
            "schedule": 30.0,
        },
        "webhook-alert-every-minute": {
            "task": "webhook.alert_check",
            "schedule": 60.0,
        },
        "webhook-purge-daily": {
            "task": "webhook.purge_old_events",
            "schedule": crontab(hour=3, minute=0),
        },
        "snooze-expire-every-minute": {
            "task": "webhook.snooze_expire",
            "schedule": 60.0,
        },
    },
)
