"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { mentionsApi } from "@/lib/api";
import type { Mention } from "@/types/conversation";
import { Button } from "@/components/ui/button";
import { AtSign, CheckCheck } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

export default function MentionsPage() {
  const { currentWorkspace } = useAuthStore();
  const workspaceId = currentWorkspace?.id;
  const [items, setItems] = useState<Mention[]>([]);
  const [unread, setUnread] = useState<boolean | undefined>(true);
  const [loading, setLoading] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (!workspaceId) return;
    setLoading(true);
    mentionsApi
      .list(workspaceId, { unread, page_size: 100 })
      .then((r) => {
        setItems(r.data?.items ?? []);
        setUnreadCount(r.data?.unreadCount ?? 0);
      })
      .finally(() => setLoading(false));
  }, [workspaceId, unread]);

  async function markAllRead() {
    if (!currentWorkspace) return;
    await mentionsApi.markRead(currentWorkspace.id);
    setItems((prev) => prev.map((m) => ({ ...m, readAt: m.readAt ?? new Date().toISOString() })));
    setUnreadCount(0);
  }

  if (!currentWorkspace) {
    return <div className="p-6 text-sm text-muted">No workspace selected</div>;
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-border bg-white px-6 py-3">
        <div className="flex items-center gap-2">
          <AtSign className="h-5 w-5 text-primary" />
          <h1 className="text-base font-semibold text-slate-900">Mentions</h1>
          <span className="text-xs text-muted">({unreadCount} unread)</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setUnread(undefined)}
            className={`text-xs font-medium ${unread === undefined ? "text-primary" : "text-muted hover:text-slate-900"}`}
          >
            All
          </button>
          <button
            onClick={() => setUnread(true)}
            className={`text-xs font-medium ${unread === true ? "text-primary" : "text-muted hover:text-slate-900"}`}
          >
            Unread
          </button>
          {unreadCount > 0 && (
            <Button variant="outline" size="sm" onClick={markAllRead}>
              <CheckCheck className="h-3.5 w-3.5" /> Mark all read
            </Button>
          )}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-6">
        {loading && <p className="text-sm text-muted">Loading…</p>}
        {!loading && items.length === 0 && (
          <p className="text-sm text-muted">Nothing to see here. You&apos;ll be notified when teammates mention you.</p>
        )}
        <div className="flex flex-col gap-2 max-w-3xl">
          {items.map((m) => (
            <Link
              key={m.id}
              href={`/inbox?conv=${m.conversationId}`}
              className={`block rounded-lg border border-border bg-white px-4 py-3 hover:bg-surface-2 ${
                !m.readAt ? "border-l-4 border-l-primary" : ""
              }`}
            >
              <p className="text-sm text-slate-800">{m.snippet ?? "(no snippet)"}</p>
              <p className="mt-1 text-[11px] text-muted">
                {formatDistanceToNow(new Date(m.createdAt), { addSuffix: true })} · {m.readAt ? "read" : "unread"}
              </p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
