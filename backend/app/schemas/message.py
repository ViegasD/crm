import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.services.media_access import attachment_for_browser
from app.models.enums import MessageOrigin, MessageType, SenderType


class AttachmentOut(BaseModel):
    key: str
    bucket: str
    url: str
    name: str
    mime_type: str
    size_bytes: int


class MessageOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_type: SenderType
    sender_id: uuid.UUID
    sender_name: str | None = None
    origin: MessageOrigin
    content: str | None
    type: MessageType
    attachments: list[dict]
    is_read: bool
    provider_status: str | None = None
    provider_status_updated_at: datetime | None = None
    provider_status_error: str | None = None
    created_at: datetime


class SendMessageRequest(BaseModel):
    content: str | None = None
    type: MessageType = MessageType.text
    attachments: list[dict] = []
    # For internal notes
    is_note: bool = False


def serialize_message_out(message: Any, user_id=None) -> MessageOut:
    payload = MessageOut.model_validate(message).model_dump()
    payload["attachments"] = [attachment_for_browser(attachment, message, index, user_id) for index, attachment in enumerate(payload.get("attachments", []))]
    metadata = getattr(message, "metadata_", None) or {}
    payload["sender_name"] = metadata.get("sender_name")
    payload["provider_status"] = metadata.get("delivery_status")
    payload["provider_status_updated_at"] = metadata.get("delivery_status_updated_at")
    payload["provider_status_error"] = metadata.get("delivery_status_error")
    return MessageOut.model_validate(payload)
