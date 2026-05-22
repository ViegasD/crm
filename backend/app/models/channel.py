import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, gen_uuid
from app.models.enums import (
    ChannelAccountStatus,
    ChannelType,
    WhatsAppOpMode,
    WhatsAppProvider,
)


class ChannelAccount(Base, TimestampMixin):
    __tablename__ = "channel_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sector_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sectors.id", ondelete="SET NULL"), nullable=True
    )
    channel_type: Mapped[ChannelType] = mapped_column(nullable=False, index=True)
    provider: Mapped[WhatsAppProvider | None] = mapped_column(nullable=True)
    operation_mode: Mapped[WhatsAppOpMode | None] = mapped_column(nullable=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    phone_number_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    waba_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    external_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_templates: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_campaigns: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_coexistence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_echo_webhooks: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_assignment: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    welcome_message: Mapped[str | None] = mapped_column(String, nullable=True)
    offline_message: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[ChannelAccountStatus] = mapped_column(default=ChannelAccountStatus.active, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    credentials: Mapped[list["ChannelCredential"]] = relationship(
        back_populates="channel_account", cascade="all, delete-orphan"
    )


class ChannelCredential(Base, TimestampMixin):
    __tablename__ = "channel_credentials"
    __table_args__ = (UniqueConstraint("channel_account_id", "credential_type"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    channel_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channel_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    credential_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # AES-256-GCM encrypted JSON
    encrypted_payload: Mapped[str] = mapped_column(String, nullable=False)
    # Previous credential kept during a rotation grace window so webhooks signed
    # with the old secret keep working until grace_until passes.
    previous_payload: Mapped[str | None] = mapped_column(String, nullable=True)
    grace_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    channel_account: Mapped["ChannelAccount"] = relationship(back_populates="credentials")
