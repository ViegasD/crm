"use client";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { serviceReasonsApi, transferReasonsApi } from "@/lib/api";
import type { ServiceReason, TransferReason } from "@/types/conversation";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { Input, Label } from "@/components/ui/form";
import { Pencil, Plus, Trash2 } from "lucide-react";

type TabKey = "transfer" | "service";

export function ReasonsTab() {
  const [tab, setTab] = useState<TabKey>("transfer");
  return (
    <div className="max-w-3xl">
      <div className="mb-4 flex items-center gap-3">
        <button
          onClick={() => setTab("transfer")}
          className={`text-sm font-medium ${tab === "transfer" ? "text-primary" : "text-muted hover:text-slate-900"}`}
        >
          Transfer reasons
        </button>
        <span className="text-muted">·</span>
        <button
          onClick={() => setTab("service")}
          className={`text-sm font-medium ${tab === "service" ? "text-primary" : "text-muted hover:text-slate-900"}`}
        >
          Service reasons
        </button>
      </div>
      {tab === "transfer" ? <TransferReasonsList /> : <ServiceReasonsList />}
    </div>
  );
}

function TransferReasonsList() {
  const { currentWorkspace } = useAuthStore();
  const [items, setItems] = useState<TransferReason[]>([]);
  const [editing, setEditing] = useState<TransferReason | null>(null);
  const [createOpen, setCreateOpen] = useState(false);

  useEffect(() => {
    if (!currentWorkspace) return;
    transferReasonsApi.list(currentWorkspace.id).then((r) => setItems(r.data ?? []));
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function remove(id: string) {
    if (!currentWorkspace) return;
    if (!confirm("Delete this reason?")) return;
    await transferReasonsApi.delete(currentWorkspace.id, id);
    setItems((prev) => prev.filter((r) => r.id !== id));
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm text-muted">
          When at least one reason is marked <span className="font-semibold">required</span>, agents must pick one to transfer a
          conversation.
        </p>
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus className="h-3.5 w-3.5" /> New
        </Button>
      </div>
      <div className="flex flex-col gap-2">
        {items.map((r) => (
          <div key={r.id} className="flex items-center justify-between rounded-lg border border-border bg-white p-3">
            <div className="flex items-center gap-3">
              <span className="font-medium text-slate-900">{r.label}</span>
              {r.required && (
                <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-700">
                  required
                </span>
              )}
              {!r.active && <span className="text-xs text-muted">(inactive)</span>}
            </div>
            <div className="flex items-center gap-1">
              <button className="text-muted hover:text-slate-900" onClick={() => setEditing(r)} aria-label="Edit">
                <Pencil className="h-4 w-4" />
              </button>
              <button className="text-muted hover:text-danger" onClick={() => remove(r.id)} aria-label="Delete">
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
        {items.length === 0 && (
          <div className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted">
            No transfer reasons yet.
          </div>
        )}
      </div>
      <TransferReasonModal
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

function TransferReasonModal({
  open,
  onClose,
  workspaceId,
  initial,
  onSaved,
}: {
  open: boolean;
  onClose: () => void;
  workspaceId: string;
  initial: TransferReason | null;
  onSaved: (r: TransferReason) => void;
}) {
  const [label, setLabel] = useState(initial?.label ?? "");
  const [required, setRequired] = useState(initial?.required ?? false);
  const [active, setActive] = useState(initial?.active ?? true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!label.trim()) {
      setError("Label required");
      return;
    }
    setLoading(true);
    try {
      const payload = { label, required, active };
      const r = initial
        ? await transferReasonsApi.update(workspaceId, initial.id, payload)
        : await transferReasonsApi.create(workspaceId, payload);
      onSaved(r.data as TransferReason);
      onClose();
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(detail ?? "Failed to save");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={initial ? "Edit transfer reason" : "New transfer reason"}>
      <form onSubmit={submit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label>Label *</Label>
          <Input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="Mudou de setor" />
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={required} onChange={(e) => setRequired(e.target.checked)} />
          <span>Required (agents must pick a reason)</span>
        </label>
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

function ServiceReasonsList() {
  const { currentWorkspace } = useAuthStore();
  const [items, setItems] = useState<ServiceReason[]>([]);
  const [editing, setEditing] = useState<ServiceReason | null>(null);
  const [createOpen, setCreateOpen] = useState(false);

  useEffect(() => {
    if (!currentWorkspace) return;
    serviceReasonsApi.list(currentWorkspace.id).then((r) => setItems(r.data ?? []));
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function remove(id: string) {
    if (!currentWorkspace) return;
    if (!confirm("Delete this reason?")) return;
    await serviceReasonsApi.delete(currentWorkspace.id, id);
    setItems((prev) => prev.filter((r) => r.id !== id));
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm text-muted">
          Catalog of reasons agents pick when resolving a conversation. Drives the reports drill-down.
        </p>
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus className="h-3.5 w-3.5" /> New
        </Button>
      </div>
      <div className="flex flex-col gap-2">
        {items.map((r) => (
          <div key={r.id} className="flex items-start justify-between rounded-lg border border-border bg-white p-3">
            <div>
              <p className="font-medium text-slate-900">{r.label}</p>
              {r.description && <p className="text-xs text-muted">{r.description}</p>}
              {!r.active && <span className="text-xs text-muted">(inactive)</span>}
            </div>
            <div className="flex items-center gap-1">
              <button className="text-muted hover:text-slate-900" onClick={() => setEditing(r)} aria-label="Edit">
                <Pencil className="h-4 w-4" />
              </button>
              <button className="text-muted hover:text-danger" onClick={() => remove(r.id)} aria-label="Delete">
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
        {items.length === 0 && (
          <div className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted">
            No service reasons yet.
          </div>
        )}
      </div>
      <ServiceReasonModal
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

function ServiceReasonModal({
  open,
  onClose,
  workspaceId,
  initial,
  onSaved,
}: {
  open: boolean;
  onClose: () => void;
  workspaceId: string;
  initial: ServiceReason | null;
  onSaved: (r: ServiceReason) => void;
}) {
  const [label, setLabel] = useState(initial?.label ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [active, setActive] = useState(initial?.active ?? true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!label.trim()) {
      setError("Label required");
      return;
    }
    setLoading(true);
    try {
      const payload = { label, description: description || null, active };
      const r = initial
        ? await serviceReasonsApi.update(workspaceId, initial.id, payload)
        : await serviceReasonsApi.create(workspaceId, payload);
      onSaved(r.data as ServiceReason);
      onClose();
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(detail ?? "Failed to save");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={initial ? "Edit service reason" : "New service reason"}>
      <form onSubmit={submit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label>Label *</Label>
          <Input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="Dúvida de produto" />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Description</Label>
          <Input value={description ?? ""} onChange={(e) => setDescription(e.target.value)} />
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
