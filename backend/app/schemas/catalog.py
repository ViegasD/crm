import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ViewVisibility


# ── Reasons ──────────────────────────────────────────────────────────────────

class TransferReasonCreate(BaseModel):
    label: str
    required: bool = False
    active: bool = True


class TransferReasonUpdate(BaseModel):
    label: str | None = None
    required: bool | None = None
    active: bool | None = None


class TransferReasonOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    label: str
    required: bool
    active: bool
    created_at: datetime


class ServiceReasonCreate(BaseModel):
    label: str
    description: str | None = None
    position: int = 0
    active: bool = True


class ServiceReasonUpdate(BaseModel):
    label: str | None = None
    description: str | None = None
    position: int | None = None
    active: bool | None = None


class ServiceReasonOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    label: str
    description: str | None
    position: int
    active: bool
    created_at: datetime


# ── Snooze ───────────────────────────────────────────────────────────────────

class SnoozeRequest(BaseModel):
    until: datetime
    reason: str | None = None


class SnoozeOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    conversation_id: uuid.UUID
    until: datetime
    reason: str | None
    snoozed_by: uuid.UUID | None
    created_at: datetime


# ── Custom views ─────────────────────────────────────────────────────────────

class ConversationViewCreate(BaseModel):
    name: str
    icon: str | None = None
    visibility: ViewVisibility = ViewVisibility.personal
    sector_id: uuid.UUID | None = None
    filters: dict = Field(default_factory=dict)
    pinned: bool = False
    position: int = 0


class ConversationViewUpdate(BaseModel):
    name: str | None = None
    icon: str | None = None
    visibility: ViewVisibility | None = None
    sector_id: uuid.UUID | None = None
    filters: dict | None = None
    pinned: bool | None = None
    position: int | None = None


class ConversationViewOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID | None
    sector_id: uuid.UUID | None
    visibility: ViewVisibility
    name: str
    icon: str | None
    filters: dict
    pinned: bool
    position: int
    created_at: datetime


# ── Mention inbox ────────────────────────────────────────────────────────────

class MentionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    conversation_id: uuid.UUID
    message_id: uuid.UUID | None
    mentioned_by: uuid.UUID | None
    snippet: str | None
    read_at: datetime | None
    created_at: datetime


class MentionMarkRead(BaseModel):
    mention_ids: list[uuid.UUID] | None = None  # null = mark all
