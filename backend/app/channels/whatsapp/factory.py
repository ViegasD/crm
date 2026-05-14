from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.channels.base import WhatsAppProviderAdapter
from app.channels.whatsapp.evolution import EvolutionAdapter
from app.channels.whatsapp.meta_cloud import MetaCloudAdapter
from app.core.encryption import decrypt_payload
from app.models.channel import ChannelAccount, ChannelCredential
from app.models.enums import WhatsAppProvider


async def get_whatsapp_adapter(
    db: AsyncSession, channel_account: ChannelAccount
) -> WhatsAppProviderAdapter:
    """Load encrypted credentials and return the correct provider adapter."""

    result = await db.execute(
        select(ChannelCredential).where(
            ChannelCredential.channel_account_id == channel_account.id
        )
    )
    creds: list[ChannelCredential] = result.scalars().all()
    cred_map = {c.credential_type: decrypt_payload(c.encrypted_payload) for c in creds}

    provider = channel_account.provider

    if provider == WhatsAppProvider.meta_cloud:
        main = cred_map.get("meta_cloud", {})
        return MetaCloudAdapter(
            access_token=main.get("access_token", ""),
            phone_number_id=channel_account.phone_number_id or "",
            app_secret=main.get("app_secret", ""),
        )

    if provider in (WhatsAppProvider.evolution_baileys, WhatsAppProvider.evolution_cloud):
        ev = cred_map.get("evolution", {})
        mode = "cloud" if provider == WhatsAppProvider.evolution_cloud else "baileys"
        return EvolutionAdapter(
            instance_name=ev.get("evolution_instance_id", channel_account.external_account_id or ""),
            api_key=ev.get("evolution_api_key"),
            base_url=ev.get("evolution_base_url"),
            webhook_secret=ev.get("webhook_secret"),
            mode=mode,
        )

    raise ValueError(f"Unsupported WhatsApp provider: {provider}")
