from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class NormalizedEvent:
    event_type: str          # "message.received" | "message.status"
    channel: str             # "whatsapp"
    provider: str            # "meta_cloud" | "evolution_baileys" | "evolution_cloud"
    workspace_id: str        # resolved upstream
    channel_account_id: str
    direction: str           # "inbound" | "outbound"
    message_type: str        # "text" | "image" | "audio" | "video" | "file"
    external_message_id: str
    contact_phone: str
    text: str | None
    timestamp: str
    origin: str              # "customer" | "whatsapp_business_app" | ...
    wamid: str | None = None
    attachments: list[dict] = field(default_factory=list)
    raw: dict = field(default_factory=dict)


@dataclass
class SentMessage:
    external_message_id: str
    wamid: str | None = None


@dataclass
class ProviderCapabilities:
    supports_templates: bool = False
    supports_campaigns: bool = False
    supports_interactive_messages: bool = True
    supports_media: bool = True
    supports_read_receipts: bool = True
    supports_coexistence: bool = False
    supports_echo_webhooks: bool = False
    window_24h_enforced: bool = False


class WhatsAppProviderAdapter(ABC):

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        ...

    @abstractmethod
    async def send_text(self, to: str, text: str, **kwargs) -> SentMessage:
        ...

    @abstractmethod
    async def send_media(self, to: str, media_url: str, media_type: str, caption: str | None = None) -> SentMessage:
        ...

    @abstractmethod
    async def mark_as_read(self, message_id: str) -> None:
        ...

    @abstractmethod
    def parse_webhook(self, headers: dict, body: dict) -> list[NormalizedEvent]:
        """Parse raw provider webhook payload into normalized events."""
        ...

    @abstractmethod
    def verify_webhook_signature(self, headers: dict, raw_body: bytes) -> bool:
        """Return True if the webhook signature is valid."""
        ...
