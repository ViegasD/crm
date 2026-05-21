import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ConvPriority, ConversationStatus, SlaStatus


class LabelInline(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    color: str


class UserInline(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    email: str
    avatar_url: str | None = None


class ConversationOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    channel_account_id: uuid.UUID
    contact_id: uuid.UUID
    assignee_id: uuid.UUID | None
    sector_id: uuid.UUID | None
    status: ConversationStatus
    sla_status: SlaStatus
    priority: ConvPriority
    unread_agent_count: int
    first_replied_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime
    contact_name: str | None = None
    contact_phone: str | None = None
    last_message: str | None = None
    last_message_at: datetime | None = None
    assignee_name: str | None = None
    labels: list[LabelInline] = []


class ConversationUpdate(BaseModel):
    assignee_id: uuid.UUID | None = None
    sector_id: uuid.UUID | None = None
    status: ConversationStatus | None = None
    priority: ConvPriority | None = None


class ConversationTransfer(BaseModel):
    assignee_id: uuid.UUID | None = None
    sector_id: uuid.UUID | None = None
    note: str | None = None


class ConversationEventOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    conversation_id: uuid.UUID
    type: str
    actor_id: uuid.UUID | None
    actor_type: str | None
    payload: dict
    created_at: datetime
    actor_name: str | None = None


class ConversationParticipantAdd(BaseModel):
    user_id: uuid.UUID


class ConversationParticipantOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    conversation_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    user: UserInline | None = None


class ConversationListFilters(BaseModel):
    status: ConversationStatus | None = None
    assignee_id: uuid.UUID | None = None
    sector_id: uuid.UUID | None = None
    channel_account_id: uuid.UUID | None = None
    label_id: uuid.UUID | None = None
    page: int = 1
    page_size: int = 30


class ConversationBulkLabel(BaseModel):
    conversation_ids: list[uuid.UUID]
    label_id: uuid.UUID


class ConversationBulkTransfer(BaseModel):
    conversation_ids: list[uuid.UUID]
    assignee_id: uuid.UUID | None = None
    sector_id: uuid.UUID | None = None
    note: str | None = None


class ConversationBulkStatus(BaseModel):
    conversation_ids: list[uuid.UUID]
    status: ConversationStatus
