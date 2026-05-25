import axios, { type AxiosError } from "axios";

function toCamelCase(key: string) {
  return key.replace(/_([a-z0-9])/g, (_, char: string) => char.toUpperCase());
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return Object.prototype.toString.call(value) === "[object Object]";
}

function camelizeKeys<T>(value: T): T {
  if (Array.isArray(value)) {
    return value.map((item) => camelizeKeys(item)) as T;
  }
  if (!isPlainObject(value)) {
    return value;
  }
  return Object.entries(value).reduce<Record<string, unknown>>((acc, [key, entry]) => {
    acc[toCamelCase(key)] = camelizeKeys(entry);
    return acc;
  }, {}) as T;
}

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-retry on 401: refresh token then retry once
api.interceptors.response.use(
  (res) => {
    res.data = camelizeKeys(res.data);
    return res;
  },
  async (error: AxiosError) => {
    const original = error.config as (typeof error.config) & { _retry?: boolean };
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null;
      if (refresh) {
        try {
          const { data } = await axios.post(
            `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/auth/refresh`,
            { refresh_token: refresh }
          );
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          original.headers!["Authorization"] = `Bearer ${data.access_token}`;
          return api(original);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// ─── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post<{ accessToken: string; refreshToken: string }>("/api/v1/auth/login", { email, password }),
  register: (name: string, email: string, password: string) =>
    api.post("/api/v1/auth/register", { name, email, password }),
  refresh: (refreshToken: string) =>
    api.post<{ accessToken: string; refreshToken: string }>("/api/v1/auth/refresh", { refresh_token: refreshToken }),
};

// ─── Users ────────────────────────────────────────────────────────────────────
export const usersApi = {
  me: () => api.get("/api/v1/users/me"),
  updateMe: (data: { name?: string; avatar_url?: string }) => api.patch("/api/v1/users/me", data),
};

// ─── Workspaces ───────────────────────────────────────────────────────────────
export const workspacesApi = {
  list: () => api.get("/api/v1/workspaces"),
  create: (name: string, slug: string) => api.post("/api/v1/workspaces", { name, slug }),
  get: (id: string) => api.get(`/api/v1/workspaces/${id}`),
  listMembers: (id: string) => api.get(`/api/v1/workspaces/${id}/members`),
  removeMember: (wsId: string, userId: string) => api.delete(`/api/v1/workspaces/${wsId}/members/${userId}`),
};

// ─── Sectors ──────────────────────────────────────────────────────────────────
export const sectorsApi = {
  list: (wsId: string) => api.get(`/api/v1/workspaces/${wsId}/sectors`),
  create: (wsId: string, name: string, description?: string) =>
    api.post(`/api/v1/workspaces/${wsId}/sectors`, { name, description }),
  delete: (wsId: string, sectorId: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/sectors/${sectorId}`),
  addMember: (wsId: string, sectorId: string, userId: string) =>
    api.post(`/api/v1/workspaces/${wsId}/sectors/${sectorId}/members`, { user_id: userId }),
  removeMember: (wsId: string, sectorId: string, userId: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/sectors/${sectorId}/members/${userId}`),
};

// ─── Channel Accounts ─────────────────────────────────────────────────────────
export const channelsApi = {
  list: (wsId: string) => api.get(`/api/v1/workspaces/${wsId}/channels`),
  create: (wsId: string, data: Record<string, unknown>) =>
    api.post(`/api/v1/workspaces/${wsId}/channels`, data),
  update: (wsId: string, channelId: string, data: Record<string, unknown>) =>
    api.patch(`/api/v1/workspaces/${wsId}/channels/${channelId}`, data),
  delete: (wsId: string, channelId: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/channels/${channelId}`),
  upsertCredential: (wsId: string, channelId: string, credentialType: string, payload: Record<string, unknown>) =>
    api.put(`/api/v1/workspaces/${wsId}/channels/${channelId}/credentials`, { credential_type: credentialType, payload }),
};

// ─── Contacts ─────────────────────────────────────────────────────────────────
export const contactsApi = {
  list: (wsId: string, params?: { search?: string; page?: number; page_size?: number }) =>
    api.get(`/api/v1/workspaces/${wsId}/contacts`, { params }),
  get: (wsId: string, contactId: string) =>
    api.get(`/api/v1/workspaces/${wsId}/contacts/${contactId}`),
  create: (wsId: string, data: Record<string, unknown>) =>
    api.post(`/api/v1/workspaces/${wsId}/contacts`, data),
  update: (wsId: string, contactId: string, data: Record<string, unknown>) =>
    api.patch(`/api/v1/workspaces/${wsId}/contacts/${contactId}`, data),
  delete: (wsId: string, contactId: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/contacts/${contactId}`),
  timeline: (
    wsId: string,
    contactId: string,
    params?: {
      channel_account_id?: string;
      since?: string;
      until?: string;
      status?: string[];
      active_conversation_id?: string;
      limit_per_conversation?: number;
    },
  ) => api.get(`/api/v1/workspaces/${wsId}/contacts/${contactId}/timeline`, { params }),
};

// ─── Conversation reopen / new-protocol policies ─────────────────────────────
export const conversationPoliciesApi = {
  list: (wsId: string) =>
    api.get(`/api/v1/workspaces/${wsId}/conversation-policies`),
  effective: (wsId: string, sectorId?: string) =>
    api.get(`/api/v1/workspaces/${wsId}/conversation-policies/effective`, {
      params: sectorId ? { sector_id: sectorId } : undefined,
    }),
  upsert: (
    wsId: string,
    data: {
      sector_id?: string | null;
      reopen_mode: "window" | "always_reopen" | "always_new";
      reopen_window_hours: number;
      inherit_assignee_on_new: boolean;
    },
  ) => api.put(`/api/v1/workspaces/${wsId}/conversation-policies`, data),
  delete: (wsId: string, policyId: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/conversation-policies/${policyId}`),
};

// ─── Conversations ────────────────────────────────────────────────────────────
export const conversationsApi = {
  list: (wsId: string, params?: Record<string, unknown>) =>
    api.get(`/api/v1/workspaces/${wsId}/conversations`, { params }),
  get: (wsId: string, convId: string) =>
    api.get(`/api/v1/workspaces/${wsId}/conversations/${convId}`),
  update: (wsId: string, convId: string, data: Record<string, unknown>) =>
    api.patch(`/api/v1/workspaces/${wsId}/conversations/${convId}`, data),
  transfer: (
    wsId: string,
    convId: string,
    data: { assignee_id?: string; sector_id?: string; note?: string; transfer_reason_id?: string },
  ) => api.post(`/api/v1/workspaces/${wsId}/conversations/${convId}/transfer`, data),
  events: (wsId: string, convId: string) =>
    api.get(`/api/v1/workspaces/${wsId}/conversations/${convId}/events`),
  participants: (wsId: string, convId: string) =>
    api.get(`/api/v1/workspaces/${wsId}/conversations/${convId}/participants`),
  addParticipant: (wsId: string, convId: string, userId: string) =>
    api.post(`/api/v1/workspaces/${wsId}/conversations/${convId}/participants`, { user_id: userId }),
  removeParticipant: (wsId: string, convId: string, userId: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/conversations/${convId}/participants/${userId}`),
  bulkLabel: (wsId: string, data: { conversation_ids: string[]; label_id: string }) =>
    api.post(`/api/v1/workspaces/${wsId}/conversations/bulk/label`, data),
  bulkTransfer: (
    wsId: string,
    data: { conversation_ids: string[]; assignee_id?: string; sector_id?: string; note?: string; transfer_reason_id?: string },
  ) => api.post(`/api/v1/workspaces/${wsId}/conversations/bulk/transfer`, data),
  bulkStatus: (
    wsId: string,
    data: { conversation_ids: string[]; status: string; resolve_note?: string; service_reason_id?: string },
  ) => api.post(`/api/v1/workspaces/${wsId}/conversations/bulk/status`, data),
  bulkAssign: (wsId: string, data: { conversation_ids: string[]; assignee_id: string }) =>
    api.post(`/api/v1/workspaces/${wsId}/conversations/bulk/assign`, data),
  bulkAddParticipant: (wsId: string, data: { conversation_ids: string[]; user_id: string }) =>
    api.post(`/api/v1/workspaces/${wsId}/conversations/bulk/add-participant`, data),
};

// ─── Messages ─────────────────────────────────────────────────────────────────
export const messagesApi = {
  list: (wsId: string, convId: string, params?: { page?: number; page_size?: number }) =>
    api.get(`/api/v1/workspaces/${wsId}/conversations/${convId}/messages`, { params }),
  send: (wsId: string, convId: string, data: { content?: string; type?: string; attachments?: unknown[]; is_note?: boolean }) =>
    api.post(`/api/v1/workspaces/${wsId}/conversations/${convId}/messages`, data),
  markRead: (wsId: string, convId: string) =>
    api.post(`/api/v1/workspaces/${wsId}/conversations/${convId}/messages/read`),
};

// ─── Labels ───────────────────────────────────────────────────────────────────
export const labelsApi = {
  list: (wsId: string) => api.get(`/api/v1/workspaces/${wsId}/labels`),
  create: (wsId: string, data: { name: string; color: string; category_id?: string | null; description?: string | null }) =>
    api.post(`/api/v1/workspaces/${wsId}/labels`, data),
  update: (wsId: string, labelId: string, data: Record<string, unknown>) =>
    api.patch(`/api/v1/workspaces/${wsId}/labels/${labelId}`, data),
  delete: (wsId: string, labelId: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/labels/${labelId}`),
  assign: (wsId: string, labelId: string, conversationId: string) =>
    api.post(`/api/v1/workspaces/${wsId}/labels/${labelId}/assign`, { conversation_id: conversationId }),
  unassign: (wsId: string, labelId: string, conversationId: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/labels/${labelId}/assign/${conversationId}`),
  // categories
  listCategories: (wsId: string) =>
    api.get(`/api/v1/workspaces/${wsId}/labels/categories`),
  createCategory: (wsId: string, data: Record<string, unknown>) =>
    api.post(`/api/v1/workspaces/${wsId}/labels/categories`, data),
  updateCategory: (wsId: string, id: string, data: Record<string, unknown>) =>
    api.patch(`/api/v1/workspaces/${wsId}/labels/categories/${id}`, data),
  deleteCategory: (wsId: string, id: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/labels/categories/${id}`),
};

// ─── Canned responses ─────────────────────────────────────────────────────────
export const cannedResponsesApi = {
  list: (wsId: string, params?: { category_id?: string; scope?: "all" | "workspace" | "sector" | "personal"; active?: boolean }) =>
    api.get(`/api/v1/workspaces/${wsId}/canned-responses`, { params }),
  create: (wsId: string, data: Record<string, unknown>) =>
    api.post(`/api/v1/workspaces/${wsId}/canned-responses`, data),
  update: (wsId: string, responseId: string, data: Record<string, unknown>) =>
    api.patch(`/api/v1/workspaces/${wsId}/canned-responses/${responseId}`, data),
  delete: (wsId: string, responseId: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/canned-responses/${responseId}`),
  render: (wsId: string, responseId: string, data: { conversation_id?: string }) =>
    api.post(`/api/v1/workspaces/${wsId}/canned-responses/${responseId}/render`, data),
  // categories
  listCategories: (wsId: string) =>
    api.get(`/api/v1/workspaces/${wsId}/canned-responses/categories`),
  createCategory: (wsId: string, data: Record<string, unknown>) =>
    api.post(`/api/v1/workspaces/${wsId}/canned-responses/categories`, data),
  updateCategory: (wsId: string, id: string, data: Record<string, unknown>) =>
    api.patch(`/api/v1/workspaces/${wsId}/canned-responses/categories/${id}`, data),
  deleteCategory: (wsId: string, id: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/canned-responses/categories/${id}`),
};

// ─── Macros ───────────────────────────────────────────────────────────────────
export const macrosApi = {
  list: (wsId: string) => api.get(`/api/v1/workspaces/${wsId}/macros`),
  get: (wsId: string, id: string) => api.get(`/api/v1/workspaces/${wsId}/macros/${id}`),
  create: (wsId: string, data: Record<string, unknown>) =>
    api.post(`/api/v1/workspaces/${wsId}/macros`, data),
  update: (wsId: string, id: string, data: Record<string, unknown>) =>
    api.patch(`/api/v1/workspaces/${wsId}/macros/${id}`, data),
  delete: (wsId: string, id: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/macros/${id}`),
  run: (wsId: string, id: string, conversationId: string) =>
    api.post(`/api/v1/workspaces/${wsId}/macros/${id}/run`, { conversation_id: conversationId }),
};

// ─── Catalog: reasons, snooze, views, mentions ───────────────────────────────
export const transferReasonsApi = {
  list: (wsId: string, params?: { active?: boolean }) =>
    api.get(`/api/v1/workspaces/${wsId}/transfer-reasons`, { params }),
  create: (wsId: string, data: Record<string, unknown>) =>
    api.post(`/api/v1/workspaces/${wsId}/transfer-reasons`, data),
  update: (wsId: string, id: string, data: Record<string, unknown>) =>
    api.patch(`/api/v1/workspaces/${wsId}/transfer-reasons/${id}`, data),
  delete: (wsId: string, id: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/transfer-reasons/${id}`),
};

export const serviceReasonsApi = {
  list: (wsId: string, params?: { active?: boolean }) =>
    api.get(`/api/v1/workspaces/${wsId}/service-reasons`, { params }),
  create: (wsId: string, data: Record<string, unknown>) =>
    api.post(`/api/v1/workspaces/${wsId}/service-reasons`, data),
  update: (wsId: string, id: string, data: Record<string, unknown>) =>
    api.patch(`/api/v1/workspaces/${wsId}/service-reasons/${id}`, data),
  delete: (wsId: string, id: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/service-reasons/${id}`),
};

export const snoozeApi = {
  get: (wsId: string, convId: string) =>
    api.get(`/api/v1/workspaces/${wsId}/conversations/${convId}/snooze`),
  set: (wsId: string, convId: string, until: string, reason?: string) =>
    api.post(`/api/v1/workspaces/${wsId}/conversations/${convId}/snooze`, { until, reason }),
  clear: (wsId: string, convId: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/conversations/${convId}/snooze`),
};

export const viewsApi = {
  list: (wsId: string) => api.get(`/api/v1/workspaces/${wsId}/views`),
  create: (wsId: string, data: Record<string, unknown>) =>
    api.post(`/api/v1/workspaces/${wsId}/views`, data),
  update: (wsId: string, id: string, data: Record<string, unknown>) =>
    api.patch(`/api/v1/workspaces/${wsId}/views/${id}`, data),
  delete: (wsId: string, id: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/views/${id}`),
};

export const mentionsApi = {
  list: (wsId: string, params?: { unread?: boolean; page?: number; page_size?: number }) =>
    api.get(`/api/v1/workspaces/${wsId}/mentions`, { params }),
  markRead: (wsId: string, mentionIds?: string[]) =>
    api.post(`/api/v1/workspaces/${wsId}/mentions/read`, { mention_ids: mentionIds ?? null }),
};

// ─── Webhook events (admin) ──────────────────────────────────────────────────
export const webhookEventsApi = {
  list: (
    wsId: string,
    params?: { status?: string; provider?: string; channel_account_id?: string; page?: number; page_size?: number },
  ) => api.get(`/api/v1/workspaces/${wsId}/webhook-events`, { params }),
  stats: (wsId: string) => api.get(`/api/v1/workspaces/${wsId}/webhook-events/stats`),
  get: (wsId: string, id: string) => api.get(`/api/v1/workspaces/${wsId}/webhook-events/${id}`),
  retry: (wsId: string, id: string) =>
    api.post(`/api/v1/workspaces/${wsId}/webhook-events/${id}/retry`),
};

// ─── Webhook ops (Tier 2) ────────────────────────────────────────────────────
export const webhookOpsApi = {
  // IP allowlist
  listIpAllowlist: (wsId: string, provider?: string) =>
    api.get(`/api/v1/workspaces/${wsId}/webhook-ops/ip-allowlist`, { params: { provider } }),
  addIpAllowlist: (wsId: string, data: { provider: string; cidr: string; description?: string | null }) =>
    api.post(`/api/v1/workspaces/${wsId}/webhook-ops/ip-allowlist`, data),
  deleteIpAllowlist: (wsId: string, id: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/webhook-ops/ip-allowlist/${id}`),
  // Circuits
  listCircuits: (wsId: string) =>
    api.get(`/api/v1/workspaces/${wsId}/webhook-ops/circuits`),
  resetCircuit: (wsId: string, channelAccountId: string) =>
    api.post(`/api/v1/workspaces/${wsId}/webhook-ops/circuits/${channelAccountId}/reset`),
  // Secret rotation
  rotateCredential: (
    wsId: string,
    channelAccountId: string,
    data: { credential_type: string; payload: Record<string, unknown>; grace_hours?: number },
  ) =>
    api.post(`/api/v1/workspaces/${wsId}/webhook-ops/channels/${channelAccountId}/rotate-credential`, data),
  finalizeRotation: (wsId: string, channelAccountId: string, credentialType: string) =>
    api.post(
      `/api/v1/workspaces/${wsId}/webhook-ops/channels/${channelAccountId}/finalize-rotation`,
      null,
      { params: { credential_type: credentialType } },
    ),
  // Attempts + latency
  listAttempts: (wsId: string, eventId: string) =>
    api.get(`/api/v1/workspaces/${wsId}/webhook-ops/events/${eventId}/attempts`),
  latency: (wsId: string, windowMinutes = 60) =>
    api.get(`/api/v1/workspaces/${wsId}/webhook-ops/latency`, { params: { window_minutes: windowMinutes } }),
};

// ─── Flows ────────────────────────────────────────────────────────────────────
export const flowsApi = {
  list: (wsId: string) => api.get(`/api/v1/workspaces/${wsId}/flows`),
  get: (wsId: string, flowId: string) => api.get(`/api/v1/workspaces/${wsId}/flows/${flowId}`),
  create: (wsId: string, data: Record<string, unknown>) =>
    api.post(`/api/v1/workspaces/${wsId}/flows`, data),
  update: (wsId: string, flowId: string, data: Record<string, unknown>) =>
    api.patch(`/api/v1/workspaces/${wsId}/flows/${flowId}`, data),
  delete: (wsId: string, flowId: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/flows/${flowId}`),
  activate: (wsId: string, flowId: string) =>
    api.post(`/api/v1/workspaces/${wsId}/flows/${flowId}/activate`),
  deactivate: (wsId: string, flowId: string) =>
    api.post(`/api/v1/workspaces/${wsId}/flows/${flowId}/deactivate`),
};

// ─── SLA ──────────────────────────────────────────────────────────────────────
export const slaApi = {
  listPolicies: (wsId: string) => api.get(`/api/v1/workspaces/${wsId}/sla/policies`),
  createPolicy: (wsId: string, data: Record<string, unknown>) =>
    api.post(`/api/v1/workspaces/${wsId}/sla/policies`, data),
  updatePolicy: (wsId: string, policyId: string, data: Record<string, unknown>) =>
    api.patch(`/api/v1/workspaces/${wsId}/sla/policies/${policyId}`, data),
  deletePolicy: (wsId: string, policyId: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/sla/policies/${policyId}`),
  listCapacity: (wsId: string) => api.get(`/api/v1/workspaces/${wsId}/sla/capacity`),
  setCapacity: (wsId: string, data: Record<string, unknown>) =>
    api.put(`/api/v1/workspaces/${wsId}/sla/capacity`, data),
  listPauseReasons: (wsId: string) => api.get(`/api/v1/workspaces/${wsId}/sla/pause-reasons`),
  createPauseReason: (wsId: string, data: Record<string, unknown>) =>
    api.post(`/api/v1/workspaces/${wsId}/sla/pause-reasons`, data),
  listAgentStatus: (wsId: string) => api.get(`/api/v1/workspaces/${wsId}/sla/agent-status`),
  setAgentStatus: (wsId: string, userId: string, data: Record<string, unknown>) =>
    api.put(`/api/v1/workspaces/${wsId}/sla/agent-status/${userId}`, data),
  listBusinessHours: (wsId: string, params?: { sector_id?: string }) =>
    api.get(`/api/v1/workspaces/${wsId}/sla/business-hours`, { params }),
  createBusinessHours: (wsId: string, data: Record<string, unknown>) =>
    api.post(`/api/v1/workspaces/${wsId}/sla/business-hours`, data),
  deleteBusinessHours: (wsId: string, hoursId: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/sla/business-hours/${hoursId}`),
  listRoutingRules: (wsId: string) => api.get(`/api/v1/workspaces/${wsId}/sla/routing-rules`),
  upsertRoutingRule: (wsId: string, data: Record<string, unknown>) =>
    api.put(`/api/v1/workspaces/${wsId}/sla/routing-rules`, data),
  assignNext: (wsId: string, data: { conversation_id: string; sector_id?: string | null }) =>
    api.post(`/api/v1/workspaces/${wsId}/sla/assign-next`, data),
  evaluate: (wsId: string) => api.post(`/api/v1/workspaces/${wsId}/sla/evaluate`),
  supervisorOverview: (wsId: string) => api.get(`/api/v1/workspaces/${wsId}/sla/supervisor/overview`),
  // pause reasons CRUD (extended)
  updatePauseReason: (wsId: string, id: string, data: Record<string, unknown>) =>
    api.patch(`/api/v1/workspaces/${wsId}/sla/pause-reasons/${id}`, data),
  deletePauseReason: (wsId: string, id: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/sla/pause-reasons/${id}`),
  // auto-resolve rules
  listAutoResolveRules: (wsId: string) =>
    api.get(`/api/v1/workspaces/${wsId}/sla/auto-resolve-rules`),
  createAutoResolveRule: (wsId: string, data: Record<string, unknown>) =>
    api.post(`/api/v1/workspaces/${wsId}/sla/auto-resolve-rules`, data),
  updateAutoResolveRule: (wsId: string, id: string, data: Record<string, unknown>) =>
    api.patch(`/api/v1/workspaces/${wsId}/sla/auto-resolve-rules/${id}`, data),
  deleteAutoResolveRule: (wsId: string, id: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/sla/auto-resolve-rules/${id}`),
  // business hours grid (bulk replace)
  replaceBusinessHours: (
    wsId: string,
    rows: Array<Record<string, unknown>>,
    sectorId?: string | null,
  ) =>
    api.put(`/api/v1/workspaces/${wsId}/sla/business-hours`, rows, {
      params: sectorId ? { sector_id: sectorId } : undefined,
    }),
  // escalation chain
  listEscalations: (wsId: string, policyId: string) =>
    api.get(`/api/v1/workspaces/${wsId}/sla/policies/${policyId}/escalations`),
  replaceEscalations: (wsId: string, policyId: string, rules: Array<Record<string, unknown>>) =>
    api.put(`/api/v1/workspaces/${wsId}/sla/policies/${policyId}/escalations`, rules),
};

// ─── Stage 9 extras: holidays, locks, idle, notifications, outbound, csat, heatmap ─
export const stage9Api = {
  // business holidays
  listHolidays: (wsId: string) =>
    api.get(`/api/v1/workspaces/${wsId}/business-holidays`),
  createHoliday: (wsId: string, data: Record<string, unknown>) =>
    api.post(`/api/v1/workspaces/${wsId}/business-holidays`, data),
  deleteHoliday: (wsId: string, id: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/business-holidays/${id}`),
  // sla override on conversation
  setSlaOverride: (wsId: string, convId: string, policyId: string | null) =>
    api.put(`/api/v1/workspaces/${wsId}/conversations/${convId}/sla-override`, {
      sla_policy_override_id: policyId,
    }),
  // conversation lock
  getLock: (wsId: string, convId: string) =>
    api.get(`/api/v1/workspaces/${wsId}/conversations/${convId}/lock`),
  acquireLock: (wsId: string, convId: string, ttlSeconds = 90) =>
    api.post(`/api/v1/workspaces/${wsId}/conversations/${convId}/lock`, {
      ttl_seconds: ttlSeconds,
    }),
  releaseLock: (wsId: string, convId: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/conversations/${convId}/lock`),
  // idle rule
  getIdleRule: (wsId: string) => api.get(`/api/v1/workspaces/${wsId}/idle-rule`),
  upsertIdleRule: (wsId: string, data: Record<string, unknown>) =>
    api.put(`/api/v1/workspaces/${wsId}/idle-rule`, data),
  // notifications
  listNotificationChannels: (wsId: string) =>
    api.get(`/api/v1/workspaces/${wsId}/notification-channels`),
  createNotificationChannel: (wsId: string, data: Record<string, unknown>) =>
    api.post(`/api/v1/workspaces/${wsId}/notification-channels`, data),
  updateNotificationChannel: (wsId: string, id: string, data: Record<string, unknown>) =>
    api.patch(`/api/v1/workspaces/${wsId}/notification-channels/${id}`, data),
  deleteNotificationChannel: (wsId: string, id: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/notification-channels/${id}`),
  // per-user notification inbox
  listNotifications: (wsId: string, params?: { unread?: boolean; page?: number }) =>
    api.get(`/api/v1/workspaces/${wsId}/notifications`, { params }),
  markNotificationsRead: (wsId: string, ids?: string[]) =>
    api.post(`/api/v1/workspaces/${wsId}/notifications/read`, { ids: ids ?? null }),
  // outbound API webhooks
  listApiWebhooks: (wsId: string) => api.get(`/api/v1/workspaces/${wsId}/api-webhooks`),
  createApiWebhook: (wsId: string, data: Record<string, unknown>) =>
    api.post(`/api/v1/workspaces/${wsId}/api-webhooks`, data),
  deleteApiWebhook: (wsId: string, id: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/api-webhooks/${id}`),
  listApiWebhookDeliveries: (wsId: string, subId: string, limit = 50) =>
    api.get(`/api/v1/workspaces/${wsId}/api-webhooks/${subId}/deliveries`, {
      params: { limit },
    }),
  // CSAT
  listCsat: (wsId: string, params?: { only_responded?: boolean; page?: number }) =>
    api.get(`/api/v1/workspaces/${wsId}/csat`, { params }),
  // heatmap
  heatmap: (wsId: string, days = 7) =>
    api.get(`/api/v1/workspaces/${wsId}/supervisor/heatmap`, { params: { days } }),
};

// ─── Media ────────────────────────────────────────────────────────────────────
export const mediaApi = {
  upload: (workspaceId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<{ key: string; url: string }>(
      `/api/v1/media/upload?workspace_id=${workspaceId}`,
      form,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
  },
  presign: (key: string) => api.get<{ url: string }>("/api/v1/media/presign", { params: { key } }),
};
