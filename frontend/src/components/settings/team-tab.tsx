"use client";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { workspacesApi } from "@/lib/api";
import type { Membership } from "@/types/workspace";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";

export function TeamTab() {
  const { currentWorkspace } = useAuthStore();
  const [members, setMembers] = useState<Membership[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!currentWorkspace) return;
    setLoading(true);
    workspacesApi.listMembers(currentWorkspace.id)
      .then((r) => setMembers(r.data ?? []))
      .finally(() => setLoading(false));
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function remove(userId: string) {
    if (!currentWorkspace) return;
    if (!confirm("Remove this member?")) return;
    await workspacesApi.removeMember(currentWorkspace.id, userId);
    setMembers((prev) => prev.filter((m) => m.userId !== userId));
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-4">
        <h2 className="font-semibold text-slate-900">Team Members</h2>
        <p className="text-sm text-muted">Manage who has access to this workspace</p>
      </div>

      {loading && <p className="text-sm text-muted">Loading…</p>}
      <div className="rounded-lg border border-border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-surface-2 border-b border-border">
            <tr>
              <th className="px-4 py-2.5 text-left font-medium text-muted">Member</th>
              <th className="px-4 py-2.5 text-left font-medium text-muted">Role</th>
              <th className="px-4 py-2.5" />
            </tr>
          </thead>
          <tbody className="divide-y divide-border bg-white">
            {members.map((m) => (
              <tr key={m.userId}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Avatar name={m.user?.name ?? m.user?.email} size="sm" />
                    <div>
                      <p className="font-medium text-slate-900">{m.user?.name ?? "—"}</p>
                      <p className="text-xs text-muted">{m.user?.email}</p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3 capitalize text-slate-600">{m.role}</td>
                <td className="px-4 py-3">
                  <button onClick={() => remove(m.userId)} className="text-muted hover:text-danger">
                    <Trash2 className="h-4 w-4" />
                  </button>

                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
