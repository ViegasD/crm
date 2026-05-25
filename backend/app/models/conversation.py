import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, gen_uuid
from app.models.enums import (
    CannedVisibility,
    ConvEventType,
    ConvPriority,
    ConversationStatus,
    MessageOrigin,
    MessageType,
    SenderType,
    SlaStatus,
    WhatsAppProvider,
)


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conv_ws_status", "workspace_id", "status"),
        Index("ix_conv_ws_assignee", "workspace_id", "assignee_id"),
        Index("ix_conv_ws_contact", "workspace_id", "contact_id"),
        Index("ix_conv_ws_channel", "workspace_id", "channel_account_id"),
        Index("ix_conv_ws_sector", "workspace_id", "sector_id"),
        Index("ix_conv_ws_created", "workspace_id", text("created_at DESC")),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    channel_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channel_accounts.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    sector_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sectors.id", ondelete="SET NULL"), nullable=True
    )
    active_flow_execution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    status: Mapped[ConversationStatus] = mapped_column(default=ConversationStatus.open, nullable=False)
    sla_status: Mapped[SlaStatus] = mapped_column(default=SlaStatus.ok, nullable=False)
    priority: Mapped[ConvPriority] = mapped_column(default=ConvPriority.medium, nullable=False)
    channel_meta: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    unread_agent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    first_replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    service_reason_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_reasons.id", ondelete="SET NULL"), nullable=True
    )
    resolve_note: Mapped[str | None] = mapped_column(String, nullable=True)
    sla_policy_override_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sla_policies.id", ondelete="SET NULL"), nullable=True
    )

    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
    events: Mapped[list["ConversationEvent"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    participants: Mapped[list["ConversationParticipant"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    labels: Mapped[list["ConversationLabel"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base, TimestampMixin):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_msg_conv_created", "conversation_id", text("created_at DESC")),
        Index("ix_msg_ws_created", "workspace_id", text("created_at DESC")),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    sender_type: Mapped[SenderType] = mapped_column(nullable=False)
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    origin: Mapped[MessageOrigin] = mapped_column(default=MessageOrigin.customer, nullable=False)
    content: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[MessageType] = mapped_column(default=MessageType.text, nullable=False)
    attachments: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    identities: Mapped[list["MessageIdentity"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )


class MessageIdentity(Base, TimestampMixin):
    __tablename__ = "message_identities"
    __table_args__ = (
        Index("ix_msgid_channel_ext", "channel_account_id", "external_message_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=True
    )
    channel_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channel_accounts.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[WhatsAppProvider | None] = mapped_column(nullable=True)
    external_message_id: Mapped[str] = mapped_column(String(255), nullable=False)
    wamid: Mapped[str | None] = mapped_column(String(255), nullable=True)
    echo_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)

    message: Mapped["Message | None"] = relationship(back_populates="identities")


class ConversationEvent(Base, TimestampMixin):
    __tablename__ = "conversation_events"
    __table_args__ = (
        Index("ix_conv_event_conv_created", "conversation_id", text("created_at")),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[ConvEventType] = mapped_column(nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actor_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    conversation: Mapped["Conversation"] = relationship(back_populates="events")


class Label(Base, TimestampMixin):
    __tablename__ = "labels"
    __table_args__ = (UniqueConstraint("workspace_id", "name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("label_categories.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)


class ConversationLabel(Base, TimestampMixin):
    __tablename__ = "conversation_labels"
    __table_args__ = (UniqueConstraint("conversation_id", "label_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    label_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("labels.id", ondelete="CASCADE"), nullable=False
    )
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    conversation: Mapped["Conversation"] = relationship(back_populates="labels")


class ConversationParticipant(Base, TimestampMixin):
    __tablename__ = "conversation_participants"
    __table_args__ = (UniqueConstraint("conversation_id", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="participants")


class CannedResponse(Base, TimestampMixin):
    __tablename__ = "canned_responses"
    __table_args__ = (
        Index("ix_canned_ws_active", "workspace_id", "active"),
        Index("ix_canned_shortcut_lookup", "workspace_id", "shortcut"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sector_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sectors.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canned_response_categories.id", ondelete="SET NULL"), nullable=True
    )
    visibility: Mapped[CannedVisibility] = mapped_column(
        default=CannedVisibility.workspace, nullable=False
    )
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    shortcut: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    attachments: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
