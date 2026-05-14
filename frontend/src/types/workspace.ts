export interface Workspace {
  id: string;
  name: string;
  slug: string;
  plan: string;
  createdAt: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  avatarUrl?: string;
  status: "active" | "inactive" | "suspended";
  createdAt: string;
}

export interface Membership {
  userId: string;
  workspaceId: string;
  role: "admin" | "supervisor" | "agent";
  user?: User;
}

export interface Sector {
  id: string;
  workspaceId: string;
  name: string;
  description?: string;
  createdAt: string;
}
