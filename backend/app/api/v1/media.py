import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_workspace_member
from app.core.minio import ensure_bucket, read_file, upload_file
from app.core.security import decode_token
from app.models.conversation import Message
from app.models.media import MediaUpload
from app.models.workspace import User
from app.services.media_access import (
    DRAFT_TTL_HOURS, authorize_message_attachment, authorize_upload, download_url, url_for_key,
    reusable_attachment, validate_key,
)

router = APIRouter(prefix="/media", tags=["media"])

ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "audio/mpeg", "audio/ogg", "audio/wav",
    "video/mp4", "video/webm",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

BUCKET = settings.minio_bucket
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def _validate_upload(file: UploadFile, content: bytes) -> None:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported media type")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    if len(file.filename) > 255 or any(c in file.filename for c in ("/", "\\", "\r", "\n", "\x00")) or file.filename in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid filename")

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 25 MB)")


@router.post("/upload")
async def upload_media(
    file: UploadFile,
    workspace_id: uuid.UUID = Query(...),
    current_user: Annotated[User, Depends(require_workspace_member)] = None,
    db: AsyncSession = Depends(get_db),
):
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    _validate_upload(file, content)

    key = f"{workspace_id}/{uuid.uuid4()}/{file.filename}"
    await run_in_threadpool(ensure_bucket, BUCKET)
    await run_in_threadpool(upload_file, BUCKET, key, content, file.content_type)

    upload = MediaUpload(id=uuid.uuid4(), workspace_id=workspace_id, owner_id=current_user.id,
        key=key, bucket=BUCKET, name=file.filename, mime_type=file.content_type, size_bytes=len(content),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=DRAFT_TTL_HOURS))
    db.add(upload)
    await db.flush()
    return {"key": key, "url": download_url(current_user.id, upload_id=upload.id)}


@router.get("/presign")
async def presign(
    key: str = Query(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: AsyncSession = Depends(get_db),
):
    return {"url": await url_for_key(db, key, current_user.id)}


@router.get("/download")
async def download_media(token: str = Query(..., max_length=4096), db: AsyncSession = Depends(get_db)):
    """A scoped browser capability, reauthorized against current DB state.

    No redirect to storage: that would bypass revocation for the redirect TTL.
    Old storage URLs cannot be revoked retroactively; only new URLs use this path.
    """
    try:
        payload = decode_token(token)
        if payload.get("type") != "media_download":
            raise ValueError
        user_id = uuid.UUID(payload["sub"])
        if await db.get(User, user_id) is None:
            raise ValueError
        if "template_key" in payload:
            key = validate_key(payload["template_key"])
            workspace_id = uuid.UUID(key.split("/")[0])
            attachment = await reusable_attachment(db, workspace_id, key, user_id)
            if attachment is None:
                raise HTTPException(status_code=404, detail="Media not found")
            bucket = attachment["bucket"]
            mime = attachment.get("mimeType") or attachment.get("mime_type") or "application/octet-stream"
        elif "upload_id" in payload:
            upload = await db.get(MediaUpload, uuid.UUID(payload["upload_id"]))
            await authorize_upload(db, upload, user_id)
            key, bucket, mime = upload.key, upload.bucket, upload.mime_type
        else:
            message = await db.get(Message, uuid.UUID(payload["message_id"]))
            attachment = await authorize_message_attachment(db, message, payload["index"], user_id)
            key, bucket = attachment["key"], attachment["bucket"]
            mime = attachment.get("mimeType") or attachment.get("mime_type") or "application/octet-stream"
    except (JWTError, ValueError, KeyError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid or expired media token")
    try:
        content = await run_in_threadpool(read_file, bucket, key, MAX_UPLOAD_BYTES)
    except (KeyError, ValueError):
        raise HTTPException(status_code=404, detail="Media not found")
    if mime not in ALLOWED_MIME_TYPES:
        mime = "application/octet-stream"
    return Response(content=content, media_type=mime, headers={
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
    })
