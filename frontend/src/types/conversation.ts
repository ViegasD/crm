// Shared TypeScript types mirroring backend Pydantic schemas

export type ConversationStatus = "open" | "in_progress" | "resolved" | "pending";
export type SlaStatus = "ok" | "at_risk" | "violated";
export type ConvPriority = "low" | "normal" | "high" | "urgent";
export type MessageType = "text" | "image" | "audio" | "video" | "file" | "internal_note" | "activity";
export type ChannelType = "whatsapp" | "instagram" | "facebook" | "telegram" | "line" | "tiktok" | "sms" | "email" | "live_chat";

export interface Conversation {
  id: string;
  workspaceId: string;
  channelAccountId: string;
  contactId: string;
  assigneeId?: string;
  sectorId?: string;
  status: ConversationStatus;
  slaStatus?: SlaStatus;
  priority: ConvPriority;
  unreadAgentCount: number;
  firstRepliedAt?: string;
  resolvedAt?: string;
  createdAt: string;
  updatedAt: string;
  // Populated joins (optional, from list/detail)
  contactName?: string;
  contactPhone?: string;
  lastMessage?: string;
  lastMessageAt?: string;
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
  payload?: Record<string, unknown>;
  createdAt: string;
}

