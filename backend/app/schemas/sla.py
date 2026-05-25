import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


AgentPresence = Literal["online", "away", "busy", "in_call", "on_break", "offline", "invisible"]
RoutingStrategy = Literal["round_robin", "least_busy", "sticky_agent", "manual"]
EscalationAction = Literal["notify", "reassign", "webhook"]


class SlaPolicyCreate(BaseModel):
    name: str
    sector_id: uuid.UUID | None = None
    channel_account_id: uuid.UUID | None = None
    priority: str | None = None
    first_response_minutes: int
    next_response_minutes: int | None = None
    resolution_minutes: int
    reopen_response_minutes: int | None = None
    business_hours_only: bool = True
    pause_when_waiting_customer: bool = True
    at_risk_threshold_pct: int = 80
    steps: dict = {}
    active: bool = True


class SlaPolicyUpdate(BaseModel):
    name: str | None = None
    sector_id: uuid.UUID | None = None
    channel_account_id: uuid.UUID | None = None
    priority: str | None = None
    first_response_minutes: int | None = None
    next_response_minutes: int | None = None
    resolution_minutes: int | None = None
    reopen_response_minutes: int | None = None
    business_hours_only: bool | None = None
    pause_when_waiting_customer: bool | None = None
    at_risk_threshold_pct: int | None = None
    steps: dict | None = None
    active: bool | None = None


class SlaPolicyOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    sector_id: uuid.UUID | None
    channel_account_id: uuid.UUID | None
    priority: str | None
    name: str
    first_response_minutes: int
    next_response_minutes: int | None
    resolution_minutes: int
    reopen_response_minutes: int | None
    business_hours_only: bool
    pause_when_waiting_customer: bool
    at_risk_threshold_pct: int
    steps: dict
    active: bool
    created_at: datetime


class AgentCapacitySet(BaseModel):
    user_id: uuid.UUID
    max_conversations: int
    sector_id: uuid.UUID | None = None
    max_weight: float | None = None
    priority_weights: dict | None = None


class AgentCapacityOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    sector_id: uuid.UUID | None
    max_conversations: int
    max_weight: float
    priority_weights: dict


class AgentPauseReasonCreate(BaseModel):
    label: str
    active: bool = True
    position: int = 0


class AgentPauseReasonOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    label: str
    active: bool
    position: int


class AgentStatusSet(BaseModel):
    status: AgentPresence
    reason_id: uuid.UUID | None = None
    note: str | None = None


class AgentStatusOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    status: str
    reason_id: uuid.UUID | None
    note: str | None
    since_at: datetime
    updated_at: datetime
    user_name: str | None = None
    user_email: str | None = None
    reason_label: str | None = None


class BusinessHoursIn(BaseModel):
    sector_id: uuid.UUID | None = None
    weekday: int
    start_minute: int
    end_minute: int
    timezone: str = "America/Sao_Paulo"
    active: bool = True


class BusinessHoursOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    sector_id: uuid.UUID | None
    weekday: int
    start_minute: int
    end_minute: int
    timezone: str
    active: bool


class RoutingRuleIn(BaseModel):
    sector_id: uuid.UUID | None = None
    strategy: RoutingStrategy = "least_busy"
    tiebreaker: str = "oldest_idle"
    sticky_hours: int = 24
    auto_reassign_minutes: int = 10
    reopen_window_hours: int = 24


class RoutingRuleOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    sector_id: uuid.UUID | None
    strategy: str
    tiebreaker: str
    sticky_hours: int
    auto_reassign_minutes: int
    reopen_window_hours: int


class SlaEscalationRuleIn(BaseModel):
    threshold_pct: int
    action: EscalationAction
    target_role: str | None = None
    target_user_id: uuid.UUID | None = None
    webhook_url: str | None = None
    position: int = 0
    active: bool = True


class SlaEscalationRuleOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    policy_id: uuid.UUID
    threshold_pct: int
    action: str
    target_role: str | None
    target_user_id: uuid.UUID | None
    webhook_url: str | None
    position: int
    active: bool


class AssignmentRequest(BaseModel):
    conversation_id: uuid.UUID
    sector_id: uuid.UUID | None = None


class AssignmentResult(BaseModel):
    conversation_id: uuid.UUID
    assignee_id: uuid.UUID | None
    assigned: bool
    reason: str | None = None


class SlaEventOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    conversation_id: uuid.UUID
    policy_id: uuid.UUID
    type: str
    status: str
    deadline_at: datetime
    achieved_at: datetime | None
    violated_at: datetime | None
    escalated_to: uuid.UUID | None
    metadata_: dict


class SupervisorSectorMetric(BaseModel):
    sector_id: uuid.UUID | None
    sector_name: str
    queued: int
    active: int
    at_risk: int
    violated: int


class SupervisorAgentMetric(BaseModel):
    user_id: uuid.UUID
    name: str
    email: str
    role: str
    sector_id: uuid.UUID | None = None
    status: str
    reason: str | None = None
    since_at: datetime | None = None
    max_conversations: int
    max_weight: float
    assigned_open: int
    weighted_load: float
    available_slots: float
    at_risk: int
    violated: int


class SupervisorAlert(BaseModel):
    conversation_id: uuid.UUID
    contact_name: str | None
    assignee_id: uuid.UUID | None
    sector_id: uuid.UUID | None
    sla_status: str
    priority: str
    last_message_at: datetime | None


class SupervisorOverview(BaseModel):
    totals: dict
    sectors: list[SupervisorSectorMetric]
    agents: list[SupervisorAgentMetric]
    alerts: list[SupervisorAlert]
