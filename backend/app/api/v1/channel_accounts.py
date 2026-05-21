from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_workspace_member
from app.core.encryption import encrypt_payload
from app.models.channel import ChannelAccount, ChannelCredential
from app.models.enums import WhatsAppProvider
from app.models.workspace import User
from app.schemas.channel import ChannelAccountCreate, ChannelAccountOut, ChannelAccountUpdate, CredentialUpsert

router = APIRouter(prefix="/workspaces/{workspace_id}/channels", tags=["channels"])


def _apply_capabilities(account: ChannelAccount) -> None:
    """Set capability flags based on provider."""
    p = account.provider
    if p == WhatsAppProvider.meta_cloud:
        account.is_official = True
        account.supports_templates = True
        account.supports_campaigns = True
        account.supports_coexistence = True
        account.supports_echo_webhooks = True
    elif p == WhatsAppProvider.evolution_cloud:
        account.is_official = True
        account.supports_templates = True
        account.supports_campaigns = True
    elif p == WhatsAppProvider.evolution_baileys:
        account.is_official = False
    elif p == WhatsAppProvider.gupshup:
        account.is_official = True
        account.supports_templates = True
        account.supports_campaigns = True


@router.post("", response_model=ChannelAccountOut, status_code=201)
async def create_channel(
    workspace_id: UUID,
    body: ChannelAccountCreate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    account = ChannelAccount(
        workspace_id=workspace_id,
        channel_type=body.channel_type,
        provider=body.provider,
        operation_mode=body.operation_mode,
        display_name=body.display_name,
        phone_number=body.phone_number,
        phone_number_id=body.phone_number_id,
        waba_id=body.waba_id,
        external_account_id=body.external_account_id,
        sector_id=body.sector_id,
    )
    _apply_capabilities(account)
    db.add(account)
    await db.flush()
    return account


@router.get("", response_model=list[ChannelAccountOut])
async def list_channels(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(ChannelAccount).where(ChannelAccount.workspace_id == workspace_id)
    )
    return result.scalars().all()


@router.get("/{channel_id}", response_model=ChannelAccountOut)
async def get_channel(
    workspace_id: UUID,
    channel_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    account = await db.get(ChannelAccount, channel_id)
    if not account or account.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Channel not found")
    return account


@router.patch("/{channel_id}", response_model=ChannelAccountOut)
async def update_channel(
    workspace_id: UUID,
    channel_id: UUID,
    body: ChannelAccountUpdate,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    account = await db.get(ChannelAccount, channel_id)
    if not account or account.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Channel not found")
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(account, field, val)
    return account


@router.delete("/{channel_id}", status_code=204)
async def delete_channel(
    workspace_id: UUID,
    channel_id: UUID,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    account = await db.get(ChannelAccount, channel_id)
    if not account or account.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Channel not found")
    await db.delete(account)


@router.put("/{channel_id}/credentials", status_code=204)
async def upsert_credential(
    workspace_id: UUID,
    channel_id: UUID,
    body: CredentialUpsert,
    current_user: Annotated[User, Depends(require_workspace_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Store (or replace) encrypted credentials for a channel account."""
    account = await db.get(ChannelAccount, channel_id)
    if not account or account.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Channel not found")

    result = await db.execute(
        select(ChannelCredential).where(
            ChannelCredential.channel_account_id == channel_id,
            ChannelCredential.credential_type == body.credential_type,
        )
    )
    cred = result.scalar_one_or_none()
    encrypted = encrypt_payload(body.payload)

    if cred:
        cred.encrypted_payload = encrypted
    else:
        db.add(ChannelCredential(
            channel_account_id=channel_id,
            workspace_id=workspace_id,
            credential_type=body.credential_type,
            encrypted_payload=encrypted,
        ))
