import axios, { type AxiosError } from "axios";

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
  (res) => res,
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
    api.post<{ access_token: string; refresh_token: string }>("/api/v1/auth/login", { email, password }),
  register: (name: string, email: string, password: string) =>
    api.post("/api/v1/auth/register", { name, email, password }),
  refresh: (refreshToken: string) =>
    api.post<{ access_token: string; refresh_token: string }>("/api/v1/auth/refresh", { refresh_token: refreshToken }),
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
};

// ─── Conversations ────────────────────────────────────────────────────────────
export const conversationsApi = {
  list: (wsId: string, params?: Record<string, unknown>) =>
    api.get(`/api/v1/workspaces/${wsId}/conversations`, { params }),
  get: (wsId: string, convId: string) =>
    api.get(`/api/v1/workspaces/${wsId}/conversations/${convId}`),
  update: (wsId: string, convId: string, data: Record<string, unknown>) =>
    api.patch(`/api/v1/workspaces/${wsId}/conversations/${convId}`, data),
  transfer: (wsId: string, convId: string, data: { assignee_id?: string; sector_id?: string; note?: string }) =>
    api.post(`/api/v1/workspaces/${wsId}/conversations/${convId}/transfer`, data),
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
  create: (wsId: string, name: string, color: string) =>
    api.post(`/api/v1/workspaces/${wsId}/labels`, { name, color }),
  delete: (wsId: string, labelId: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/labels/${labelId}`),
  assign: (wsId: string, labelId: string, conversationId: string) =>
    api.post(`/api/v1/workspaces/${wsId}/labels/${labelId}/assign`, { conversation_id: conversationId }),
  unassign: (wsId: string, labelId: string, conversationId: string) =>
    api.delete(`/api/v1/workspaces/${wsId}/labels/${labelId}/assign/${conversationId}`),
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
