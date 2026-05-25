"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout";
import { useAuthStore } from "@/stores/auth-store";
import { usersApi, workspacesApi } from "@/lib/api";
import type { Workspace } from "@/types/workspace";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { accessToken, setUser, setWorkspaces, setCurrentWorkspace, currentWorkspace } = useAuthStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
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
  }, [mounted, accessToken]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!mounted || !accessToken) return null;

  return (
    <div className="flex h-screen overflow-hidden bg-surface-2">
      <Sidebar />
      <main className="flex-1 overflow-hidden">{children}</main>
    </div>
  );
}

