import hashlib
import hmac
import logging
from datetime import datetime, timezone

import httpx

from app.channels.base import (
    NormalizedEvent,
    ProviderCapabilities,
    SentMessage,
    WhatsAppProviderAdapter,
)
from app.core.config import settings


logger = logging.getLogger(__name__)


def _format_group_name(remote_jid: str) -> str:
    return f"Group {remote_jid.split('@')[0]}"


def _extract_group_name(msg: dict, remote_jid: str) -> str:
    group_name = (
        msg.get("groupName")
        or msg.get("groupSubject")
        or msg.get("subject")
        or msg.get("chatName")
        or (msg.get("message") or {}).get("groupInviteMessage", {}).get("groupName")
    )
    return group_name or _format_group_name(remote_jid)


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

    async def fetch_group_names(self, group_jids: list[str]) -> dict[str, str]:
        wanted = {group_jid for group_jid in group_jids if group_jid.endswith("@g.us")}
        if not wanted:
            return {}

        resolved: dict[str, str] = {}
        async with httpx.AsyncClient(timeout=10) as client:
            for jid in wanted:
                try:
                    r = await client.get(
                        f"{self.base_url}/group/findGroupInfos/{self.instance_name}",
                        params={"groupJid": jid},
                        headers=self._headers,
                    )
                    r.raise_for_status()
                    data = r.json()
                    subject = (data.get("subject") or "").strip()
                    if subject:
                        resolved[jid] = subject
                except Exception:  # noqa: BLE001
                    logger.debug("Could not fetch group info for %s", jid)
        return resolved

    def verify_webhook_signature(self, headers: dict, raw_body: bytes) -> bool:
        if not self.webhook_secret:
            return False
        sig = headers.get("x-evolution-signature", "")
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
            is_group = remote_jid.endswith("@g.us")
            sender_name = msg.get("pushName") or msg.get("senderName")

            # Groups should be keyed by the group JID, not by the participant.
            contact_phone = remote_jid if is_group else remote_jid.split("@")[0]
            contact_name = _extract_group_name(msg, remote_jid) if is_group else sender_name

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
            elif "stickerMessage" in message_content:
                msg_type = "sticker"
                attachments = [{"provider_payload": message_content["stickerMessage"]}]
            elif "audioMessage" in message_content:
                msg_type = "audio"
                attachments = [{"provider_payload": message_content["audioMessage"]}]
            elif "videoMessage" in message_content:
                msg_type = "video"
                attachments = [{"provider_payload": message_content["videoMessage"]}]
            elif "documentMessage" in message_content:
                msg_type = "file"
                attachments = [{"provider_payload": message_content["documentMessage"]}]

            if msg_type != "text":
                payload = attachments[0].get("provider_payload", {}) if attachments else {}
                logger.info(
                    "Evolution media webhook parsed instance=%s message_id=%s type=%s from_me=%s has_url=%s mimetype=%s",
                    self.instance_name,
                    msg_id,
                    msg_type,
                    from_me,
                    bool(payload.get("url")),
                    payload.get("mimetype") or payload.get("mimeType"),
                )

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
                contact_name=contact_name,
                sender_name=sender_name,
                is_group=is_group,
                attachments=attachments,
                raw=msg,
            ))

        return events
