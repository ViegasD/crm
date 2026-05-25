import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── Pause reasons ───────────────────────────────────────────────────────────

class PauseReasonUpdate(BaseModel):
    label: str | None = None
    active: bool | None = None
    position: int | None = None


# ── Auto-resolve rules ──────────────────────────────────────────────────────

class AutoResolveRuleCreate(BaseModel):
    sector_id: uuid.UUID | None = None
    inactivity_hours: int = 72
    status_from: list[str] = Field(default_factory=lambda: ["pending", "open"])
    status_to: str = "resolved"
    active: bool = False


class AutoResolveRuleUpdate(BaseModel):
    sector_id: uuid.UUID | None = None
    inactivity_hours: int | None = None
    status_from: list[str] | None = None
    status_to: str | None = None
    active: bool | None = None


class AutoResolveRuleOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    sector_id: uuid.UUID | None
    inactivity_hours: int
    status_from: list
    status_to: str
    active: bool


# ── Business holidays ───────────────────────────────────────────────────────

class BusinessHolidayCreate(BaseModel):
    sector_id: uuid.UUID | None = None
    holiday_date: date
    label: str
    treat_as: Literal["closed", "half_day", "custom"] = "closed"
    custom_start_minute: int | None = None
    custom_end_minute: int | None = None


class BusinessHolidayOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    sector_id: uuid.UUID | None
    holiday_date: date
    label: str
    treat_as: str
    custom_start_minute: int | None
    custom_end_minute: int | None


# ── Conversation lock ───────────────────────────────────────────────────────

class ConversationLockOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    conversation_id: uuid.UUID
    holder_user_id: uuid.UUID
    acquired_at: datetime
    expires_at: datetime
    holder_name: str | None = None


class ConversationLockRequest(BaseModel):
    ttl_seconds: int = 90


# ── Idle rule ───────────────────────────────────────────────────────────────

class IdleRuleIn(BaseModel):
    idle_minutes: int = 10
    offline_minutes: int = 30
    active: bool = True


class IdleRuleOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    idle_minutes: int
    offline_minutes: int
    active: bool


# ── Notifications ───────────────────────────────────────────────────────────

NotificationKind = Literal["email", "slack_webhook", "inapp", "webhook"]


class NotificationChannelIn(BaseModel):
    name: str
    kind: NotificationKind
    config: dict = Field(default_factory=dict)
    events: list[str] = Field(default_factory=list)
    active: bool = True


class NotificationChannelOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    kind: str
    config: dict
    events: list
    active: bool
    created_at: datetime


class NotificationDeliveryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    channel_id: uuid.UUID | None
    user_id: uuid.UUID | None
    event_type: str
    title: str
    body: str | None
    status: str
    read_at: datetime | None
    created_at: datetime


# ── Outbound webhooks ──────────────────────────────────────────────────────

class ExternalWebhookSubscriptionIn(BaseModel):
    name: str
    url: str
    secret: str | None = None
    events: list[str] = Field(default_factory=list)
    active: bool = True


class ExternalWebhookSubscriptionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    url: str
    events: list
    active: bool
    created_at: datetime


class ExternalWebhookDeliveryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    subscription_id: uuid.UUID
    event_type: str
    status: str
    attempts: int
    last_error: str | None
    response_status: int | None
    delivered_at: datetime | None
    created_at: datetime


# ── CSAT ───────────────────────────────────────────────────────────────────

class CsatSurveyOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    conversation_id: uuid.UUID
    contact_id: uuid.UUID | None
    assignee_id: uuid.UUID | None
    sector_id: uuid.UUID | None
    score: int | None
    feedback: str | None
    sent_at: datetime
    responded_at: datetime | None
    delivery_status: str


class CsatPublicRespond(BaseModel):
    score: int
    feedback: str | None = None


# ── SLA override ────────────────────────────────────────────────────────────

class ConversationSlaOverrideRequest(BaseModel):
    sla_policy_override_id: uuid.UUID | None  # null = clear


# ── Supervisor heatmap ─────────────────────────────────────────────────────

class HeatmapCell(BaseModel):
    user_id: uuid.UUID
    user_name: str
    hour: int
    minutes_assigned: int
    conversations: int


class HeatmapOut(BaseModel):
    days: int
    cells: list[HeatmapCell]
