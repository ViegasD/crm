// Auth store — token, user profile, workspace context
"use client";
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, Workspace } from "@/types/workspace";

function persistTokens(access: string, refresh: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
  document.cookie = `access_token=${access}; path=/; SameSite=Lax`;
}

function clearPersistedTokens() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  document.cookie = "access_token=; path=/; max-age=0";
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  currentWorkspace: Workspace | null;
  workspaces: Workspace[];
  setTokens: (access: string, refresh: string) => void;
  setUser: (user: User) => void;
  setWorkspaces: (ws: Workspace[]) => void;
  setCurrentWorkspace: (ws: Workspace) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      currentWorkspace: null,
      workspaces: [],
      setTokens: (access, refresh) => {
        persistTokens(access, refresh);
        set({ accessToken: access, refreshToken: refresh });
      },
      setUser: (user) => set({ user }),
      setWorkspaces: (workspaces) => set({ workspaces }),
      setCurrentWorkspace: (currentWorkspace) => set({ currentWorkspace }),
      logout: () => {
        clearPersistedTokens();
        set({ accessToken: null, refreshToken: null, user: null, currentWorkspace: null });
      },
    }),
    {
      name: "crm-auth",
      partialize: (s) => ({
        accessToken: s.accessToken,
        refreshToken: s.refreshToken,
        currentWorkspace: s.currentWorkspace,
      }),
    }
  )
);

export function syncAuthTokens(access: string, refresh: string) {
  persistTokens(access, refresh);
  useAuthStore.setState({ accessToken: access, refreshToken: refresh });
}

export function clearAuthState() {
  clearPersistedTokens();
  useAuthStore.setState({ accessToken: null, refreshToken: null, user: null, currentWorkspace: null });
}
