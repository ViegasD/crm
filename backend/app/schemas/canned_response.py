import uuid
from datetime import datetime

from pydantic import BaseModel


class CannedResponseCreate(BaseModel):
    title: str
    shortcut: str
    content: str
    sector_id: uuid.UUID | None = None
    active: bool = True


class CannedResponseUpdate(BaseModel):
    title: str | None = None
    shortcut: str | None = None
    content: str | None = None
    sector_id: uuid.UUID | None = None
    active: bool | None = None


class CannedResponseOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    sector_id: uuid.UUID | None
    title: str
    shortcut: str
    content: str
    active: bool
    created_at: datetime
    updated_at: datetime
