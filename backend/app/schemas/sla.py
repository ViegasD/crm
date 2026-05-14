import uuid
from datetime import datetime

from pydantic import BaseModel


class SlaPolicyCreate(BaseModel):
    name: str
    sector_id: uuid.UUID | None = None
    first_response_minutes: int
    resolution_minutes: int


class SlaPolicyUpdate(BaseModel):
    name: str | None = None
    first_response_minutes: int | None = None
    resolution_minutes: int | None = None
    active: bool | None = None


class SlaPolicyOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    sector_id: uuid.UUID | None
    name: str
    first_response_minutes: int
    resolution_minutes: int
    active: bool
    created_at: datetime


class AgentCapacitySet(BaseModel):
    user_id: uuid.UUID
    max_conversations: int
    sector_id: uuid.UUID | None = None


class AgentCapacityOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    sector_id: uuid.UUID | None
    max_conversations: int
