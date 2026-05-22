import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import CircuitState


# ── IP allowlist ────────────────────────────────────────────────────────────

class WebhookIpAllowlistCreate(BaseModel):
    provider: str
    cidr: str
    description: str | None = None


class WebhookIpAllowlistOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    provider: str
    cidr: str
    description: str | None
    created_at: datetime


# ── Circuit ────────────────────────────────────────────────────────────────

class ChannelCircuitOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    channel_account_id: uuid.UUID
    workspace_id: uuid.UUID
    state: CircuitState
    failure_count: int
    last_failure_at: datetime | None
    opened_at: datetime | None
    next_probe_at: datetime | None
    last_error_message: str | None


# ── Secret rotation ────────────────────────────────────────────────────────

class CredentialRotateRequest(BaseModel):
    credential_type: str
    payload: dict
    grace_hours: int = 24


class CredentialRotationOut(BaseModel):
    rotated: bool
    grace_until: datetime | None


# ── Latency / attempts ─────────────────────────────────────────────────────

class WebhookAttemptOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    webhook_event_id: uuid.UUID
    attempt: int
    payload_hash: str
    status: str
    error_message: str | None
    latency_ms: int | None
    created_at: datetime


class LatencyStats(BaseModel):
    window_minutes: int
    sample_size: int
    p50_ms: float | None
    p95_ms: float | None
    p99_ms: float | None
    avg_ms: float | None
    max_ms: int | None
