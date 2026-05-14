"use client";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { Input } from "@/components/ui/form";
import { conversationsApi } from "@/lib/api";
import { useConversationStore } from "@/stores/conversation-store";
import type { Conversation, ConversationStatus } from "@/types/conversation";
import { formatDistanceToNow } from "date-fns";

const TABS: { label: string; status: ConversationStatus | "all" }[] = [
  { label: "Open", status: "open" },
  { label: "Active", status: "in_progress" },
  { label: "Pending", status: "pending" },
  { label: "Resolved", status: "resolved" },
];

interface Props {
  workspaceId: string;
}

export function ConversationList({ workspaceId }: Props) {
  const [tab, setTab] = useState<ConversationStatus | "all">("open");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);

  const { conversations, setConversations, activeId, setActiveId, unreadCounts } = useConversationStore();

  useEffect(() => {
    setLoading(true);
    conversationsApi
      .list(workspaceId, { status: tab === "all" ? undefined : tab, page_size: 50 })
      .then((r) => setConversations(r.data.items ?? [], r.data.total ?? 0))
      .finally(() => setLoading(false));
  }, [workspaceId, tab]); // eslint-disable-line react-hooks/exhaustive-deps

  const filtered = conversations.filter((c) =>
    search
      ? c.contactName?.toLowerCase().includes(search.toLowerCase()) ||
        c.lastMessage?.toLowerCase().includes(search.toLowerCase())
      : true
  );

  return (
    <div className="flex h-full w-72 shrink-0 flex-col border-r border-border bg-white">
      {/* Header */}
      <div className="px-3 pt-4 pb-2">
        <h1 className="text-base font-semibold text-slate-900 mb-2">Inbox</h1>
        <Input
          placeholder="Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-8 text-xs"
        />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 px-3 pb-2">
        {TABS.map((t) => (
          <button
            key={t.status}
            onClick={() => setTab(t.status)}
            className={cn(
              "rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors",
              tab === t.status
                ? "bg-primary text-white"
                : "text-muted hover:text-slate-900"
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {loading && (
          <div className="flex items-center justify-center py-8 text-muted text-sm">Loading…</div>
        )}
        {!loading && filtered.length === 0 && (
          <div className="flex items-center justify-center py-8 text-muted text-sm">No conversations</div>
        )}
        {filtered.map((conv) => (
          <ConversationItem
            key={conv.id}
            conv={conv}
            active={conv.id === activeId}
            unread={unreadCounts[conv.id] ?? conv.unreadAgentCount}
            onClick={() => setActiveId(conv.id)}
          />
        ))}
      </div>
    </div>
  );
}

function ConversationItem({
  conv,
  active,
  unread,
  onClick,
}: {
  conv: Conversation;
  active: boolean;
  unread: number;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full flex items-start gap-2.5 px-3 py-3 text-left transition-colors hover:bg-surface-2 border-b border-border/50",
        active && "bg-blue-50"
      )}
    >
      <Avatar name={conv.contactName} size="md" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-slate-900 truncate">{conv.contactName ?? "Unknown"}</span>
          <span className="text-xs text-muted shrink-0 ml-1">
            {conv.lastMessageAt
              ? formatDistanceToNow(new Date(conv.lastMessageAt), { addSuffix: false })
              : ""}
          </span>
        </div>
        <div className="flex items-center justify-between mt-0.5">
          <p className="text-xs text-muted truncate">{conv.lastMessage ?? "No messages yet"}</p>
          {unread > 0 && (
            <span className="ml-1 shrink-0 rounded-full bg-primary px-1.5 py-0.5 text-[10px] font-bold text-white">
              {unread > 99 ? "99+" : unread}
            </span>
          )}
        </div>
        <Badge status={conv.status} className="mt-1">{conv.status}</Badge>
      </div>
    </button>
  );
}
