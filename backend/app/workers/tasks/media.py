"""
Media worker tasks.

download_provider_media: Downloads a media file from a provider's temporary URL
(e.g. Meta Graph API media URL) and re-uploads to MinIO. Updates the message
attachments field when done.
"""
import logging
from uuid import UUID

import httpx

from app.core.minio import upload_file
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def download_and_store_media(
    self,
    workspace_id: str,
    message_id: str,
    attachment_index: int,
    provider_url: str,
    provider_access_token: str | None,
    mime_type: str,
    original_filename: str | None,
    minio_key: str,
    minio_bucket: str,
):
    """Download media from provider URL and store in MinIO."""
    try:
        headers = {}
        if provider_access_token:
            headers["Authorization"] = f"Bearer {provider_access_token}"

        with httpx.Client(timeout=30) as client:
            r = client.get(provider_url, headers=headers, follow_redirects=True)
            r.raise_for_status()
            data = r.content

        upload_file(minio_bucket, minio_key, data, mime_type)
        logger.info("Stored media %s in bucket %s", minio_key, minio_bucket)

        # Update message attachments in DB (sync via separate session)
        _update_message_attachment(message_id, attachment_index, minio_key, minio_bucket)

    except Exception as exc:
        logger.error("Failed to download media for message %s: %s", message_id, exc)
        raise self.retry(exc=exc)


def _update_message_attachment(
    message_id: str, attachment_index: int, key: str, bucket: str
) -> None:
    """Synchronous DB update — runs in Celery worker process."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.core.config import settings
    from app.models.conversation import Message

    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    with Session(engine) as session:
        msg = session.get(Message, UUID(message_id))
        if msg:
            attachments = list(msg.attachments)
            if attachment_index < len(attachments):
                attachments[attachment_index].update({"key": key, "bucket": bucket, "ready": True})
                msg.attachments = attachments
                session.commit()
    engine.dispose()
