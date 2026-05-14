import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import (
    ChannelAccountStatus,
    ChannelType,
    WhatsAppOpMode,
    WhatsAppProvider,
)


class ChannelAccountCreate(BaseModel):
    channel_type: ChannelType
    provider: WhatsAppProvider | None = None
    operation_mode: WhatsAppOpMode | None = None
    display_name: str
    phone_number: str | None = None
    phone_number_id: str | None = None
    waba_id: str | None = None
    external_account_id: str | None = None
    sector_id: uuid.UUID | None = None


class ChannelAccountUpdate(BaseModel):
    display_name: str | None = None
    sector_id: uuid.UUID | None = None
    welcome_message: str | None = None
    offline_message: str | None = None
    auto_assignment: bool | None = None
    enabled: bool | None = None


class ChannelAccountOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    channel_type: ChannelType
    provider: WhatsAppProvider | None
    operation_mode: WhatsAppOpMode | None
    display_name: str
    phone_number: str | None
    phone_number_id: str | None
    waba_id: str | None
    external_account_id: str | None
    is_official: bool
    supports_templates: bool
    supports_campaigns: bool
    supports_coexistence: bool
    auto_assignment: bool
    status: ChannelAccountStatus
    enabled: bool
    sector_id: uuid.UUID | None
    created_at: datetime


# Credentials — only credential_type and raw payload (encrypted on write)
class CredentialUpsert(BaseModel):
    credential_type: str
    payload: dict  # raw — will be encrypted server-side
