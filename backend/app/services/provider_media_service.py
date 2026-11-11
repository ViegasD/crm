import logging
import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.encryption import decrypt_payload
from app.models.channel import ChannelAccount, ChannelCredential
from app.models.conversation import Message, MessageIdentity
from app.models.enums import WhatsAppProvider
from app.workers.tasks.media import download_and_store_media


logger = logging.getLogger(__name__)


_BASE64_RE = re.compile(r"^[A-Za-z0-9+/=\r\n]+$")


@dataclass
class ResolvedMediaDownload:
    provider_url: str
    mime_type: str
    original_filename: str
    minio_key: str
    minio_bucket: str
    provider_method: str = "GET"
    provider_headers: dict | None = None
    provider_payload: dict | None = None
    response_kind: str = "binary"
    inline_base64: str | None = None


def normalize_inbound_attachments(
    provider: str,
    message_type: str,
    attachments: list[dict] | None,
) -> list[dict]:
    normalized: list[dict] = []
    for index, attachment in enumerate(attachments or []):
        item = dict(attachment)
        item_type = str(item.get("type") or message_type or "file")
        payload = item.get("provider_payload") if isinstance(item.get("provider_payload"), dict) else {}
        mime_type = item.get("mimeType") or item.get("mime_type") or payload.get("mimetype") or payload.get("mime_type")
        provider_media_id = item.get("providerMediaId") or item.get("provider_media_id")
        name = item.get("name") or item.get("filename") or payload.get("fileName") or payload.get("filename")
        source_url = item.get("sourceUrl") or item.get("source_url") or payload.get("url")
        embedded_base64 = _extract_inline_base64(item, payload)

        normalized.append(
            {
                **item,
                "provider": item.get("provider") or provider,
                "type": item_type,
                "mimeType": mime_type,
                "providerMediaId": provider_media_id,
                "name": name or _default_filename(item_type, mime_type, provider_media_id, index),
                "sourceUrl": source_url,
                "base64": embedded_base64,
                "ready": bool(item.get("ready", False)),
            }
        )

    return normalized


async def enqueue_inbound_media_downloads(
    db: AsyncSession,
    channel_account: ChannelAccount,
    message: Message,
) -> None:
    for index, attachment in enumerate(message.attachments or []):
        resolved = await resolve_inbound_media_download(db, channel_account, message.id, index, attachment)
        if not resolved:
            continue

        download_and_store_media.delay(
            workspace_id=str(message.workspace_id),
            message_id=str(message.id),
            attachment_index=index,
            provider_url=resolved.provider_url,
            provider_method=resolved.provider_method,
            provider_headers=resolved.provider_headers,
            provider_payload=resolved.provider_payload,
            response_kind=resolved.response_kind,
            mime_type=resolved.mime_type,
            original_filename=resolved.original_filename,
            minio_key=resolved.minio_key,
            minio_bucket=resolved.minio_bucket,
        )


async def resolve_inbound_media_download(
    db: AsyncSession,
    channel_account: ChannelAccount,
    message_id: UUID,
    attachment_index: int,
    attachment: dict,
) -> ResolvedMediaDownload | None:
    provider = attachment.get("provider") or (
        channel_account.provider.value if channel_account.provider else None
    )
    if provider == WhatsAppProvider.meta_cloud.value:
        provider_media_id = attachment.get("providerMediaId") or attachment.get("provider_media_id")
        if not provider_media_id:
            return None

        creds = await _get_channel_credentials(db, channel_account.id, "meta_cloud")
        access_token = creds.get("access_token")
        if not access_token:
            return None

        meta_media = await _fetch_meta_media(provider_media_id, access_token)
        mime_type = str(meta_media.get("mime_type") or attachment.get("mimeType") or "application/octet-stream")
        name = str(
            attachment.get("name")
            or _default_filename(
                str(attachment.get("type") or "file"),
                mime_type,
                provider_media_id,
                attachment_index,
            )
        )

        return ResolvedMediaDownload(
            provider_url=str(meta_media["url"]),
            provider_headers={"Authorization": f"Bearer {access_token}"},
            mime_type=mime_type,
            original_filename=name,
            minio_key=_build_minio_key(channel_account.workspace_id, message_id, attachment_index, name),
            minio_bucket=settings.minio_bucket,
        )

    if provider not in {
        WhatsAppProvider.evolution_baileys.value,
        WhatsAppProvider.evolution_cloud.value,
    }:
        return None

    source_url = attachment.get("sourceUrl") or attachment.get("source_url")
    embedded_base64 = _extract_inline_base64(attachment, attachment.get("provider_payload"))
    mime_type = str(attachment.get("mimeType") or "application/octet-stream")
    name = str(
        attachment.get("name")
        or _default_filename(
            str(attachment.get("type") or "file"),
            mime_type,
            attachment.get("providerMediaId") or attachment.get("provider_media_id"),
            attachment_index,
        )
    )

    if embedded_base64:
        logger.info(
            "Using embedded webhook base64 for inbound media message_id=%s attachment_index=%s type=%s",
            message_id,
            attachment_index,
            attachment.get("type"),
        )
        return ResolvedMediaDownload(
            provider_url="",
            mime_type=mime_type,
            original_filename=name,
            minio_key=_build_minio_key(channel_account.workspace_id, message_id, attachment_index, name),
            minio_bucket=settings.minio_bucket,
            response_kind="inline_base64",
            inline_base64=str(embedded_base64),
        )

    provider_message_id = await _get_provider_message_id(
        db,
        message_id,
        channel_account.id,
        attachment,
    )
    if not provider_message_id:
        return None

    creds = await _get_channel_credentials(db, channel_account.id, "evolution")
    api_key = creds.get("evolution_api_key") or settings.evolution_api_key
    if not api_key:
        return None

    base_url = str(
        creds.get("evolution_api_url")
        or creds.get("evolution_base_url")
        or settings.evolution_api_url
    ).rstrip("/")
    instance_name = str(creds.get("evolution_instance_id") or channel_account.external_account_id or "")
    if not instance_name:
        return None

    logger.info(
        "Using Evolution getBase64FromMediaMessage for inbound media message_id=%s attachment_index=%s type=%s has_source_url=%s",
        message_id,
        attachment_index,
        attachment.get("type"),
        bool(source_url),
    )

    return ResolvedMediaDownload(
        provider_url=f"{base_url}/chat/getBase64FromMediaMessage/{instance_name}",
        provider_method="POST",
        provider_headers={"apikey": api_key, "Content-Type": "application/json"},
        provider_payload={
            "message": {"key": {"id": provider_message_id}},
            "convertToMp4": str(attachment.get("type") or "") == "video",
        },
        response_kind="json_base64",
        mime_type=mime_type,
        original_filename=name,
        minio_key=_build_minio_key(channel_account.workspace_id, message_id, attachment_index, name),
        minio_bucket=settings.minio_bucket,
    )


async def _get_channel_credentials(
    db: AsyncSession, channel_account_id: UUID, credential_type: str
) -> dict:
    result = await db.execute(
        select(ChannelCredential).where(
            ChannelCredential.channel_account_id == channel_account_id,
            ChannelCredential.credential_type == credential_type,
        )
    )
    cred = result.scalar_one_or_none()
    if not cred:
        return {}
    return decrypt_payload(cred.encrypted_payload)


async def _fetch_meta_media(provider_media_id: str, access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(
            f"https://graph.facebook.com/v20.0/{provider_media_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


async def _get_provider_message_id(
    db: AsyncSession,
    message_id: UUID,
    channel_account_id: UUID,
    attachment: dict,
) -> str | None:
    provider_message_id = attachment.get("providerMessageId") or attachment.get("provider_message_id")
    if provider_message_id:
        return str(provider_message_id)

    result = await db.execute(
        select(MessageIdentity.external_message_id).where(
            MessageIdentity.message_id == message_id,
            MessageIdentity.channel_account_id == channel_account_id,
            MessageIdentity.direction == "inbound",
        )
    )
    return result.scalar_one_or_none()


def _build_minio_key(
    workspace_id: UUID, message_id: UUID, attachment_index: int, original_filename: str
) -> str:
    safe_name = Path(original_filename).name or f"attachment-{attachment_index}"
    return f"{workspace_id}/{message_id}/{attachment_index}-{safe_name}"


def _default_filename(
    message_type: str,
    mime_type: str | None,
    provider_media_id: str | None,
    attachment_index: int,
) -> str:
    extension = mimetypes.guess_extension(mime_type or "") or ""
    stem = provider_media_id or f"attachment-{attachment_index}"
    prefix = message_type if message_type in {"image", "audio", "video", "file"} else "attachment"
    return f"{prefix}-{stem}{extension}"


def _find_base64_value(payload) -> str | None:
    if isinstance(payload, str):
        candidate = payload.strip()
        if not candidate:
            return None
        if candidate.startswith(("http://", "https://")):
            return None
        if candidate.startswith("data:"):
            return candidate
        if len(candidate) >= 64 and _BASE64_RE.fullmatch(candidate):
            return candidate
        return None
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


def _extract_inline_base64(attachment: dict, payload: dict | None) -> str | None:
    for candidate in (attachment.get("base64"), attachment.get("data"), payload):
        value = _find_base64_value(candidate)
        if value:
            return value
    return None