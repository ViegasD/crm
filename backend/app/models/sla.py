import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, gen_uuid
from app.models.enums import SlaEventType, SlaStatus


class SlaPolicy(Base, TimestampMixin):
    __tablename__ = "sla_policies"
    __table_args__ = (
        Index("ix_sla_policy_scope", "workspace_id", "sector_id", "channel_account_id", "priority"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sector_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sectors.id", ondelete="CASCADE"), nullable=True
    )
    channel_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channel_accounts.id", ondelete="CASCADE"), nullable=True
    )
    priority: Mapped[str | None] = mapped_column(String(20), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    first_response_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    next_response_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolution_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    reopen_response_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    business_hours_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    pause_when_waiting_customer: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    at_risk_threshold_pct: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    steps: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    events: Mapped[list["SlaEvent"]] = relationship(back_populates="policy")
    escalations: Mapped[list["SlaEscalationRule"]] = relationship(
        back_populates="policy", cascade="all, delete-orphan"
    )


class SlaEvent(Base, TimestampMixin):
    __tablename__ = "sla_events"
    __table_args__ = ()

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sla_policies.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[SlaEventType] = mapped_column(nullable=False)
    status: Mapped[SlaStatus] = mapped_column(default=SlaStatus.ok, nullable=False)
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    achieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    violated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    escalated_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    policy: Mapped["SlaPolicy"] = relationship(back_populates="events")


class AgentCapacity(Base, TimestampMixin):
    __tablename__ = "agent_capacity"
    __table_args__ = (UniqueConstraint("user_id", "workspace_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    sector_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sectors.id", ondelete="SET NULL"), nullable=True
    )
    max_conversations: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    max_weight: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    priority_weights: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class AgentPauseReason(Base, TimestampMixin):
    __tablename__ = "agent_pause_reasons"
    __table_args__ = (UniqueConstraint("workspace_id", "label"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class AgentStatus(Base, TimestampMixin):
    __tablename__ = "agent_status"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id"),
        Index("ix_agent_status_ws_status", "workspace_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), default="offline", nullable=False)
    reason_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_pause_reasons.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    since_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class AgentStatusLog(Base):
    __tablename__ = "agent_status_log"
    __table_args__ = (Index("ix_agent_status_log_user_created", "workspace_id", "user_id", "changed_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_pause_reasons.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BusinessHours(Base, TimestampMixin):
    __tablename__ = "business_hours"
    __table_args__ = (
        Index("ix_business_hours_scope", "workspace_id", "sector_id", "weekday"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sector_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sectors.id", ondelete="CASCADE"), nullable=True
    )
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    end_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="America/Sao_Paulo", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class RoutingRule(Base, TimestampMixin):
    __tablename__ = "routing_rules"
    __table_args__ = (UniqueConstraint("workspace_id", "sector_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sector_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sectors.id", ondelete="CASCADE"), nullable=True
    )
    strategy: Mapped[str] = mapped_column(String(32), default="least_busy", nullable=False)
    tiebreaker: Mapped[str] = mapped_column(String(32), default="oldest_idle", nullable=False)
    sticky_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    auto_reassign_minutes: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    reopen_window_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)


class ConversationAssignment(Base):
    __tablename__ = "conversation_assignments"
    __table_args__ = (
        Index("ix_assignment_conv_assigned", "conversation_id", "assigned_at"),
        Index("ix_assignment_user_active", "workspace_id", "user_id", "unassigned_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    sector_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sectors.id", ondelete="SET NULL"), nullable=True
    )
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    unassigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    method: Mapped[str] = mapped_column(String(32), default="manual", nullable=False)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)


class SlaEscalationRule(Base, TimestampMixin):
    __tablename__ = "sla_escalation_chain"
    __table_args__ = (
        Index("ix_sla_escalation_policy", "policy_id", "threshold_pct"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sla_policies.id", ondelete="CASCADE"), nullable=False
    )
    threshold_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    target_role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    webhook_url: Mapped[str | None] = mapped_column(String, nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    policy: Mapped["SlaPolicy"] = relationship(back_populates="escalations")


class AutoResolveRule(Base, TimestampMixin):
    __tablename__ = "auto_resolve_rules"
    __table_args__ = (UniqueConstraint("workspace_id", "sector_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sector_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sectors.id", ondelete="CASCADE"), nullable=True
    )
    inactivity_hours: Mapped[int] = mapped_column(Integer, default=72, nullable=False)
    status_from: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    status_to: Mapped[str] = mapped_column(String(32), default="resolved", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
