import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import WebhookEventStatus


class WebhookEventOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID | None
    channel_account_id: uuid.UUID | None
    provider: str
    signature_hash: str | None
    status: WebhookEventStatus
    attempts: int
    max_attempts: int
    error_message: str | None
    next_retry_at: datetime | None
    last_error_at: datetime | None
    created_at: datetime
    processed_at: datetime | None


class WebhookEventDetail(WebhookEventOut):
    headers: dict
    payload: dict


class WebhookRetryResult(BaseModel):
    success: bool
    error: str | None = None
