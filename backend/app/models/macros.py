"""Macros: sequence of conversation actions executed in one click."""
import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, gen_uuid
from app.models.enums import CannedVisibility, MacroActionType


class Macro(Base, TimestampMixin):
    """A reusable sequence of actions executable on any conversation."""

    __tablename__ = "macros"
    __table_args__ = (Index("ix_macro_ws_visibility", "workspace_id", "visibility"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    visibility: Mapped[CannedVisibility] = mapped_column(default=CannedVisibility.workspace, nullable=False)
    sector_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sectors.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    actions: Mapped[list["MacroAction"]] = relationship(
        back_populates="macro", cascade="all, delete-orphan", order_by="MacroAction.position"
    )


class MacroAction(Base, TimestampMixin):
    __tablename__ = "macro_actions"
    __table_args__ = (Index("ix_macro_action_macro_pos", "macro_id", "position"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    macro_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("macros.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    action_type: Mapped[MacroActionType] = mapped_column(nullable=False)
    params: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    macro: Mapped["Macro"] = relationship(back_populates="actions")
