"use client";
import { useEffect, useMemo, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { cannedResponsesApi, labelsApi, macrosApi, sectorsApi, workspacesApi } from "@/lib/api";
import type {
  CannedResponse,
  CannedVisibility,
  Label as LabelType,
  Macro,
  MacroAction,
  MacroActionType,
  WorkspaceMember,
} from "@/types/conversation";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { Input, Label as FormLabel, Textarea } from "@/components/ui/form";
import { ChevronDown, ChevronUp, Pencil, Plus, Trash2 } from "lucide-react";

const ACTION_LABELS: Record<MacroActionType, string> = {
  send_message: "Send message",
  send_canned: "Send canned response",
  apply_label: "Apply label",
  remove_label: "Remove label",
  transfer: "Transfer",
  assign: "Assign agent",
  add_note: "Add internal note",
  set_status: "Set status",
  set_priority: "Set priority",
  add_participant: "Add participant",
};

const ACTION_TYPES: MacroActionType[] = Object.keys(ACTION_LABELS) as MacroActionType[];

export function MacrosTab() {
  const { currentWorkspace } = useAuthStore();
  const [items, setItems] = useState<Macro[]>([]);
  const [editing, setEditing] = useState<Macro | null>(null);
  const [createOpen, setCreateOpen] = useState(false);

  useEffect(() => {
    if (!currentWorkspace) return;
    macrosApi.list(currentWorkspace.id).then((r) => setItems(r.data ?? []));
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function remove(id: string) {
    if (!currentWorkspace) return;
    if (!confirm("Delete this macro?")) return;
    await macrosApi.delete(currentWorkspace.id, id);
    setItems((prev) => prev.filter((m) => m.id !== id));
  }

  return (
    <div className="max-w-3xl">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-slate-900">Macros</h2>
          <p className="text-sm text-muted">Chain multiple conversation actions and trigger them with one click.</p>
        </div>
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus className="h-3.5 w-3.5" /> New macro
        </Button>
      </div>

      <div className="flex flex-col gap-2">
        {items.map((m) => (
          <div key={m.id} className="rounded-lg border border-border bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <p className="font-medium text-slate-900">{m.name}</p>
                  <span className="rounded-full bg-surface-3 px-2 py-0.5 text-[10px] font-semibold uppercase text-muted">
                    {m.visibility}
                  </span>
                  {!m.active && (
                    <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-700">
                      inactive
                    </span>
                  )}
                </div>
                {m.description && <p className="mt-1 text-xs text-muted">{m.description}</p>}
                <div className="mt-2 flex flex-wrap gap-1">
                  {m.actions.map((a) => (
                    <span key={a.position} className="rounded-full bg-blue-50 px-2 py-0.5 text-[11px] text-blue-700">
                      {ACTION_LABELS[a.actionType]}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button className="text-muted hover:text-slate-900" onClick={() => setEditing(m)} aria-label="Edit">
                  <Pencil className="h-4 w-4" />
                </button>
                <button className="text-muted hover:text-danger" onClick={() => remove(m.id)} aria-label="Delete">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
        {items.length === 0 && (
          <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted">
            No macros yet.
          </div>
        )}
      </div>

      <MacroFormModal
        key={editing?.id ?? "new"}
        open={createOpen || editing !== null}
        initial={editing}
        workspaceId={currentWorkspace?.id ?? ""}
        onClose={() => {
          setCreateOpen(false);
          setEditing(null);
        }}
        onSaved={(saved) =>
          setItems((prev) => {
            const idx = prev.findIndex((p) => p.id === saved.id);
            if (idx === -1) return [...prev, saved];
            const copy = prev.slice();
            copy[idx] = saved;
            return copy;
          })
        }
      />
    </div>
  );
}

function MacroFormModal({
  open,
  onClose,
  workspaceId,
  initial,
  onSaved,
}: {
  open: boolean;
  onClose: () => void;
  workspaceId: string;
  initial: Macro | null;
  onSaved: (m: Macro) => void;
}) {
  const [name, setName] = useState(initial?.name ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [visibility, setVisibility] = useState<CannedVisibility>(initial?.visibility ?? "workspace");
  const [sectorId, setSectorId] = useState(initial?.sectorId ?? "");
  const [active, setActive] = useState(initial?.active ?? true);
  const [actions, setActions] = useState<MacroAction[]>(initial?.actions ?? []);

  const [labels, setLabels] = useState<LabelType[]>([]);
  const [canneds, setCanneds] = useState<CannedResponse[]>([]);
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [sectors, setSectors] = useState<{ id: string; name: string }[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open || !workspaceId) return;
    labelsApi.list(workspaceId).then((r) => setLabels(r.data ?? []));
    cannedResponsesApi.list(workspaceId).then((r) => setCanneds(r.data ?? []));
    workspacesApi.listMembers(workspaceId).then((r) => setMembers(r.data ?? []));
    sectorsApi.list(workspaceId).then((r) => setSectors(r.data ?? []));
  }, [open, workspaceId]);

  function addAction() {
    setActions((prev) => [
      ...prev,
      { actionType: "send_message", params: {}, position: prev.length },
    ]);
  }

  function updateAction(idx: number, patch: Partial<MacroAction>) {
    setActions((prev) => {
      const copy = prev.slice();
      copy[idx] = { ...copy[idx], ...patch };
      return copy;
    });
  }

  function move(idx: number, direction: -1 | 1) {
    setActions((prev) => {
      const target = idx + direction;
      if (target < 0 || target >= prev.length) return prev;
      const copy = prev.slice();
      const [removed] = copy.splice(idx, 1);
      copy.splice(target, 0, removed);
      return copy.map((a, i) => ({ ...a, position: i }));
    });
  }

  function removeAction(idx: number) {
    setActions((prev) => prev.filter((_, i) => i !== idx).map((a, i) => ({ ...a, position: i })));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      setError("Name required");
      return;
    }
    if (actions.length === 0) {
      setError("Macro needs at least one action");
      return;
    }
    setLoading(true);
    try {
      const payload = {
        name,
        description: description || null,
        visibility,
        sector_id: visibility === "sector" && sectorId ? sectorId : null,
        active,
        actions: actions.map((a, i) => ({ action_type: a.actionType, params: a.params, position: i })),
      };
      const r = initial
        ? await macrosApi.update(workspaceId, initial.id, payload)
        : await macrosApi.create(workspaceId, payload);
      onSaved(r.data as Macro);
      onClose();
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(detail ?? "Failed to save");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={initial ? "Edit macro" : "New macro"} size="lg">
      <form onSubmit={submit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <FormLabel>Name *</FormLabel>
          <Input value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="flex flex-col gap-1.5">
          <FormLabel>Description</FormLabel>
          <Textarea rows={2} value={description ?? ""} onChange={(e) => setDescription(e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <FormLabel>Visibility</FormLabel>
            <select
              value={visibility}
              onChange={(e) => setVisibility(e.target.value as CannedVisibility)}
              className="h-9 rounded-md border border-border bg-white px-2 text-sm"
            >
              <option value="workspace">Workspace (all)</option>
              <option value="sector">Sector</option>
              <option value="user">Personal</option>
            </select>
          </div>
          {visibility === "sector" && (
            <div className="flex flex-col gap-1.5">
              <FormLabel>Sector</FormLabel>
              <select
                value={sectorId ?? ""}
                onChange={(e) => setSectorId(e.target.value)}
                className="h-9 rounded-md border border-border bg-white px-2 text-sm"
              >
                <option value="">Select sector…</option>
                {sectors.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <FormLabel>Actions *</FormLabel>
            <Button type="button" variant="outline" size="sm" onClick={addAction}>
              <Plus className="h-3.5 w-3.5" /> Add action
            </Button>
          </div>
          <div className="flex flex-col gap-2">
            {actions.map((action, idx) => (
              <ActionRow
                key={idx}
                action={action}
                idx={idx}
                total={actions.length}
                labels={labels}
                canneds={canneds}
                members={members}
                sectors={sectors}
                onChange={(patch) => updateAction(idx, patch)}
                onMoveUp={() => move(idx, -1)}
                onMoveDown={() => move(idx, 1)}
                onRemove={() => removeAction(idx)}
              />
            ))}
            {actions.length === 0 && (
              <div className="rounded-lg border border-dashed border-border p-4 text-center text-sm text-muted">
                No actions yet.
              </div>
            )}
          </div>
        </div>

        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} />
          <span>Active</span>
        </label>

        {error && <p className="text-sm text-danger">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button variant="outline" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={loading}>
            {initial ? "Save" : "Create"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function ActionRow({
  action,
  idx,
  total,
  labels,
  canneds,
  members,
  sectors,
  onChange,
  onMoveUp,
  onMoveDown,
  onRemove,
}: {
  action: MacroAction;
  idx: number;
  total: number;
  labels: LabelType[];
  canneds: CannedResponse[];
  members: WorkspaceMember[];
  sectors: { id: string; name: string }[];
  onChange: (patch: Partial<MacroAction>) => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onRemove: () => void;
}) {
  const params = action.params as Record<string, string>;

  return (
    <div className="rounded-lg border border-border bg-surface-2 p-3">
      <div className="mb-2 flex items-center gap-2">
        <span className="font-mono text-xs text-muted">#{idx + 1}</span>
        <select
          value={action.actionType}
          onChange={(e) => onChange({ actionType: e.target.value as MacroActionType, params: {} })}
          className="h-8 rounded-md border border-border bg-white px-2 text-xs"
        >
          {ACTION_TYPES.map((t) => (
            <option key={t} value={t}>
              {ACTION_LABELS[t]}
            </option>
          ))}
        </select>
        <div className="ml-auto flex items-center gap-1">
          <button type="button" disabled={idx === 0} onClick={onMoveUp} className="text-muted disabled:opacity-30">
            <ChevronUp className="h-4 w-4" />
          </button>
          <button
            type="button"
            disabled={idx === total - 1}
            onClick={onMoveDown}
            className="text-muted disabled:opacity-30"
          >
            <ChevronDown className="h-4 w-4" />
          </button>
          <button type="button" onClick={onRemove} className="text-muted hover:text-danger">
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
      <ActionParams action={action} labels={labels} canneds={canneds} members={members} sectors={sectors} onChange={onChange} />
    </div>
  );
}

function ActionParams({
  action,
  labels,
  canneds,
  members,
  sectors,
  onChange,
}: {
  action: MacroAction;
  labels: LabelType[];
  canneds: CannedResponse[];
  members: WorkspaceMember[];
  sectors: { id: string; name: string }[];
  onChange: (patch: Partial<MacroAction>) => void;
}) {
  const params = action.params as Record<string, string>;
  function set(key: string, value: string) {
    onChange({ params: { ...params, [key]: value } });
  }

  switch (action.actionType) {
    case "send_message":
    case "add_note":
      return (
        <Textarea
          rows={2}
          value={params.content ?? ""}
          onChange={(e) => set("content", e.target.value)}
          placeholder="Message content"
        />
      );
    case "send_canned":
      return (
        <select
          value={params.canned_response_id ?? ""}
          onChange={(e) => set("canned_response_id", e.target.value)}
          className="h-8 w-full rounded-md border border-border bg-white px-2 text-sm"
        >
          <option value="">Pick canned response…</option>
          {canneds.map((c) => (
            <option key={c.id} value={c.id}>
              /{c.shortcut} — {c.title}
            </option>
          ))}
        </select>
      );
    case "apply_label":
    case "remove_label":
      return (
        <select
          value={params.label_id ?? ""}
          onChange={(e) => set("label_id", e.target.value)}
          className="h-8 w-full rounded-md border border-border bg-white px-2 text-sm"
        >
          <option value="">Pick label…</option>
          {labels.map((l) => (
            <option key={l.id} value={l.id}>
              {l.name}
            </option>
          ))}
        </select>
      );
    case "transfer": {
      return (
        <div className="grid grid-cols-2 gap-2">
          <select
            value={params.assignee_id ?? ""}
            onChange={(e) => set("assignee_id", e.target.value)}
            className="h-8 rounded-md border border-border bg-white px-2 text-sm"
          >
            <option value="">No agent</option>
            {members.map((m) => (
              <option key={m.userId} value={m.userId}>
                {m.user?.name ?? m.userId}
              </option>
            ))}
          </select>
          <select
            value={params.sector_id ?? ""}
            onChange={(e) => set("sector_id", e.target.value)}
            className="h-8 rounded-md border border-border bg-white px-2 text-sm"
          >
            <option value="">No sector</option>
            {sectors.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
      );
    }
    case "assign":
    case "add_participant":
      return (
        <select
          value={params[action.actionType === "assign" ? "assignee_id" : "user_id"] ?? ""}
          onChange={(e) => set(action.actionType === "assign" ? "assignee_id" : "user_id", e.target.value)}
          className="h-8 w-full rounded-md border border-border bg-white px-2 text-sm"
        >
          <option value="">Pick member…</option>
          {members.map((m) => (
            <option key={m.userId} value={m.userId}>
              {m.user?.name ?? m.userId}
            </option>
          ))}
        </select>
      );
    case "set_status":
      return (
        <select
          value={params.status ?? "open"}
          onChange={(e) => set("status", e.target.value)}
          className="h-8 w-full rounded-md border border-border bg-white px-2 text-sm"
        >
          <option value="open">open</option>
          <option value="in_progress">in_progress</option>
          <option value="pending">pending</option>
          <option value="resolved">resolved</option>
        </select>
      );
    case "set_priority":
      return (
        <select
          value={params.priority ?? "medium"}
          onChange={(e) => set("priority", e.target.value)}
          className="h-8 w-full rounded-md border border-border bg-white px-2 text-sm"
        >
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
          <option value="urgent">urgent</option>
        </select>
      );
    default:
      return null;
  }
}
