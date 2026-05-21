import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, gen_uuid
from app.models.enums import WebhookEventStatus


class WebhookEvent(Base):
    """Durable record of every webhook payload received.

    Stored *after* signature/replay validation and *before* the 200 is returned,
    so reprocessing is possible even if the in-process pipeline crashes.
    """

    __tablename__ = "webhook_events"
    __table_args__ = (
        Index("ix_webhook_status_created", "status", "created_at"),
        Index("ix_webhook_provider_signature", "provider", "signature_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True
    )
    channel_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channel_accounts.id", ondelete="SET NULL"), nullable=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    signature_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[WebhookEventStatus] = mapped_column(default=WebhookEventStatus.received, nullable=False)
    headers: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
