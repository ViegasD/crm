export type ChannelType = "whatsapp" | "instagram" | "facebook" | "telegram" | "sms" | "email" | "live_chat";
export type WhatsAppProvider = "meta_cloud" | "gupshup" | "evolution_baileys" | "evolution_cloud";
export type ChannelAccountStatus = "active" | "inactive" | "error" | "pending";

export interface ChannelAccount {
  id: string;
  workspaceId: string;
  sectorId?: string;
  channelType: ChannelType;
  provider: WhatsAppProvider | string;
  operationMode?: string;
  displayName: string;
  phoneNumber?: string;
  phoneNumberId?: string;
  wabaId?: string;
  externalAccountId?: string;
  isOfficial: boolean;
  supportsTemplates: boolean;
  supportsCampaigns: boolean;
  status: ChannelAccountStatus;
  enabled: boolean;
  createdAt: string;
}

export interface ChannelAccountCreate {
  channelType: ChannelType;
  provider: string;
  operationMode?: string;
  displayName: string;
  phoneNumber?: string;
  phoneNumberId?: string;
  wabaId?: string;
  externalAccountId?: string;
  sectorId?: string;
}
