"""Schemas for the reopen / new-protocol policy (Stage 3)."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import ReopenMode


class ConversationPolicyIn(BaseModel):
    sector_id: UUID | None = None
    reopen_mode: ReopenMode = ReopenMode.window
    reopen_window_hours: int = Field(default=24, ge=0, le=24 * 30)
    inherit_assignee_on_new: bool = False


class ConversationPolicyOut(BaseModel):
    id: UUID
    workspace_id: UUID
    sector_id: UUID | None
    reopen_mode: ReopenMode
    reopen_window_hours: int
    inherit_assignee_on_new: bool

    model_config = {"from_attributes": True}


class ResolvedPolicyOut(BaseModel):
    reopen_mode: ReopenMode
    reopen_window_hours: int
    inherit_assignee_on_new: bool
    source: str  # "sector" | "workspace" | "default"
