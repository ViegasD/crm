// Shared TypeScript types mirroring backend Pydantic schemas

export type ConversationStatus = "open" | "in_progress" | "resolved" | "pending";
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
  unreadAgentCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface Message {
  id: string;
  conversationId: string;
  senderType: "agent" | "contact" | "bot" | "system";
  senderId: string;
  content?: string;
  type: MessageType;
  attachments: Attachment[];
  createdAt: string;
}

export interface Attachment {
  key: string;
  bucket: string;
  url: string;
  name: string;
  mimeType: string;
  sizeBytes: number;
}
