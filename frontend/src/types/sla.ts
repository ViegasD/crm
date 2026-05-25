export interface SlaPolicy {
  id: string;
  workspaceId: string;
  sectorId?: string;
  channelAccountId?: string;
  priority?: string;
  name: string;
  firstResponseMinutes: number;
  nextResponseMinutes?: number;
  resolutionMinutes: number;
  reopenResponseMinutes?: number;
  businessHoursOnly: boolean;
  pauseWhenWaitingCustomer: boolean;
  atRiskThresholdPct: number;
  steps: Record<string, unknown>;
  active: boolean;
  createdAt: string;
}

export interface AgentCapacity {
  id: string;
  workspaceId: string;
  userId: string;
  sectorId?: string;
  maxConversations: number;
  maxWeight: number;
  priorityWeights: Record<string, number>;
}

export type AgentPresence = "online" | "away" | "busy" | "in_call" | "on_break" | "offline" | "invisible";

export interface AgentStatus {
  id: string;
  workspaceId: string;
  userId: string;
  status: AgentPresence;
  reasonId?: string | null;
  note?: string | null;
  sinceAt: string;
  updatedAt: string;
  userName?: string | null;
  userEmail?: string | null;
  reasonLabel?: string | null;
}

export interface AgentPauseReason {
  id: string;
  workspaceId: string;
  label: string;
  active: boolean;
  position: number;
}

export interface BusinessHours {
  id: string;
  workspaceId: string;
  sectorId?: string | null;
  weekday: number;
  startMinute: number;
  endMinute: number;
  timezone: string;
  active: boolean;
}

export interface RoutingRule {
  id: string;
  workspaceId: string;
  sectorId?: string | null;
  strategy: "round_robin" | "least_busy" | "sticky_agent" | "manual";
  tiebreaker: string;
  stickyHours: number;
  autoReassignMinutes: number;
  reopenWindowHours: number;
}

export interface SupervisorSectorMetric {
  sectorId?: string | null;
  sectorName: string;
  queued: number;
  active: number;
  atRisk: number;
  violated: number;
}

export interface SupervisorAgentMetric {
  userId: string;
  name: string;
  email: string;
  role: string;
  sectorId?: string | null;
  status: AgentPresence;
  reason?: string | null;
  sinceAt?: string | null;
  maxConversations: number;
  maxWeight: number;
  assignedOpen: number;
  weightedLoad: number;
  availableSlots: number;
  atRisk: number;
  violated: number;
}

export interface SupervisorAlert {
  conversationId: string;
  contactName?: string | null;
  assigneeId?: string | null;
  sectorId?: string | null;
  slaStatus: "ok" | "at_risk" | "violated";
  priority: string;
  lastMessageAt?: string | null;
}

export interface SupervisorOverview {
  totals: {
    queued: number;
    active: number;
    atRisk: number;
    violated: number;
    agentsOnline: number;
    capacityUsed: number;
    capacityTotal: number;
  };
  sectors: SupervisorSectorMetric[];
  agents: SupervisorAgentMetric[];
  alerts: SupervisorAlert[];
}

// ── Stage 9 extras types ────────────────────────────────────────────────────

export interface AutoResolveRule {
  id: string;
  workspaceId: string;
  sectorId?: string | null;
  inactivityHours: number;
  statusFrom: string[];
  statusTo: string;
  active: boolean;
}

export interface BusinessHoliday {
  id: string;
  workspaceId: string;
  sectorId?: string | null;
  holidayDate: string;
  label: string;
  treatAs: "closed" | "half_day" | "custom";
  customStartMinute?: number | null;
  customEndMinute?: number | null;
}

export type EscalationAction = "notify" | "reassign" | "webhook";

export interface SlaEscalationRule {
  id?: string;
  workspaceId?: string;
  policyId?: string;
  thresholdPct: number;
  action: EscalationAction;
  targetRole?: string | null;
  targetUserId?: string | null;
  webhookUrl?: string | null;
  position: number;
  active: boolean;
}

export interface IdleRule {
  id: string;
  workspaceId: string;
  idleMinutes: number;
  offlineMinutes: number;
  active: boolean;
}

export type NotificationKind = "email" | "slack_webhook" | "inapp" | "webhook";

export interface NotificationChannel {
  id: string;
  workspaceId: string;
  name: string;
  kind: NotificationKind;
  config: Record<string, unknown>;
  events: string[];
  active: boolean;
  createdAt: string;
}

export interface NotificationDelivery {
  id: string;
  workspaceId: string;
  channelId?: string | null;
  userId?: string | null;
  eventType: string;
  title: string;
  body?: string | null;
  status: string;
  readAt?: string | null;
  createdAt: string;
}

export interface ExternalWebhookSubscription {
  id: string;
  workspaceId: string;
  name: string;
  url: string;
  events: string[];
  active: boolean;
  createdAt: string;
}

export interface ExternalWebhookDelivery {
  id: string;
  subscriptionId: string;
  eventType: string;
  status: string;
  attempts: number;
  lastError?: string | null;
  responseStatus?: number | null;
  deliveredAt?: string | null;
  createdAt: string;
}

export interface ConversationLock {
  id: string;
  conversationId: string;
  holderUserId: string;
  acquiredAt: string;
  expiresAt: string;
  holderName?: string | null;
}

export interface CsatSummary {
  items: Array<{
    id: string;
    conversationId: string;
    assigneeId?: string | null;
    score?: number | null;
    feedback?: string | null;
    sentAt: string;
    respondedAt?: string | null;
  }>;
  averageScore?: number | null;
}

export interface HeatmapCell {
  userId: string;
  userName: string;
  hour: number;
  minutesAssigned: number;
  conversations: number;
}

export interface HeatmapData {
  days: number;
  cells: HeatmapCell[];
}
