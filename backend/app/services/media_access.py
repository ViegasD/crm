"""Ownership checks and short-lived browser capabilities for private media."""
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import UUID

from fastapi import HTTPException
from jose import jwt
from sqlalchemy import and_, or_, select

from app.core.config import settings
from app.core.conversation_access import conversation_access_clause, require_conversation, require_workspace_user
from app.core.security import ALGORITHM
from app.models.conversation import CannedResponse, Message, Conversation
from app.models.macros import Macro, MacroAction
from app.models.enums import CannedVisibility
from app.models.workspace import SectorMember
from app.models.media import MediaUpload

DOWNLOAD_TTL_SECONDS = 300
DRAFT_TTL_HOURS = 24


def validate_key(key):
    if not isinstance(key, str) or not key or len(key) > 1024 or "\\" in key:
        raise HTTPException(status_code=400, detail="Invalid storage key")
    parts = key.split("/")
    if len(parts) < 3 or any(part in {"", ".", ".."} for part in parts):
        raise HTTPException(status_code=400, detail="Invalid storage key")
    try:
        UUID(parts[0])
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid storage key")
    return key


def download_url(user_id, *, upload_id=None, message_id=None, index=None, template_key=None):
    payload = {"type": "media_download", "sub": str(user_id),
               "exp": datetime.now(timezone.utc) + timedelta(seconds=DOWNLOAD_TTL_SECONDS)}
    if template_key is not None:
        payload["template_key"] = template_key
    elif upload_id is not None:
        payload["upload_id"] = str(upload_id)
    else:
        payload.update({"message_id": str(message_id), "index": index})
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    return "/api/v1/media/download?" + urlencode({"token": token})


def safe_attachment_metadata(attachment):
    # Actual inbound payloads retain sourceUrl, nested provider_payload and
    # inline base64. An allowlist prevents new provider fields becoming leaks.
    allowed = {"key", "bucket", "name", "mimeType", "mime_type", "sizeBytes", "size_bytes", "type", "ready"}
    return {k: v for k, v in attachment.items() if k in allowed and isinstance(v, (str, int, float, bool, type(None)))}


def attachment_for_browser(attachment, message, index, user_id=None):
    item = safe_attachment_metadata(attachment)
    key = item.get("key")
    if key and item.get("bucket") == settings.minio_bucket:
        item["ready"] = True
        if user_id is not None:
            item["url"] = download_url(user_id, message_id=message.id, index=index)
    else:
        item["ready"] = False
    return item


async def authorize_upload(db, upload, user_id):
    if upload is None:
        raise HTTPException(status_code=404, detail="Media not found")
    await require_workspace_user(db, upload.workspace_id, user_id)
    if await reusable_attachment(db, upload.workspace_id, upload.key, user_id) is not None:
        return upload
    if upload.conversation_id is not None:
        await require_conversation(db, upload.workspace_id, upload.conversation_id, user_id)
    elif upload.owner_id != user_id or upload.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=404, detail="Media not found")
    return upload


async def authorize_message_attachment(db, message, index, user_id):
    if message is None or not isinstance(index, int) or index < 0 or index >= len(message.attachments):
        raise HTTPException(status_code=404, detail="Media not found")
    await require_conversation(db, message.workspace_id, message.conversation_id, user_id)
    attachment = message.attachments[index]
    key = validate_key(attachment.get("key"))
    if attachment.get("bucket") != settings.minio_bucket:
        raise HTTPException(status_code=404, detail="Media not found")
    # Prefix is structural validation; authorization comes from the stored
    # message/conversation relationship, supporting existing inbound media keys.
    if UUID(key.split("/")[0]) != message.workspace_id:
        raise HTTPException(status_code=404, detail="Media not found")
    return attachment


async def url_for_key(db, key, user_id):
    validate_key(key)
    upload = await db.scalar(select(MediaUpload).where(MediaUpload.key == key))
    if upload is not None:
        await authorize_upload(db, upload, user_id)
        return download_url(user_id, upload_id=upload.id)
    workspace_id = UUID(key.split("/")[0])
    if await reusable_attachment(db, workspace_id, key, user_id) is not None:
        return download_url(user_id, template_key=key)
    # Existing provider/legacy attachments have no upload registry entry.
    # Only a persisted message visible to this user can prove their ownership.
    messages = (await db.scalars(select(Message).where(
        Message.workspace_id == workspace_id,
        Message.attachments.contains([{"key": key, "bucket": settings.minio_bucket}]),
        Message.conversation_id.in_(select(Conversation.id).where(conversation_access_clause(workspace_id, user_id))),
    ))).all()
    for message in messages:
        for index, attachment in enumerate(message.attachments):
            if attachment.get("key") == key:
                await authorize_message_attachment(db, message, index, user_id)
                return download_url(user_id, message_id=message.id, index=index)
    raise HTTPException(status_code=404, detail="Media not found")


async def bind_attachments(db, workspace_id, conversation_id, user_id, attachments):
    if not attachments:
        return []
    await require_conversation(db, workspace_id, conversation_id, user_id)
    normalized = []
    bindings = []
    for attachment in attachments:
        key = validate_key(attachment.get("key"))
        reusable = await reusable_attachment(db, workspace_id, key, user_id)
        if reusable is not None:
            normalized.append(reusable)
            continue
        # Serialize competing attempts to bind an upload to different records.
        upload = await db.scalar(select(MediaUpload).where(MediaUpload.key == key).with_for_update())
        if upload is None or upload.workspace_id != workspace_id:
            raise HTTPException(status_code=404, detail="Media not found")
        if upload.conversation_id is None:
            if upload.owner_id != user_id or upload.expires_at <= datetime.now(timezone.utc):
                raise HTTPException(status_code=404, detail="Media not found")
            bindings.append(upload)
        elif upload.conversation_id != conversation_id:
            raise HTTPException(status_code=404, detail="Media not found")
        normalized.append({"key": upload.key, "bucket": upload.bucket, "name": upload.name,
                           "mimeType": upload.mime_type, "sizeBytes": upload.size_bytes, "ready": True})
    # A macro catches per-action failures. Do not leave earlier uploads bound
    # when any later attachment in the batch fails validation.
    for upload in bindings:
        upload.conversation_id = conversation_id
    return normalized


def template_visibility(model, workspace_id, user_id, *, active_only=True):
    sectors = select(SectorMember.sector_id).where(SectorMember.workspace_id == workspace_id, SectorMember.user_id == user_id)
    return and_(model.workspace_id == workspace_id, model.active.is_(True) if active_only else True, or_(
        model.visibility == CannedVisibility.workspace,
        and_(model.visibility == CannedVisibility.user, model.user_id == user_id),
        and_(model.visibility == CannedVisibility.sector, model.sector_id.in_(sectors)),
    ))


async def require_template_scope(db, model, workspace_id, identity, user_id):
    template = await db.scalar(select(model).where(model.id == identity,
        template_visibility(model, workspace_id, user_id, active_only=False)))
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


async def validate_template_destination(db, workspace_id, user_id, visibility, sector_id):
    from app.models.workspace import Sector
    if sector_id is not None:
        sector = await db.get(Sector, sector_id)
        if sector is None or sector.workspace_id != workspace_id:
            raise HTTPException(status_code=404, detail="Sector not found")
    if visibility == CannedVisibility.sector:
        member = await db.scalar(select(SectorMember.id).where(SectorMember.workspace_id == workspace_id,
            SectorMember.sector_id == sector_id, SectorMember.user_id == user_id))
        if member is None:
            raise HTTPException(status_code=403, detail="Sector access required")


async def reusable_attachment(db, workspace_id, key, user_id):
    """Only an authorized, persisted template grants cross-conversation reuse.

    Template saves validate their source first. Historical templates can prove
    existing storage-key access, but never authorize external URLs or buckets.
    """
    if UUID(key.split("/")[0]) != workspace_id:
        return None
    await require_workspace_user(db, workspace_id, user_id)
    canned = (await db.scalars(select(CannedResponse).where(
        template_visibility(CannedResponse, workspace_id, user_id),
        CannedResponse.attachments.contains([{"key": key}]),
    ))).all()
    actions = (await db.scalars(select(MacroAction).join(Macro, Macro.id == MacroAction.macro_id).where(
        template_visibility(Macro, workspace_id, user_id),
        MacroAction.params["attachments"].contains([{"key": key}]),
    ))).all()
    candidates = [a for response in canned for a in response.attachments]
    candidates += [a for action in actions for a in action.params.get("attachments", [])]
    for attachment in candidates:
        if attachment.get("key") == key and attachment.get("bucket", settings.minio_bucket) == settings.minio_bucket:
            upload = await db.scalar(select(MediaUpload).where(MediaUpload.key == key, MediaUpload.workspace_id == workspace_id))
            if upload is not None:
                return {"key": key, "bucket": upload.bucket, "name": upload.name,
                        "mimeType": upload.mime_type, "sizeBytes": upload.size_bytes, "ready": True}
            return {**safe_attachment_metadata(attachment), "key": key, "bucket": settings.minio_bucket, "ready": True}
    return None


async def prepare_template_attachments(db, workspace_id, user_id, attachments):
    """Validate before publishing an upload/visible legacy file as reusable."""
    canonical = []
    for attachment in attachments:
        if hasattr(attachment, "model_dump"):
            attachment = attachment.model_dump()
        key = validate_key(attachment.get("key"))
        if UUID(key.split("/")[0]) != workspace_id:
            raise HTTPException(status_code=404, detail="Media not found")
        await url_for_key(db, key, user_id)
        upload = await db.scalar(select(MediaUpload).where(MediaUpload.key == key))
        if upload is not None:
            canonical.append({"key": key, "bucket": upload.bucket, "name": upload.name,
                              "mimeType": upload.mime_type, "sizeBytes": upload.size_bytes, "ready": True})
        else:
            canonical.append({"key": key, "bucket": settings.minio_bucket, "name": key.rsplit("/", 1)[-1], "ready": True})
    return canonical


async def prepare_macro_actions(db, workspace_id, user_id, actions):
    result = []
    for action in actions:
        data = action.model_dump() if hasattr(action, "model_dump") else dict(action)
        params = dict(data.get("params") or {})
        if params.get("attachments"):
            params["attachments"] = await prepare_template_attachments(db, workspace_id, user_id, params["attachments"])
        data["params"] = params
        result.append(data)
    return result
