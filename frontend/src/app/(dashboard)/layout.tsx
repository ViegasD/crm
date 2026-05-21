"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout";
import { useAuthStore } from "@/stores/auth-store";
import { usersApi, workspacesApi } from "@/lib/api";
import type { Workspace } from "@/types/workspace";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { accessToken, setUser, setWorkspaces, setCurrentWorkspace, currentWorkspace } = useAuthStore();

  useEffect(() => {
    if (!accessToken) {
      router.replace("/login");
      return;
    }
    // Load user + workspaces on mount
    usersApi.me().then((r) => setUser(r.data)).catch(() => router.replace("/login"));
    workspacesApi.list().then((r) => {
      const workspaces = r.data as Workspace[];
      setWorkspaces(workspaces);
      if (!currentWorkspace && workspaces.length > 0) setCurrentWorkspace(workspaces[0]);
    });
  }, [accessToken]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!accessToken) return null;

  return (
    <div className="flex h-screen overflow-hidden bg-surface-2">
      <Sidebar />
      <main className="flex-1 overflow-hidden">{children}</main>
    </div>
  );
}

