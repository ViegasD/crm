import enum


class UserStatus(str, enum.Enum):
    online = "online"
    offline = "offline"
    busy = "busy"
    invisible = "invisible"


class WorkspaceRole(str, enum.Enum):
    admin = "admin"
    supervisor = "supervisor"
    agent = "agent"


class ChannelType(str, enum.Enum):
    whatsapp = "whatsapp"
    instagram = "instagram"
    facebook = "facebook"
    telegram = "telegram"
    line = "line"
    tiktok = "tiktok"
    sms = "sms"
    email = "email"
    live_chat = "live_chat"


class WhatsAppProvider(str, enum.Enum):
    meta_cloud = "meta_cloud"
    gupshup = "gupshup"
    evolution_baileys = "evolution_baileys"
    evolution_cloud = "evolution_cloud"


class WhatsAppOpMode(str, enum.Enum):
    official_api_only = "official_api_only"
    business_app_coexistence = "business_app_coexistence"
    evolution_linked_device = "evolution_linked_device"
    hybrid_migration = "hybrid_migration"


class MessageOrigin(str, enum.Enum):
    customer = "customer"
    crm_agent = "crm_agent"
    bot = "bot"
    whatsapp_business_app = "whatsapp_business_app"
    provider_api = "provider_api"
    campaign = "campaign"
    system = "system"


class ContactType(str, enum.Enum):
    person = "person"
    organization = "organization"


class ContactStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    blocked = "blocked"


class ConversationStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    pending = "pending"


class SlaStatus(str, enum.Enum):
    ok = "ok"
    at_risk = "at_risk"
    violated = "violated"


class ConvPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class MessageType(str, enum.Enum):
    text = "text"
    image = "image"
    audio = "audio"
    video = "video"
    file = "file"
    internal_note = "internal_note"
    activity = "activity"


class SenderType(str, enum.Enum):
    agent = "agent"
    contact = "contact"
    bot = "bot"
    system = "system"


class ConvEventType(str, enum.Enum):
    assigned = "assigned"
    unassigned = "unassigned"
    transferred = "transferred"
    opened = "opened"
    resolved = "resolved"
    reopened = "reopened"
    label_added = "label_added"
    label_removed = "label_removed"
    note_added = "note_added"
    bot_handed_off = "bot_handed_off"
    bot_took_over = "bot_took_over"


class SlaEventType(str, enum.Enum):
    first_response = "first_response"
    resolution = "resolution"


class FlowTriggerType(str, enum.Enum):
    message_received = "message_received"
    keyword_match = "keyword_match"
    conversation_created = "conversation_created"
    campaign_reply = "campaign_reply"
    manual = "manual"
    schedule = "schedule"


class FlowExecStatus(str, enum.Enum):
    running = "running"
    waiting_input = "waiting_input"
    completed = "completed"
    error = "error"
    cancelled = "cancelled"


class ChannelAccountStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    error = "error"
    disconnected = "disconnected"
