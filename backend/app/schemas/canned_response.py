import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import CannedVisibility


class CannedAttachment(BaseModel):
    key: str
    url: str | None = None
    name: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None


class CannedResponseCreate(BaseModel):
    title: str
    shortcut: str
    content: str
    sector_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    visibility: CannedVisibility = CannedVisibility.workspace
    language: str | None = None
    attachments: list[CannedAttachment] = Field(default_factory=list)
    active: bool = True


class CannedResponseUpdate(BaseModel):
    title: str | None = None
    shortcut: str | None = None
    content: str | None = None
    sector_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    visibility: CannedVisibility | None = None
    language: str | None = None
    attachments: list[CannedAttachment] | None = None
    active: bool | None = None


class CannedResponseOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    sector_id: uuid.UUID | None
    user_id: uuid.UUID | None
    category_id: uuid.UUID | None
    visibility: CannedVisibility
    language: str | None
    title: str
    shortcut: str
    content: str
    attachments: list[dict]
    active: bool
    created_at: datetime
    updated_at: datetime


class CannedCategoryCreate(BaseModel):
    name: str
    color: str | None = None
    position: int = 0


class CannedCategoryUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    position: int | None = None


class CannedCategoryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    color: str | None
    position: int
    created_at: datetime
