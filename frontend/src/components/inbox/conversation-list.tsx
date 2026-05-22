"use client";
import { useEffect, useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { Input } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { conversationsApi, labelsApi, viewsApi } from "@/lib/api";
import { useConversationStore } from "@/stores/conversation-store";
import type { Conversation, ConversationStatus, ConversationView, Label } from "@/types/conversation";
import { formatDistanceToNow } from "date-fns";
import { AtSign, BellOff, Check, CheckSquare, Square, Star } from "lucide-react";

const TABS: { label: string; status: ConversationStatus | "all" }[] = [
  { label: "Open", status: "open" },
  { label: "Active", status: "in_progress" },
  { label: "Pending", status: "pending" },
  { label: "Resolved", status: "resolved" },
];

type SpecialView = "mentions" | "snoozed" | null;

interface Props {
  workspaceId: string;
}

interface SelectionContextValue {
  selectionMode: boolean;
  setSelectionMode: (next: boolean) => void;
  selected: Set<string>;
  toggle: (id: string) => void;
  clear: () => void;
}

export function ConversationList({ workspaceId }: Props) {
  const [tab, setTab] = useState<ConversationStatus | "all">("open");
  const [search, setSearch] = useState("");
  const [labelFilter, setLabelFilter] = useState<string>("");
  const [special, setSpecial] = useState<SpecialView>(null);
  const [viewId, setViewId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [labels, setLabels] = useState<Label[]>([]);
  const [views, setViews] = useState<ConversationView[]>([]);
  const [selectionMode, setSelectionMode] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const { conversations, setConversations, activeId, setActiveId, unreadCounts } = useConversationStore();

  useEffect(() => {
    setLoading(true);
    const params: Record<string, unknown> = {
      label_id: labelFilter || undefined,
      page_size: 50,
    };
    if (viewId) {
      params.view_id = viewId;
    } else {
      params.status = tab === "all" ? undefined : tab;
      if (special === "mentions") params.mentions_for_me = true;
      else if (special === "snoozed") params.snoozed = true;
      if (search.trim()) params.search = search.trim();
    }
    conversationsApi
      .list(workspaceId, params)
      .then((r) => setConversations(r.data.items ?? [], r.data.total ?? 0))
      .finally(() => setLoading(false));
  }, [workspaceId, tab, labelFilter, special, viewId, search]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    labelsApi.list(workspaceId).then((r) => setLabels(r.data ?? []));
    viewsApi.list(workspaceId).then((r) => setViews(r.data ?? []));
  }, [workspaceId]);

  const filtered = conversations.filter((c) =>
    search
      ? c.contactName?.toLowerCase().includes(search.toLowerCase()) ||
        c.contactPhone?.toLowerCase().includes(search.toLowerCase()) ||
        c.lastMessage?.toLowerCase().includes(search.toLowerCase())
      : true,
  );

  const selection: SelectionContextValue = {
    selectionMode,
    setSelectionMode,
    selected,
    toggle: (id) =>
      setSelected((prev) => {
        const next = new Set(prev);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        return next;
      }),
    clear: () => setSelected(new Set()),
  };

  return (
    <div className="flex h-full w-72 shrink-0 flex-col border-r border-border bg-white">
      <div className="px-3 pt-4 pb-2">
        <div className="mb-2 flex items-center justify-between">
          <h1 className="text-base font-semibold text-slate-900">Inbox</h1>
          <button
            onClick={() => {
              const next = !selectionMode;
              setSelectionMode(next);
              if (!next) setSelected(new Set());
            }}
            className={cn(
              "text-[11px] font-medium",
              selectionMode ? "text-primary" : "text-muted hover:text-slate-900",
            )}
          >
            {selectionMode ? "Done" : "Select"}
          </button>
        </div>
        <Input
          placeholder="Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-8 text-xs"
        />
      </div>

      <div className="flex flex-wrap gap-1 px-3 pb-2">
        {TABS.map((t) => (
          <button
            key={t.status}
            onClick={() => {
              setTab(t.status);
              setSpecial(null);
              setViewId("");
            }}
            className={cn(
              "rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors",
              tab === t.status && !special && !viewId
                ? "bg-primary text-white"
                : "text-muted hover:text-slate-900",
            )}
          >
            {t.label}
          </button>
        ))}
        <button
          onClick={() => {
            setSpecial(special === "mentions" ? null : "mentions");
            setViewId("");
          }}
          className={cn(
            "flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors",
            special === "mentions" ? "bg-primary text-white" : "text-muted hover:text-slate-900",
          )}
        >
          <AtSign className="h-3 w-3" /> @me
        </button>
        <button
          onClick={() => {
            setSpecial(special === "snoozed" ? null : "snoozed");
            setViewId("");
          }}
          className={cn(
            "flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors",
            special === "snoozed" ? "bg-primary text-white" : "text-muted hover:text-slate-900",
          )}
        >
          <BellOff className="h-3 w-3" /> Snoozed
        </button>
      </div>
      {views.length > 0 && (
        <div className="flex flex-wrap items-center gap-1 px-3 pb-2">
          {views.map((v) => (
            <button
              key={v.id}
              onClick={() => {
                setViewId(viewId === v.id ? "" : v.id);
                setSpecial(null);
              }}
              className={cn(
                "flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium",
                viewId === v.id
                  ? "border-slate-900 text-slate-900"
                  : "border-border text-muted hover:text-slate-700",
              )}
            >
              {v.pinned && <Star className="h-3 w-3" />}
              {v.name}
            </button>
          ))}
        </div>
      )}

      {labels.length > 0 && (
        <div className="flex flex-wrap items-center gap-1 px-3 pb-2">
          <button
            onClick={() => setLabelFilter("")}
            className={cn(
              "rounded-full border px-2 py-0.5 text-[11px] font-medium transition-colors",
              !labelFilter ? "border-primary text-primary" : "border-border text-muted hover:text-slate-700",
            )}
          >
            All labels
          </button>
          {labels.map((l) => (
            <button
              key={l.id}
              onClick={() => setLabelFilter(labelFilter === l.id ? "" : l.id)}
              className={cn(
                "flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium transition-colors",
                labelFilter === l.id
                  ? "border-slate-900 text-slate-900"
                  : "border-border text-muted hover:text-slate-700",
              )}
            >
              <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: l.color }} />
              {l.name}
            </button>
          ))}
        </div>
      )}

      {selectionMode && (
        <BulkActionsBar
          workspaceId={workspaceId}
          labels={labels}
          selected={selected}
          onDone={() => {
            setSelected(new Set());
            conversationsApi
              .list(workspaceId, {
                status: tab === "all" ? undefined : tab,
                label_id: labelFilter || undefined,
                page_size: 50,
              })
              .then((r) => setConversations(r.data.items ?? [], r.data.total ?? 0));
          }}
        />
      )}

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
            selection={selection}
            onClick={() => {
              if (selection.selectionMode) {
                selection.toggle(conv.id);
              } else {
                setActiveId(conv.id);
              }
            }}
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
  selection,
  onClick,
}: {
  conv: Conversation;
  active: boolean;
  unread: number;
  selection: SelectionContextValue;
  onClick: () => void;
}) {
  const displayName = conv.contactName ?? conv.contactPhone ?? "Unknown";
  const isChecked = selection.selected.has(conv.id);

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full flex items-start gap-2.5 px-3 py-3 text-left transition-colors hover:bg-surface-2 border-b border-border/50",
        active && !selection.selectionMode && "bg-blue-50",
        isChecked && "bg-blue-50/70",
      )}
    >
      {selection.selectionMode ? (
        isChecked ? (
          <CheckSquare className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
        ) : (
          <Square className="mt-0.5 h-5 w-5 shrink-0 text-muted" />
        )
      ) : (
        <Avatar name={displayName} size="md" />
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-slate-900 truncate">{displayName}</span>
          <span className="text-xs text-muted shrink-0 ml-1">
            {conv.lastMessageAt
              ? formatDistanceToNow(new Date(conv.lastMessageAt), { addSuffix: false })
              : ""}
          </span>
        </div>
        <div className="flex items-center justify-between mt-0.5">
          <p className="text-xs text-muted truncate">{conv.lastMessage ?? conv.contactPhone ?? "No messages yet"}</p>
          {unread > 0 && (
            <span className="ml-1 shrink-0 rounded-full bg-primary px-1.5 py-0.5 text-[10px] font-bold text-white">
              {unread > 99 ? "99+" : unread}
            </span>
          )}
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-1">
          <Badge status={conv.status}>{conv.status}</Badge>
          {(conv.labels ?? []).map((label) => (
            <span
              key={label.id}
              className="inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-medium"
              style={{ backgroundColor: `${label.color}1a`, color: label.color }}
            >
              <span className="inline-block h-1.5 w-1.5 rounded-full" style={{ backgroundColor: label.color }} />
              {label.name}
            </span>
          ))}
          {conv.assigneeName && (
            <span className="text-[10px] text-muted">· {conv.assigneeName}</span>
          )}
        </div>
      </div>
    </button>
  );
}

function BulkActionsBar({
  workspaceId,
  labels,
  selected,
  onDone,
}: {
  workspaceId: string;
  labels: Label[];
  selected: Set<string>;
  onDone: () => void;
}) {
  const [labelId, setLabelId] = useState("");
  const [status, setStatus] = useState<ConversationStatus | "">("");
  const [assigneeId, setAssigneeId] = useState("");
  const [members, setMembers] = useState<{ userId: string; user?: { name: string } | null }[]>([]);
  const [working, setWorking] = useState(false);

  const ids = useMemo(() => Array.from(selected), [selected]);
  const disabled = working || ids.length === 0;

  useEffect(() => {
    import("@/lib/api").then(({ workspacesApi }) =>
      workspacesApi.listMembers(workspaceId).then((r) => setMembers(r.data ?? [])),
    );
  }, [workspaceId]);

  async function applyLabel() {
    if (!labelId || ids.length === 0) return;
    setWorking(true);
    try {
      await conversationsApi.bulkLabel(workspaceId, { conversation_ids: ids, label_id: labelId });
      onDone();
    } finally {
      setWorking(false);
    }
  }

  async function applyStatus() {
    if (!status || ids.length === 0) return;
    setWorking(true);
    try {
      await conversationsApi.bulkStatus(workspaceId, { conversation_ids: ids, status });
      onDone();
    } finally {
      setWorking(false);
    }
  }

  async function applyAssign() {
    if (!assigneeId || ids.length === 0) return;
    setWorking(true);
    try {
      await conversationsApi.bulkAssign(workspaceId, { conversation_ids: ids, assignee_id: assigneeId });
      onDone();
    } finally {
      setWorking(false);
    }
  }

  return (
    <div className="border-y border-border bg-amber-50 px-3 py-2">
      <div className="mb-1 text-[11px] text-amber-800">{ids.length} selected</div>
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center gap-1">
          <select
            value={labelId}
            onChange={(e) => setLabelId(e.target.value)}
            className="h-7 flex-1 rounded-md border border-border bg-white px-1 text-xs"
          >
            <option value="">Label…</option>
            {labels.map((l) => (
              <option key={l.id} value={l.id}>
                {l.name}
              </option>
            ))}
          </select>
          <Button size="sm" onClick={applyLabel} disabled={disabled || !labelId}>
            <Check className="h-3.5 w-3.5" />
          </Button>
        </div>
        <div className="flex items-center gap-1">
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as ConversationStatus)}
            className="h-7 flex-1 rounded-md border border-border bg-white px-1 text-xs"
          >
            <option value="">Set status…</option>
            <option value="open">Open</option>
            <option value="in_progress">In progress</option>
            <option value="pending">Pending</option>
            <option value="resolved">Resolved</option>
          </select>
          <Button size="sm" onClick={applyStatus} disabled={disabled || !status}>
            <Check className="h-3.5 w-3.5" />
          </Button>
        </div>
        <div className="flex items-center gap-1">
          <select
            value={assigneeId}
            onChange={(e) => setAssigneeId(e.target.value)}
            className="h-7 flex-1 rounded-md border border-border bg-white px-1 text-xs"
          >
            <option value="">Assign to…</option>
            {members.map((m) => (
              <option key={m.userId} value={m.userId}>
                {m.user?.name ?? m.userId}
              </option>
            ))}
          </select>
          <Button size="sm" onClick={applyAssign} disabled={disabled || !assigneeId}>
            <Check className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </div>
  );
}
