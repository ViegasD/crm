import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.enums import ContactStatus, ContactType


class ContactPhoneIn(BaseModel):
    phone: str
    label: str | None = None
    is_primary: bool = False


class ContactEmailIn(BaseModel):
    email: EmailStr
    label: str | None = None
    is_primary: bool = False


class ContactCreate(BaseModel):
    name: str
    type: ContactType = ContactType.person
    document: str | None = None
    company: str | None = None
    integration_id: str | None = None
    phones: list[ContactPhoneIn] = []
    emails: list[ContactEmailIn] = []


class ContactUpdate(BaseModel):
    name: str | None = None
    status: ContactStatus | None = None
    is_priority: bool | None = None
    company: str | None = None
    document: str | None = None


class ContactOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    type: ContactType
    status: ContactStatus
    is_priority: bool
    avatar_url: str | None
    company: str | None
    integration_id: str | None
    document: str | None
    created_at: datetime
