import uuid
from datetime import datetime

from pydantic import BaseModel


class WorkspaceCreate(BaseModel):
    name: str
    slug: str


class WorkspaceOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: str
    plan: str
    created_at: datetime


class SectorCreate(BaseModel):
    name: str
    description: str | None = None


class SectorOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime


class SectorMemberAdd(BaseModel):
    user_id: uuid.UUID


class MembershipUserInline(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    email: str
    avatar_url: str | None = None


class MembershipOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    role: str
    created_at: datetime
    user: MembershipUserInline | None = None
