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


class MetaCloudAdapter(WhatsAppProviderAdapter):
    """Adapter for Meta WhatsApp Cloud API."""

    def __init__(self, access_token: str, phone_number_id: str, app_secret: str):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.app_secret = app_secret
        self._base = f"https://graph.facebook.com/v20.0/{phone_number_id}"

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_templates=True,
            supports_campaigns=True,
            supports_interactive_messages=True,
            supports_media=True,
            supports_read_receipts=True,
            supports_coexistence=True,
            supports_echo_webhooks=True,
            window_24h_enforced=True,
        )

    async def send_text(self, to: str, text: str, **kwargs) -> SentMessage:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self._base}/messages",
                json=payload,
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
        wamid = data.get("messages", [{}])[0].get("id")
        return SentMessage(external_message_id=wamid, wamid=wamid)

    async def send_media(self, to: str, media_url: str, media_type: str, caption: str | None = None) -> SentMessage:
        type_map = {"image": "image", "audio": "audio", "video": "video", "file": "document"}
        wa_type = type_map.get(media_type, "document")
        media_obj: dict = {"link": media_url}
        if caption:
            media_obj["caption"] = caption
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": wa_type,
            wa_type: media_obj,
        }
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self._base}/messages",
                json=payload,
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
        wamid = data.get("messages", [{}])[0].get("id")
        return SentMessage(external_message_id=wamid, wamid=wamid)

    async def mark_as_read(self, message_id: str) -> None:
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self._base}/messages",
                json=payload,
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=10,
            )

    def verify_webhook_signature(self, headers: dict, raw_body: bytes) -> bool:
        sig_header = headers.get("x-hub-signature-256", "")
        expected = "sha256=" + hmac.new(
            self.app_secret.encode(), raw_body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, sig_header)

    def parse_webhook(self, headers: dict, body: dict) -> list[NormalizedEvent]:
        events: list[NormalizedEvent] = []
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                contacts = value.get("contacts", [])
                contact_map = {c["wa_id"]: c.get("profile", {}).get("name") for c in contacts}

                for msg in messages:
                    from_number = msg.get("from", "")
                    ext_id = msg.get("id", "")
                    msg_type = msg.get("type", "text")
                    ts = msg.get("timestamp", "0")

                    text = None
                    attachments: list[dict] = []

                    if msg_type == "text":
                        text = msg.get("text", {}).get("body")
                    elif msg_type in ("image", "audio", "video", "document", "sticker"):
                        media = msg.get(msg_type, {})
                        attachments = [{"provider_media_id": media.get("id"), "mime_type": media.get("mime_type"), "type": msg_type}]
                    elif msg_type == "location":
                        loc = msg.get("location", {})
                        text = f"[Location] lat={loc.get('latitude')} lng={loc.get('longitude')}"

                    normalized_type = "file" if msg_type == "document" else msg_type
                    if normalized_type not in ("text", "image", "audio", "video", "file"):
                        normalized_type = "text"

                    events.append(NormalizedEvent(
                        event_type="message.received",
                        channel="whatsapp",
                        provider="meta_cloud",
                        workspace_id="",  # filled upstream
                        channel_account_id="",  # filled upstream
                        direction="inbound",
                        message_type=normalized_type,
                        external_message_id=ext_id,
                        contact_phone=from_number,
                        text=text,
                        timestamp=datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat(),
                        origin="customer",
                        contact_name=contact_map.get(from_number),
                        wamid=ext_id,
                        attachments=attachments,
                        raw=msg,
                    ))

                # Status updates
                for status_update in value.get("statuses", []):
                    events.append(NormalizedEvent(
                        event_type="message.status",
                        channel="whatsapp",
                        provider="meta_cloud",
                        workspace_id="",
                        channel_account_id="",
                        direction="outbound",
                        message_type="text",
                        external_message_id=status_update.get("id", ""),
                        contact_phone=status_update.get("recipient_id", ""),
                        text=None,
                        timestamp=datetime.fromtimestamp(
                            int(status_update.get("timestamp", 0)), tz=timezone.utc
                        ).isoformat(),
                        origin="system",
                        wamid=status_update.get("id"),
                        raw=status_update,
                    ))
        return events
