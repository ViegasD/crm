export interface SlaPolicy {
  id: string;
  workspaceId: string;
  sectorId?: string;
  name: string;
  firstResponseMinutes: number;
  resolutionMinutes: number;
  active: boolean;
  createdAt: string;
}

export interface AgentCapacity {
  id: string;
  workspaceId: string;
  userId: string;
  sectorId?: string;
  maxConversations: number;
}

export interface Label {
  id: string;
  workspaceId: string;
  name: string;
  color: string;
  createdAt: string;
}
