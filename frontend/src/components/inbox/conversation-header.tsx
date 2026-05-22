"use client";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { Input, Label, Textarea } from "@/components/ui/form";
import {
  conversationsApi,
  macrosApi,
  sectorsApi,
  serviceReasonsApi,
  snoozeApi,
  transferReasonsApi,
  workspacesApi,
} from "@/lib/api";
import { useConversationStore } from "@/stores/conversation-store";
import type { Conversation, Macro, ServiceReason, TransferReason, WorkspaceMember } from "@/types/conversation";
import {
  AlarmClockOff,
  ArrowRightLeft,
  BellOff,
  CheckCheck,
  ChevronDown,
  Lock,
  RotateCw,
  Wand2,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface Props {
  workspaceId: string;
  conversation: Conversation;
}

export function ConversationHeader({ workspaceId, conversation }: Props) {
  const { upsertConversation } = useConversationStore();
  const [resolving, setResolving] = useState(false);
  const [snoozeOpen, setSnoozeOpen] = useState(false);
  const [resolveOpen, setResolveOpen] = useState(false);
  const [reopenOpen, setReopenOpen] = useState(false);
  const [transferOpen, setTransferOpen] = useState(false);
  const [macros, setMacros] = useState<Macro[]>([]);
  const [macroMenuOpen, setMacroMenuOpen] = useState(false);
  const [runningMacroId, setRunningMacroId] = useState<string | null>(null);

  useEffect(() => {
    macrosApi.list(workspaceId).then((r) => setMacros(r.data ?? []));
  }, [workspaceId]);

  async function setStatus(status: string, extra?: Record<string, unknown>) {
    const r = await conversationsApi.update(workspaceId, conversation.id, { status, ...(extra ?? {}) });
    upsertConversation(r.data as Conversation);
  }

  async function clearSnooze() {
    await snoozeApi.clear(workspaceId, conversation.id);
    upsertConversation({ ...conversation, snoozedUntil: null });
  }

  async function togglePrivate() {
    const r = await conversationsApi.update(workspaceId, conversation.id, {
      is_private: !conversation.isPrivate,
    });
    upsertConversation(r.data as Conversation);
  }

  async function runMacro(macroId: string) {
    setRunningMacroId(macroId);
    setMacroMenuOpen(false);
    try {
      await macrosApi.run(workspaceId, macroId, conversation.id);
      // refresh conversation
      const r = await conversationsApi.get(workspaceId, conversation.id);
      upsertConversation(r.data as Conversation);
    } finally {
      setRunningMacroId(null);
    }
  }

  const isResolved = conversation.status === "resolved";
  const displayName = conversation.contactName ?? conversation.contactPhone ?? "Unknown";
  const snoozedUntil = conversation.snoozedUntil ? new Date(conversation.snoozedUntil) : null;
  const snoozedActive = snoozedUntil && snoozedUntil > new Date();

  return (
    <div className="shrink-0 border-b border-border bg-white px-4 py-2.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-900">{displayName}</span>
          <Badge status={conversation.status}>{conversation.status}</Badge>
          {conversation.slaStatus && conversation.slaStatus !== "ok" && (
            <Badge status={conversation.slaStatus}>SLA {conversation.slaStatus}</Badge>
          )}
          {conversation.isPrivate && (
            <span className="inline-flex items-center gap-1 rounded-full bg-purple-100 px-2 py-0.5 text-[10px] font-semibold uppercase text-purple-700">
              <Lock className="h-3 w-3" /> Private
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <div className="relative">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setMacroMenuOpen((o) => !o)}
              disabled={macros.length === 0}
              loading={runningMacroId !== null}
            >
              <Wand2 className="h-3.5 w-3.5" /> Macro <ChevronDown className="h-3 w-3" />
            </Button>
            {macroMenuOpen && macros.length > 0 && (
              <div className="absolute right-0 top-full z-30 mt-1 max-h-64 w-64 overflow-y-auto rounded-md border border-border bg-white shadow-lg">
                {macros.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => runMacro(m.id)}
                    className="block w-full px-3 py-2 text-left text-sm hover:bg-surface-2"
                  >
                    <div className="font-medium text-slate-900">{m.name}</div>
                    {m.description && <div className="text-[11px] text-muted">{m.description}</div>}
                  </button>
                ))}
              </div>
            )}
          </div>
          <Button variant="outline" size="sm" onClick={() => setTransferOpen(true)}>
            <ArrowRightLeft className="h-3.5 w-3.5" /> Transfer
          </Button>
          <Button variant="outline" size="sm" onClick={() => setSnoozeOpen(true)}>
            <BellOff className="h-3.5 w-3.5" /> Snooze
          </Button>
          <Button variant="outline" size="sm" onClick={togglePrivate}>
            <Lock className="h-3.5 w-3.5" />
            {conversation.isPrivate ? "Unmark" : "Private"}
          </Button>
          {isResolved ? (
            <Button variant="outline" size="sm" onClick={() => setReopenOpen(true)}>
              <RotateCw className="h-3.5 w-3.5" /> Reopen
            </Button>
          ) : (
            <Button size="sm" loading={resolving} onClick={() => setResolveOpen(true)}>
              <CheckCheck className="h-3.5 w-3.5" /> Resolve
            </Button>
          )}
        </div>
      </div>

      {snoozedActive && (
        <div className="mt-2 flex items-center justify-between rounded-md bg-amber-50 px-3 py-1.5 text-xs text-amber-800">
          <span>
            Snoozed — wakes {formatDistanceToNow(snoozedUntil, { addSuffix: true })}
            {conversation.snoozedUntil && (
              <> ({new Date(conversation.snoozedUntil).toLocaleString()})</>
            )}
          </span>
          <button onClick={clearSnooze} className="font-medium text-amber-900 hover:underline">
            <AlarmClockOff className="inline h-3 w-3" /> Unsnooze
          </button>
        </div>
      )}

      <SnoozeModal
        open={snoozeOpen}
        onClose={() => setSnoozeOpen(false)}
        workspaceId={workspaceId}
        conversationId={conversation.id}
        onSnoozed={(until) => upsertConversation({ ...conversation, snoozedUntil: until })}
      />
      <ResolveModal
        open={resolveOpen}
        onClose={() => setResolveOpen(false)}
        workspaceId={workspaceId}
        onConfirm={async (payload) => {
          setResolving(true);
          try {
            await setStatus("resolved", payload);
          } finally {
            setResolving(false);
            setResolveOpen(false);
          }
        }}
      />
      <ReopenModal
        open={reopenOpen}
        onClose={() => setReopenOpen(false)}
        onConfirm={async (note) => {
          await setStatus("open", { resolve_note: note || null });
          setReopenOpen(false);
        }}
      />
      <TransferModal
        open={transferOpen}
        onClose={() => setTransferOpen(false)}
        workspaceId={workspaceId}
        conversation={conversation}
        onTransferred={(updated) => {
          upsertConversation(updated);
          setTransferOpen(false);
        }}
      />
    </div>
  );
}

function TransferModal({
  open,
  onClose,
  workspaceId,
  conversation,
  onTransferred,
}: {
  open: boolean;
  onClose: () => void;
  workspaceId: string;
  conversation: Conversation;
  onTransferred: (c: Conversation) => void;
}) {
  const [reasons, setReasons] = useState<TransferReason[]>([]);
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [sectors, setSectors] = useState<{ id: string; name: string }[]>([]);
  const [assigneeId, setAssigneeId] = useState("");
  const [sectorId, setSectorId] = useState("");
  const [reasonId, setReasonId] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const hasRequired = reasons.some((r) => r.required && r.active);

  useEffect(() => {
    if (!open) return;
    transferReasonsApi.list(workspaceId, { active: true }).then((r) => setReasons(r.data ?? []));
    workspacesApi.listMembers(workspaceId).then((r) => setMembers(r.data ?? []));
    sectorsApi.list(workspaceId).then((r) => setSectors(r.data ?? []));
    setAssigneeId(conversation.assigneeId ?? "");
    setSectorId(conversation.sectorId ?? "");
  }, [open, workspaceId, conversation.assigneeId, conversation.sectorId]);

  async function submit() {
    if (hasRequired && !reasonId) {
      setError("This workspace requires a transfer reason");
      return;
    }
    if (!assigneeId && !sectorId) {
      setError("Pick at least an agent or a sector");
      return;
    }
    setLoading(true);
    try {
      const r = await conversationsApi.transfer(workspaceId, conversation.id, {
        assignee_id: assigneeId || undefined,
        sector_id: sectorId || undefined,
        note: note || undefined,
        transfer_reason_id: reasonId || undefined,
      });
      onTransferred(r.data as Conversation);
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(detail ?? "Failed to transfer");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Transfer conversation">
      <div className="flex flex-col gap-3">
        <div className="grid grid-cols-2 gap-2">
          <div className="flex flex-col gap-1.5">
            <Label>Agent</Label>
            <select
              value={assigneeId}
              onChange={(e) => setAssigneeId(e.target.value)}
              className="h-9 rounded-md border border-border bg-white px-2 text-sm"
            >
              <option value="">No agent</option>
              {members.map((m) => (
                <option key={m.userId} value={m.userId}>
                  {m.user?.name ?? m.userId}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Sector</Label>
            <select
              value={sectorId}
              onChange={(e) => setSectorId(e.target.value)}
              className="h-9 rounded-md border border-border bg-white px-2 text-sm"
            >
              <option value="">No sector</option>
              {sectors.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        {reasons.length > 0 && (
          <div className="flex flex-col gap-1.5">
            <Label>Reason{hasRequired && " *"}</Label>
            <select
              value={reasonId}
              onChange={(e) => setReasonId(e.target.value)}
              className="h-9 rounded-md border border-border bg-white px-2 text-sm"
            >
              <option value="">Pick reason…</option>
              {reasons.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="flex flex-col gap-1.5">
          <Label>Note</Label>
          <Textarea rows={2} value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
        {error && <p className="text-sm text-danger">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button variant="outline" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={submit} loading={loading}>
            Transfer
          </Button>
        </div>
      </div>
    </Modal>
  );
}

function SnoozeModal({
  open,
  onClose,
  workspaceId,
  conversationId,
  onSnoozed,
}: {
  open: boolean;
  onClose: () => void;
  workspaceId: string;
  conversationId: string;
  onSnoozed: (until: string) => void;
}) {
  const [preset, setPreset] = useState<string>("4h");
  const [customUntil, setCustomUntil] = useState("");
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);

  function computeUntil(): Date | null {
    if (preset === "custom") {
      return customUntil ? new Date(customUntil) : null;
    }
    const now = new Date();
    if (preset === "1h") now.setHours(now.getHours() + 1);
    else if (preset === "4h") now.setHours(now.getHours() + 4);
    else if (preset === "tomorrow") {
      now.setDate(now.getDate() + 1);
      now.setHours(9, 0, 0, 0);
    } else if (preset === "next_week") {
      now.setDate(now.getDate() + 7);
      now.setHours(9, 0, 0, 0);
    }
    return now;
  }

  async function submit() {
    const until = computeUntil();
    if (!until || until <= new Date()) return;
    setLoading(true);
    try {
      await snoozeApi.set(workspaceId, conversationId, until.toISOString(), reason || undefined);
      onSnoozed(until.toISOString());
      onClose();
      setReason("");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Snooze conversation">
      <div className="flex flex-col gap-3">
        <div className="grid grid-cols-2 gap-2">
          {[
            { v: "1h", label: "1 hour" },
            { v: "4h", label: "4 hours" },
            { v: "tomorrow", label: "Tomorrow 9am" },
            { v: "next_week", label: "Next week" },
            { v: "custom", label: "Custom…" },
          ].map((opt) => (
            <button
              key={opt.v}
              onClick={() => setPreset(opt.v)}
              className={`rounded-md border px-3 py-2 text-sm ${
                preset === opt.v ? "border-primary text-primary" : "border-border text-slate-700 hover:bg-surface-2"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
        {preset === "custom" && (
          <Input
            type="datetime-local"
            value={customUntil}
            onChange={(e) => setCustomUntil(e.target.value)}
          />
        )}
        <Input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Reason (optional)" />
        <div className="flex justify-end gap-2">
          <Button variant="outline" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={submit} loading={loading}>
            Snooze
          </Button>
        </div>
      </div>
    </Modal>
  );
}

function ResolveModal({
  open,
  onClose,
  workspaceId,
  onConfirm,
}: {
  open: boolean;
  onClose: () => void;
  workspaceId: string;
  onConfirm: (payload: Record<string, unknown>) => Promise<void>;
}) {
  const [reasons, setReasons] = useState<ServiceReason[]>([]);
  const [reasonId, setReasonId] = useState("");
  const [note, setNote] = useState("");

  useEffect(() => {
    if (!open) return;
    serviceReasonsApi.list(workspaceId, { active: true }).then((r) => setReasons(r.data ?? []));
  }, [open, workspaceId]);

  function submit() {
    onConfirm({ service_reason_id: reasonId || null, resolve_note: note || null });
  }

  return (
    <Modal open={open} onClose={onClose} title="Resolve conversation">
      <div className="flex flex-col gap-3">
        {reasons.length > 0 && (
          <div className="flex flex-col gap-1.5">
            <Label>Service reason</Label>
            <select
              value={reasonId}
              onChange={(e) => setReasonId(e.target.value)}
              className="h-9 rounded-md border border-border bg-white px-2 text-sm"
            >
              <option value="">Pick reason…</option>
              {reasons.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="flex flex-col gap-1.5">
          <Label>Note</Label>
          <Textarea
            rows={3}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Optional note about the resolution"
          />
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="outline" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={submit}>Resolve</Button>
        </div>
      </div>
    </Modal>
  );
}

function ReopenModal({
  open,
  onClose,
  onConfirm,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: (note: string) => Promise<void>;
}) {
  const [note, setNote] = useState("");
  return (
    <Modal open={open} onClose={onClose} title="Reopen conversation">
      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1.5">
          <Label>Why are you reopening?</Label>
          <Textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} placeholder="Optional" />
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="outline" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={() => onConfirm(note)}>Reopen</Button>
        </div>
      </div>
    </Modal>
  );
}
