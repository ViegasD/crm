// Auth store — token, user profile, workspace context
"use client";
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, Workspace } from "@/types/workspace";

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
        if (typeof window !== "undefined") {
          localStorage.setItem("access_token", access);
          localStorage.setItem("refresh_token", refresh);
          // Set cookie for middleware SSR route protection
          document.cookie = `access_token=${access}; path=/; SameSite=Lax`;
        }
        set({ accessToken: access, refreshToken: refresh });
      },
      setUser: (user) => set({ user }),
      setWorkspaces: (workspaces) => set({ workspaces }),
      setCurrentWorkspace: (currentWorkspace) => set({ currentWorkspace }),
      logout: () => {
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          // Clear cookie
          document.cookie = "access_token=; path=/; max-age=0";
        }
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
