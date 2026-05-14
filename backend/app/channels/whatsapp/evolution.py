import hashlib
import hmac
from datetime import datetime, timezone

import httpx

from app.channels.base import (
    NormalizedEvent,
    ProviderCapabilities,
    SentMessage,
    WhatsAppProviderAdapter,
)
from app.core.config import settings


class EvolutionAdapter(WhatsAppProviderAdapter):
    """
    Shared adapter for Evolution API — covers both Baileys (WhatsApp Web)
    and Cloud API modes. The `mode` controls capabilities only.
    """

    def __init__(
        self,
        instance_name: str,
        api_key: str | None = None,
        base_url: str | None = None,
        webhook_secret: str | None = None,
        mode: str = "baileys",  # "baileys" | "cloud"
    ):
        self.instance_name = instance_name
        self.api_key = api_key or settings.evolution_api_key
        self.base_url = (base_url or settings.evolution_api_url).rstrip("/")
        self.webhook_secret = webhook_secret
        self.mode = mode

    @property
    def _headers(self) -> dict:
        return {"apikey": self.api_key, "Content-Type": "application/json"}

    def get_capabilities(self) -> ProviderCapabilities:
        if self.mode == "cloud":
            return ProviderCapabilities(
                supports_templates=True,
                supports_campaigns=True,
                supports_interactive_messages=True,
                supports_media=True,
                supports_read_receipts=True,
                supports_coexistence=False,
                supports_echo_webhooks=False,
                window_24h_enforced=True,
            )
        # Baileys
        return ProviderCapabilities(
            supports_templates=False,
            supports_campaigns=False,
            supports_interactive_messages=True,
            supports_media=True,
            supports_read_receipts=True,
            supports_coexistence=False,
            supports_echo_webhooks=False,
            window_24h_enforced=False,
        )

    async def send_text(self, to: str, text: str, **kwargs) -> SentMessage:
        payload = {
            "number": to,
            "text": text,
        }
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/message/sendText/{self.instance_name}",
                json=payload,
                headers=self._headers,
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
        key_id = data.get("key", {}).get("id", "")
        return SentMessage(external_message_id=key_id)

    async def send_media(self, to: str, media_url: str, media_type: str, caption: str | None = None) -> SentMessage:
        type_map = {"image": "image", "audio": "audio", "video": "video", "file": "document"}
        ev_type = type_map.get(media_type, "document")
        payload: dict = {
            "number": to,
            "mediatype": ev_type,
            "media": media_url,
        }
        if caption:
            payload["caption"] = caption

        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/message/sendMedia/{self.instance_name}",
                json=payload,
                headers=self._headers,
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
        key_id = data.get("key", {}).get("id", "")
        return SentMessage(external_message_id=key_id)

    async def mark_as_read(self, message_id: str) -> None:
        payload = {
            "readMessages": [{"id": message_id, "fromMe": False, "remote": ""}]
        }
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.base_url}/chat/markMessageAsRead/{self.instance_name}",
                json=payload,
                headers=self._headers,
                timeout=10,
            )

    def verify_webhook_signature(self, headers: dict, raw_body: bytes) -> bool:
        if not self.webhook_secret:
            return True  # no secret configured — allow (dev mode)
        sig = headers.get("x-evolution-signature", "") or headers.get("authorization", "")
        expected = "sha256=" + hmac.new(
            self.webhook_secret.encode(), raw_body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, sig)

    def parse_webhook(self, headers: dict, body: dict) -> list[NormalizedEvent]:
        """
        Evolution v2 webhook — event field identifies the type.
        e.g. MESSAGES_UPSERT, MESSAGES_UPDATE, CONNECTION_UPDATE
        """
        events: list[NormalizedEvent] = []
        event_type = body.get("event", "")

        if event_type not in ("MESSAGES_UPSERT", "messages.upsert"):
            return events  # ignore status/connection events for now

        data = body.get("data", {})
        messages = data if isinstance(data, list) else [data]

        provider_name = "evolution_cloud" if self.mode == "cloud" else "evolution_baileys"

        for msg in messages:
            key = msg.get("key", {})
            from_me = key.get("fromMe", False)
            remote_jid = key.get("remoteJid", "")
            msg_id = key.get("id", "")

            # Strip @s.whatsapp.net suffix
            contact_phone = remote_jid.split("@")[0]

            message_content = msg.get("message", {})
            text: str | None = None
            msg_type = "text"
            attachments: list[dict] = []

            if "conversation" in message_content:
                text = message_content["conversation"]
            elif "extendedTextMessage" in message_content:
                text = message_content["extendedTextMessage"].get("text")
            elif "imageMessage" in message_content:
                msg_type = "image"
                attachments = [{"provider_payload": message_content["imageMessage"]}]
            elif "audioMessage" in message_content:
                msg_type = "audio"
                attachments = [{"provider_payload": message_content["audioMessage"]}]
            elif "videoMessage" in message_content:
                msg_type = "video"
                attachments = [{"provider_payload": message_content["videoMessage"]}]
            elif "documentMessage" in message_content:
                msg_type = "file"
                attachments = [{"provider_payload": message_content["documentMessage"]}]

            ts_raw = msg.get("messageTimestamp", 0)
            ts = datetime.fromtimestamp(int(ts_raw), tz=timezone.utc).isoformat()

            origin = "crm_agent" if from_me else "customer"

            events.append(NormalizedEvent(
                event_type="message.received",
                channel="whatsapp",
                provider=provider_name,
                workspace_id="",
                channel_account_id="",
                direction="outbound" if from_me else "inbound",
                message_type=msg_type,
                external_message_id=msg_id,
                contact_phone=contact_phone,
                text=text,
                timestamp=ts,
                origin=origin,
                attachments=attachments,
                raw=msg,
            ))

        return events
