import uuid
from datetime import datetime

from pydantic import BaseModel


class LabelCreate(BaseModel):
    name: str
    color: str
    category_id: uuid.UUID | None = None
    description: str | None = None


class LabelUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    category_id: uuid.UUID | None = None
    description: str | None = None


class LabelOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    color: str
    category_id: uuid.UUID | None = None
    description: str | None = None
    created_at: datetime


class LabelAssign(BaseModel):
    conversation_id: uuid.UUID


class LabelBulkAssign(BaseModel):
    conversation_ids: list[uuid.UUID]
    label_id: uuid.UUID


class LabelCategoryCreate(BaseModel):
    name: str
    color: str | None = None
    position: int = 0


class LabelCategoryUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    position: int | None = None


class LabelCategoryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    color: str | None
    position: int
    created_at: datetime
