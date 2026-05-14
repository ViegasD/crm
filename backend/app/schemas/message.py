import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

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
    origin: MessageOrigin
    content: str | None
    type: MessageType
    attachments: list[dict]
    is_read: bool
    created_at: datetime


class SendMessageRequest(BaseModel):
    content: str | None = None
    type: MessageType = MessageType.text
    attachments: list[dict] = []
    # For internal notes
    is_note: bool = False
