"use client";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { slaApi } from "@/lib/api";
import type { AgentPauseReason, AgentPresence } from "@/types/sla";
import { Modal } from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/form";
import { ChevronDown } from "lucide-react";

const STATES: { v: AgentPresence; label: string; dot: string; requiresReason?: boolean }[] = [
  { v: "online", label: "Online", dot: "bg-emerald-500" },
  { v: "away", label: "Away", dot: "bg-amber-500" },
  { v: "busy", label: "Busy", dot: "bg-rose-500" },
  { v: "in_call", label: "In call", dot: "bg-sky-500" },
  { v: "on_break", label: "On break", dot: "bg-violet-500", requiresReason: true },
  { v: "invisible", label: "Invisible", dot: "bg-slate-400" },
  { v: "offline", label: "Offline", dot: "bg-slate-500" },
];

export function PresenceDropdown() {
  const { user, currentWorkspace } = useAuthStore();
  const [current, setCurrent] = useState<AgentPresence>("offline");
  const [reasonLabel, setReasonLabel] = useState<string | null>(null);
  const [reasons, setReasons] = useState<AgentPauseReason[]>([]);
  const [open, setOpen] = useState(false);
  const [pauseOpen, setPauseOpen] = useState(false);
  const [pendingState, setPendingState] = useState<AgentPresence | null>(null);

  useEffect(() => {
    if (!currentWorkspace || !user) return;
    let mounted = true;
    Promise.all([
      slaApi.listAgentStatus(currentWorkspace.id),
      slaApi.listPauseReasons(currentWorkspace.id),
    ]).then(([statusRes, reasonsRes]) => {
      if (!mounted) return;
      setReasons(reasonsRes.data ?? []);
      const mine = (statusRes.data ?? []).find((s: { userId: string }) => s.userId === user.id);
      if (mine) {
        setCurrent(mine.status);
        setReasonLabel(mine.reasonLabel ?? null);
      }
    });
    return () => {
      mounted = false;
    };
  }, [currentWorkspace?.id, user?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!user || !currentWorkspace) return null;

  async function setState(state: AgentPresence, reasonId?: string | null, note?: string | null) {
    if (!currentWorkspace || !user) return;
    const r = await slaApi.setAgentStatus(currentWorkspace.id, user.id, {
      status: state,
      reason_id: reasonId ?? null,
      note: note ?? null,
    });
    setCurrent((r.data as { status: AgentPresence }).status);
    setReasonLabel((r.data as { reasonLabel?: string | null }).reasonLabel ?? null);
    setOpen(false);
  }

  async function handlePick(state: AgentPresence) {
    const opt = STATES.find((s) => s.v === state);
    if (opt?.requiresReason && reasons.length > 0) {
      setPendingState(state);
      setPauseOpen(true);
      setOpen(false);
    } else {
      await setState(state);
    }
  }

  const currentOpt = STATES.find((s) => s.v === current) ?? STATES[STATES.length - 1];

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 rounded-full bg-sidebar-hover px-2 py-1 text-[11px] font-medium text-white hover:bg-white/10"
      >
        <span className={`h-2 w-2 rounded-full ${currentOpt.dot}`} />
        <span>{currentOpt.label}</span>
        <ChevronDown className="h-3 w-3" />
      </button>
      {open && (
        <div className="absolute bottom-full left-0 z-40 mb-1 w-44 overflow-hidden rounded-md border border-border bg-white shadow-lg">
          {STATES.map((s) => (
            <button
              key={s.v}
              onClick={() => handlePick(s.v)}
              className={`flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm hover:bg-surface-2 ${
                s.v === current ? "bg-blue-50" : ""
              }`}
            >
              <span className={`h-2 w-2 rounded-full ${s.dot}`} />
              <span>{s.label}</span>
            </button>
          ))}
          {reasonLabel && (
            <div className="border-t border-border bg-surface-2 px-3 py-1.5 text-[11px] text-muted">
              Reason: {reasonLabel}
            </div>
          )}
        </div>
      )}

      <PauseReasonModal
        open={pauseOpen}
        reasons={reasons}
        onClose={() => {
          setPauseOpen(false);
          setPendingState(null);
        }}
        onConfirm={async (reasonId, note) => {
          if (pendingState) await setState(pendingState, reasonId, note);
          setPauseOpen(false);
          setPendingState(null);
        }}
      />
    </div>
  );
}

function PauseReasonModal({
  open,
  reasons,
  onClose,
  onConfirm,
}: {
  open: boolean;
  reasons: AgentPauseReason[];
  onClose: () => void;
  onConfirm: (reasonId: string, note: string | null) => Promise<void>;
}) {
  const [reasonId, setReasonId] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    if (!reasonId) {
      setError("Reason required");
      return;
    }
    setLoading(true);
    try {
      await onConfirm(reasonId, note || null);
      setReasonId("");
      setNote("");
      setError("");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Why are you pausing?">
      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1.5">
          <Label>Reason *</Label>
          <select
            value={reasonId}
            onChange={(e) => setReasonId(e.target.value)}
            className="h-9 rounded-md border border-border bg-white px-2 text-sm"
          >
            <option value="">Pick reason…</option>
            {reasons
              .filter((r) => r.active)
              .map((r) => (
                <option key={r.id} value={r.id}>
                  {r.label}
                </option>
              ))}
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Note</Label>
          <Input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Optional context" />
        </div>
        {error && <p className="text-sm text-danger">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button variant="outline" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={submit} loading={loading}>
            Pause
          </Button>
        </div>
      </div>
    </Modal>
  );
}
