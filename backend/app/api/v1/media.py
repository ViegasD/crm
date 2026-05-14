import io
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.minio import delete_object, ensure_bucket, generate_presigned_url, get_minio_client, upload_file
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


@router.post("/upload")
async def upload_media(
    file: UploadFile,
    workspace_id: str = Query(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported media type")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50 MB hard limit
        raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

    key = f"{workspace_id}/{uuid.uuid4()}/{file.filename}"
    await ensure_bucket(BUCKET)
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
