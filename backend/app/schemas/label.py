import uuid
from datetime import datetime

from pydantic import BaseModel


class LabelCreate(BaseModel):
    name: str
    color: str  # Hex e.g. "#3B82F6"


class LabelUpdate(BaseModel):
    name: str | None = None
    color: str | None = None


class LabelOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    color: str
    created_at: datetime


class LabelAssign(BaseModel):
    conversation_id: uuid.UUID


class LabelBulkAssign(BaseModel):
    conversation_ids: list[uuid.UUID]
    label_id: uuid.UUID
