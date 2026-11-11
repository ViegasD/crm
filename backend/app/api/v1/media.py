import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.minio import ensure_bucket, generate_presigned_url, upload_file
from app.models.workspace import User

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

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 25 MB)")


@router.post("/upload")
async def upload_media(
    file: UploadFile,
    workspace_id: str = Query(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    content = await file.read()
    _validate_upload(file, content)

    key = f"{workspace_id}/{uuid.uuid4()}/{file.filename}"
    ensure_bucket(BUCKET)
    upload_file(BUCKET, key, content, file.content_type)

    presigned = generate_presigned_url(BUCKET, key)
    return {"key": key, "url": presigned}


@router.get("/presign")
async def presign(
    key: str = Query(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    url = generate_presigned_url(BUCKET, key)
    return {"url": url}
