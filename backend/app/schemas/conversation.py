import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ConvPriority, ConversationStatus, SlaStatus


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


class ConversationUpdate(BaseModel):
    assignee_id: uuid.UUID | None = None
    sector_id: uuid.UUID | None = None
    status: ConversationStatus | None = None
    priority: ConvPriority | None = None


class ConversationTransfer(BaseModel):
    assignee_id: uuid.UUID | None = None
    sector_id: uuid.UUID | None = None
    note: str | None = None


class ConversationListFilters(BaseModel):
    status: ConversationStatus | None = None
    assignee_id: uuid.UUID | None = None
    sector_id: uuid.UUID | None = None
    channel_account_id: uuid.UUID | None = None
    page: int = 1
    page_size: int = 30
