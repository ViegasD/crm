// Shared TypeScript types mirroring backend Pydantic schemas

export type ConversationStatus = "open" | "in_progress" | "resolved" | "pending";
export type SlaStatus = "ok" | "at_risk" | "violated";
export type ConvPriority = "low" | "medium" | "high" | "urgent";
export type MessageType = "text" | "image" | "audio" | "video" | "file" | "internal_note" | "activity";
export type ChannelType = "whatsapp" | "instagram" | "facebook" | "telegram" | "line" | "tiktok" | "sms" | "email" | "live_chat";

export type CannedVisibility = "workspace" | "sector" | "user";
export type ViewVisibility = "personal" | "sector" | "workspace";
export type MacroActionType =
  | "send_message"
  | "send_canned"
  | "apply_label"
  | "remove_label"
  | "transfer"
  | "assign"
  | "add_note"
  | "set_status"
  | "set_priority"
  | "add_participant";

export interface LabelInline {
  id: string;
  name: string;
  color: string;
}

export interface UserInline {
  id: string;
  name: string;
  email: string;
  avatarUrl?: string | null;
}

export interface Conversation {
  id: string;
  workspaceId: string;
  channelAccountId: string;
  contactId: string;
  assigneeId?: string;
  assigneeName?: string | null;
  sectorId?: string;
  status: ConversationStatus;
  slaStatus?: SlaStatus;
  priority: ConvPriority;
  unreadAgentCount: number;
  firstRepliedAt?: string;
  resolvedAt?: string;
  createdAt: string;
  updatedAt: string;
  isPrivate?: boolean;
  serviceReasonId?: string | null;
  resolveNote?: string | null;
  contactName?: string;
  contactPhone?: string;
  lastMessage?: string;
  lastMessageAt?: string;
  labels?: LabelInline[];
  snoozedUntil?: string | null;
}

export interface Message {
  id: string;
  conversationId: string;
  senderType: "agent" | "contact" | "bot" | "system";
  senderId?: string;
  senderName?: string;
  origin?: string;
  content?: string;
  type: MessageType;
  attachments: Attachment[];
  isRead: boolean;
  createdAt: string;
}

export interface Attachment {
  key: string;
  bucket?: string;
  url?: string;
  name?: string;
  mimeType?: string;
  sizeBytes?: number;
}

export interface ConversationEvent {
  id: string;
  conversationId: string;
  type: string;
  actorId?: string;
  actorType?: string;
  actorName?: string | null;
  payload?: Record<string, unknown>;
  createdAt: string;
}

export interface ConversationParticipant {
  id: string;
  conversationId: string;
  userId: string;
  createdAt: string;
  user?: UserInline | null;
}

export interface CannedResponse {
  id: string;
  workspaceId: string;
  sectorId?: string | null;
  userId?: string | null;
  categoryId?: string | null;
  visibility: CannedVisibility;
  language?: string | null;
  title: string;
  shortcut: string;
  content: string;
  attachments?: Attachment[];
  active: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CannedCategory {
  id: string;
  workspaceId: string;
  name: string;
  color?: string | null;
  position: number;
  createdAt: string;
}

export interface CannedRenderResponse {
  content: string;
  context: Record<string, string>;
}

export interface Label {
  id: string;
  workspaceId: string;
  name: string;
  color: string;
  categoryId?: string | null;
  description?: string | null;
  createdAt: string;
}

export interface LabelCategory {
  id: string;
  workspaceId: string;
  name: string;
  color?: string | null;
  position: number;
  createdAt: string;
}

export interface WorkspaceMember {
  id: string;
  userId: string;
  workspaceId: string;
  role: "admin" | "supervisor" | "agent";
  createdAt: string;
  user?: UserInline | null;
}

export interface TransferReason {
  id: string;
  workspaceId: string;
  label: string;
  required: boolean;
  active: boolean;
  createdAt: string;
}

export interface ServiceReason {
  id: string;
  workspaceId: string;
  label: string;
  description?: string | null;
  position: number;
  active: boolean;
  createdAt: string;
}

export interface ConversationView {
  id: string;
  workspaceId: string;
  userId?: string | null;
  sectorId?: string | null;
  visibility: ViewVisibility;
  name: string;
  icon?: string | null;
  filters: Record<string, unknown>;
  pinned: boolean;
  position: number;
  createdAt: string;
}

export interface MacroAction {
  id?: string;
  actionType: MacroActionType;
  params: Record<string, unknown>;
  position: number;
}

export interface Macro {
  id: string;
  workspaceId: string;
  name: string;
  description?: string | null;
  visibility: CannedVisibility;
  sectorId?: string | null;
  userId?: string | null;
  active: boolean;
  actions: MacroAction[];
  createdAt: string;
  updatedAt: string;
}

export interface MacroRunResult {
  executed: string[];
  skipped: string[];
  errors: string[];
}

export interface Mention {
  id: string;
  workspaceId: string;
  conversationId: string;
  messageId?: string | null;
  mentionedBy?: string | null;
  snippet?: string | null;
  readAt?: string | null;
  createdAt: string;
}

export interface Snooze {
  id: string;
  conversationId: string;
  until: string;
  reason?: string | null;
  snoozedBy?: string | null;
  createdAt: string;
}

export type WebhookEventStatus =
  | "received"
  | "processing"
  | "processed"
  | "failed"
  | "ignored"
  | "dead_letter";

export interface WebhookEvent {
  id: string;
  workspaceId?: string | null;
  channelAccountId?: string | null;
  provider: string;
  signatureHash?: string | null;
  status: WebhookEventStatus;
  attempts: number;
  maxAttempts: number;
  errorMessage?: string | null;
  nextRetryAt?: string | null;
  lastErrorAt?: string | null;
  createdAt: string;
  processedAt?: string | null;
}

export interface WebhookEventDetail extends WebhookEvent {
  headers: Record<string, unknown>;
  payload: Record<string, unknown>;
}
