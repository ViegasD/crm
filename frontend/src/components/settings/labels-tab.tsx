"use client";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { labelsApi } from "@/lib/api";
import type { Label as LabelType } from "@/types/conversation";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { Input, Label as FormLabel } from "@/components/ui/form";
import { Pencil, Plus, Trash2 } from "lucide-react";

const PRESET_COLORS = [
  "#EF4444",
  "#F97316",
  "#F59E0B",
  "#10B981",
  "#06B6D4",
  "#3B82F6",
  "#8B5CF6",
  "#EC4899",
  "#64748B",
];

export function LabelsTab() {
  const { currentWorkspace } = useAuthStore();
  const [labels, setLabels] = useState<LabelType[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [editing, setEditing] = useState<LabelType | null>(null);

  useEffect(() => {
    if (!currentWorkspace) return;
    setLoading(true);
    labelsApi
      .list(currentWorkspace.id)
      .then((r) => setLabels(r.data ?? []))
      .finally(() => setLoading(false));
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function remove(id: string) {
    if (!currentWorkspace) return;
    if (!confirm("Delete this label? It will be removed from every conversation.")) return;
    await labelsApi.delete(currentWorkspace.id, id);
    setLabels((prev) => prev.filter((l) => l.id !== id));
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-slate-900">Labels</h2>
          <p className="text-sm text-muted">Tag conversations to categorize and filter the inbox.</p>
        </div>
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus className="h-3.5 w-3.5" /> New label
        </Button>
      </div>

      {loading && <p className="text-sm text-muted">Loading…</p>}
      <div className="flex flex-col gap-2">
        {labels.map((l) => (
          <div
            key={l.id}
            className="flex items-center justify-between gap-3 rounded-lg border border-border bg-white p-3"
          >
            <div className="flex items-center gap-3">
              <span className="inline-block h-5 w-5 rounded-full" style={{ backgroundColor: l.color }} />
              <span className="font-medium text-slate-900">{l.name}</span>
              <span className="text-xs text-muted">{l.color}</span>
            </div>
            <div className="flex items-center gap-1">
              <button
                className="text-muted hover:text-slate-900"
                onClick={() => setEditing(l)}
                aria-label="Edit label"
              >
                <Pencil className="h-4 w-4" />
              </button>
              <button
                className="text-muted hover:text-danger"
                onClick={() => remove(l.id)}
                aria-label="Delete label"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
        {!loading && labels.length === 0 && (
          <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted">
            No labels yet.
          </div>
        )}
      </div>

      <LabelFormModal
        key={editing?.id ?? "new"}
        open={createOpen || editing !== null}
        initial={editing}
        workspaceId={currentWorkspace?.id ?? ""}
        onClose={() => {
          setCreateOpen(false);
          setEditing(null);
        }}
        onSaved={(saved) =>
          setLabels((prev) => {
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

function LabelFormModal({
  open,
  onClose,
  workspaceId,
  initial,
  onSaved,
}: {
  open: boolean;
  onClose: () => void;
  workspaceId: string;
  initial: LabelType | null;
  onSaved: (l: LabelType) => void;
}) {
  const [name, setName] = useState(initial?.name ?? "");
  const [color, setColor] = useState(initial?.color ?? PRESET_COLORS[5]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      setError("Name required");
      return;
    }
    setLoading(true);
    try {
      const r = initial
        ? await labelsApi.update(workspaceId, initial.id, { name, color })
        : await labelsApi.create(workspaceId, name, color);
      onSaved(r.data as LabelType);
      onClose();
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(detail ?? "Failed to save label");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={initial ? "Edit label" : "New label"}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <FormLabel>Name *</FormLabel>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Urgent" />
        </div>
        <div className="flex flex-col gap-2">
          <FormLabel>Color</FormLabel>
          <div className="flex flex-wrap items-center gap-2">
            {PRESET_COLORS.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setColor(c)}
                className="h-7 w-7 rounded-full border-2 transition-transform"
                style={{
                  backgroundColor: c,
                  borderColor: color === c ? "#0f172a" : "transparent",
                }}
                aria-label={`Pick color ${c}`}
              />
            ))}
            <Input
              value={color}
              onChange={(e) => setColor(e.target.value)}
              className="h-7 w-28 text-xs"
              placeholder="#RRGGBB"
            />
          </div>
        </div>
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
