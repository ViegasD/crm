"""
Media worker tasks.

download_provider_media: Downloads a media file from a provider's temporary URL
(e.g. Meta Graph API media URL) and re-uploads to MinIO. Updates the message
attachments field when done.
"""
import base64
import logging
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID

import httpx

from app.core.minio import generate_presigned_url, upload_file
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _normalize_provider_url(provider_url: str) -> str:
    parts = urlsplit(provider_url)
    if parts.hostname not in {"localhost", "127.0.0.1"}:
        return provider_url

    port = f":{parts.port}" if parts.port else ""
    netloc = f"host.docker.internal{port}"
    if parts.username:
        auth = parts.username
        if parts.password:
            auth = f"{auth}:{parts.password}"
        netloc = f"{auth}@{netloc}"

    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def download_and_store_media(
    self,
    workspace_id: str,
    message_id: str,
    attachment_index: int,
    provider_url: str,
    mime_type: str,
    original_filename: str | None,
    minio_key: str,
    minio_bucket: str,
    provider_method: str = "GET",
    provider_headers: dict | None = None,
    provider_payload: dict | None = None,
    response_kind: str = "binary",
    inline_base64: str | None = None,
):
    """Download media from provider URL and store in MinIO."""
    try:
        if response_kind == "inline_base64":
            if not inline_base64:
                raise ValueError("Inline base64 media content was missing")
            data = _decode_base64_value(inline_base64)
        else:
            headers = dict(provider_headers or {})
            request_url = _normalize_provider_url(provider_url)

            with httpx.Client(timeout=30) as client:
                r = client.request(
                    provider_method.upper(),
                    request_url,
                    headers=headers,
                    json=provider_payload,
                    follow_redirects=True,
                )
                r.raise_for_status()
                data = _read_response_bytes(r, response_kind)

        upload_file(minio_bucket, minio_key, data, mime_type)
        logger.info("Stored media %s in bucket %s", minio_key, minio_bucket)

        # Update message attachments in DB (sync via separate session)
        _update_message_attachment(message_id, attachment_index, minio_key, minio_bucket, len(data))

    except Exception as exc:
        logger.error("Failed to download media for message %s: %s", message_id, exc)
        raise self.retry(exc=exc)


def _read_response_bytes(response: httpx.Response, response_kind: str) -> bytes:
    if response_kind == "json_base64":
        payload = response.json()
        encoded = _find_base64_value(payload)
        if not encoded:
            raise ValueError("Provider response did not include base64 media content")
        return _decode_base64_value(encoded)
    return response.content


def _find_base64_value(payload) -> str | None:
    if isinstance(payload, str):
        return payload if payload.strip() else None
    if isinstance(payload, list):
        for item in payload:
            value = _find_base64_value(item)
            if value:
                return value
        return None
    if isinstance(payload, dict):
        for key in ("base64", "data", "message", "media", "file", "buffer"):
            if key in payload:
                value = _find_base64_value(payload[key])
                if value:
                    return value
        for value in payload.values():
            nested = _find_base64_value(value)
            if nested:
                return nested
    return None


def _decode_base64_value(value: str) -> bytes:
    raw = value.strip()
    if raw.startswith("data:"):
        _, _, raw = raw.partition(",")
    return base64.b64decode(raw)


def _update_message_attachment(
    message_id: str, attachment_index: int, key: str, bucket: str, size_bytes: int
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
                attachment = dict(attachments[attachment_index])
                attachment.update(
                    {
                        "key": key,
                        "bucket": bucket,
                        "url": generate_presigned_url(bucket, key),
                        "ready": True,
                        "sizeBytes": size_bytes,
                    }
                )
                attachments[attachment_index] = attachment
                msg.attachments = attachments
                session.commit()
    engine.dispose()
