import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_serializer
from app.services.media_access import safe_attachment_metadata

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

    @field_serializer("params")
    def safe_params(self, params):
        result = dict(params)
        if "attachments" in result:
            result["attachments"] = [safe_attachment_metadata(a) for a in result["attachments"]]
        return result


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
