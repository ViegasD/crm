import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import CannedVisibility, MacroActionType


class MacroActionIn(BaseModel):
    action_type: MacroActionType
    params: dict = Field(default_factory=dict)
    position: int = 0


class MacroActionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    action_type: MacroActionType
    params: dict
    position: int


class MacroCreate(BaseModel):
    name: str
    description: str | None = None
    visibility: CannedVisibility = CannedVisibility.workspace
    sector_id: uuid.UUID | None = None
    actions: list[MacroActionIn] = Field(default_factory=list)
    active: bool = True


class MacroUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    visibility: CannedVisibility | None = None
    sector_id: uuid.UUID | None = None
    actions: list[MacroActionIn] | None = None
    active: bool | None = None


class MacroOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None
    visibility: CannedVisibility
    sector_id: uuid.UUID | None
    user_id: uuid.UUID | None
    active: bool
    actions: list[MacroActionOut]
    created_at: datetime
    updated_at: datetime


class MacroRunRequest(BaseModel):
    conversation_id: uuid.UUID


class MacroRunResult(BaseModel):
    executed: list[str]
    skipped: list[str]
    errors: list[str]
