"""Stage 4 Tier 2: webhook operational tables.

- WebhookIpAllowlist: per workspace + provider, optional CIDRs allowed
- ChannelCircuitState: per channel circuit breaker state
- WebhookEventAttempt: per-attempt history with payload hash for diff
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, gen_uuid
from app.models.enums import CircuitState


class WebhookIpAllowlist(Base, TimestampMixin):
    """Optional inbound IP allowlist per (workspace, provider).

    If at least one row exists for (workspace, provider), inbound webhook IPs
    must match one CIDR — otherwise the request is rejected with 403.
    When zero rows exist, anything is allowed (default).
    """

    __tablename__ = "webhook_ip_allowlist"
    __table_args__ = (
        UniqueConstraint("workspace_id", "provider", "cidr"),
        Index("ix_webhook_allow_lookup", "workspace_id", "provider"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    cidr: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)


class ChannelCircuitState(Base, TimestampMixin):
    __tablename__ = "channel_circuit_state"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    channel_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channel_accounts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    state: Mapped[CircuitState] = mapped_column(default=CircuitState.closed, nullable=False)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_probe_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class WebhookEventAttempt(Base):
    """Per-attempt audit row attached to a WebhookEvent.

    Lets the UI diff payload between retries (provider sometimes mutates the
    same logical event between sends — e.g. Meta correcting a typo).
    """

    __tablename__ = "webhook_event_attempts"
    __table_args__ = (Index("ix_webhook_attempt_event", "webhook_event_id", "attempt"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    webhook_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("webhook_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # success | failed | skipped
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
