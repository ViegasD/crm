// Shared TypeScript types mirroring backend Pydantic schemas

export type ConversationStatus = "open" | "in_progress" | "resolved" | "pending";
export type SlaStatus = "ok" | "at_risk" | "violated";
export type ConvPriority = "low" | "medium" | "high" | "urgent";
export type MessageType = "text" | "image" | "audio" | "video" | "file" | "internal_note" | "activity";
export type ChannelType = "whatsapp" | "instagram" | "facebook" | "telegram" | "line" | "tiktok" | "sms" | "email" | "live_chat";

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
  contactName?: string;
  contactPhone?: string;
  lastMessage?: string;
  lastMessageAt?: string;
  labels?: LabelInline[];
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
  sectorId?: string;
  title: string;
  shortcut: string;
  content: string;
  active: boolean;
  createdAt: string;
  updatedAt: string;
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
