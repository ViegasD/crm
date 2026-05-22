"use client";
import { useEffect, useMemo, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { labelsApi } from "@/lib/api";
import type { Label as LabelType, LabelCategory } from "@/types/conversation";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { Input, Label as FormLabel } from "@/components/ui/form";
import { Pencil, Plus, Tag, Trash2 } from "lucide-react";

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
  const [categories, setCategories] = useState<LabelCategory[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [editing, setEditing] = useState<LabelType | null>(null);
  const [categoriesOpen, setCategoriesOpen] = useState(false);

  useEffect(() => {
    if (!currentWorkspace) return;
    setLoading(true);
    Promise.all([
      labelsApi.list(currentWorkspace.id),
      labelsApi.listCategories(currentWorkspace.id),
    ])
      .then(([l, c]) => {
        setLabels(l.data ?? []);
        setCategories(c.data ?? []);
      })
      .finally(() => setLoading(false));
  }, [currentWorkspace?.id, categoriesOpen]); // eslint-disable-line react-hooks/exhaustive-deps

  async function remove(id: string) {
    if (!currentWorkspace) return;
    if (!confirm("Delete this label?")) return;
    await labelsApi.delete(currentWorkspace.id, id);
    setLabels((prev) => prev.filter((l) => l.id !== id));
  }

  const grouped = useMemo(() => {
    const map = new Map<string, { category: LabelCategory | null; labels: LabelType[] }>();
    map.set("__none__", { category: null, labels: [] });
    categories.forEach((c) => map.set(c.id, { category: c, labels: [] }));
    labels.forEach((l) => {
      const key = l.categoryId ?? "__none__";
      if (!map.has(key)) map.set(key, { category: null, labels: [] });
      map.get(key)!.labels.push(l);
    });
    return Array.from(map.values());
  }, [labels, categories]);

  return (
    <div className="max-w-2xl">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-slate-900">Labels</h2>
          <p className="text-sm text-muted">Tag conversations and group labels into categories.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={() => setCategoriesOpen(true)}>
            <Tag className="h-3.5 w-3.5" /> Categories
          </Button>
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="h-3.5 w-3.5" /> New label
          </Button>
        </div>
      </div>

      {loading && <p className="text-sm text-muted">Loading…</p>}
      <div className="flex flex-col gap-4">
        {grouped.map((group) => {
          if (group.labels.length === 0 && !group.category) return null;
          return (
            <div key={group.category?.id ?? "__none__"} className="flex flex-col gap-2">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted">
                {group.category?.color && (
                  <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: group.category.color }} />
                )}
                {group.category?.name ?? "Uncategorized"}
              </div>
              {group.labels.map((l) => (
                <div
                  key={l.id}
                  className="flex items-center justify-between gap-3 rounded-lg border border-border bg-white p-3"
                >
                  <div className="flex items-center gap-3">
                    <span className="inline-block h-5 w-5 rounded-full" style={{ backgroundColor: l.color }} />
                    <span className="font-medium text-slate-900">{l.name}</span>
                    {l.description && <span className="text-xs text-muted">— {l.description}</span>}
                  </div>
                  <div className="flex items-center gap-1">
                    <button className="text-muted hover:text-slate-900" onClick={() => setEditing(l)} aria-label="Edit">
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button className="text-muted hover:text-danger" onClick={() => remove(l.id)} aria-label="Delete">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          );
        })}
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
        categories={categories}
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

      <CategoriesModal
        open={categoriesOpen}
        onClose={() => setCategoriesOpen(false)}
        workspaceId={currentWorkspace?.id ?? ""}
        categories={categories}
        onChange={setCategories}
      />
    </div>
  );
}

function LabelFormModal({
  open,
  onClose,
  workspaceId,
  initial,
  categories,
  onSaved,
}: {
  open: boolean;
  onClose: () => void;
  workspaceId: string;
  initial: LabelType | null;
  categories: LabelCategory[];
  onSaved: (l: LabelType) => void;
}) {
  const [name, setName] = useState(initial?.name ?? "");
  const [color, setColor] = useState(initial?.color ?? PRESET_COLORS[5]);
  const [categoryId, setCategoryId] = useState(initial?.categoryId ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
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
      const payload = {
        name,
        color,
        category_id: categoryId || null,
        description: description || null,
      };
      const r = initial
        ? await labelsApi.update(workspaceId, initial.id, payload)
        : await labelsApi.create(workspaceId, payload);
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
        <div className="flex flex-col gap-1.5">
          <FormLabel>Category</FormLabel>
          <select
            value={categoryId ?? ""}
            onChange={(e) => setCategoryId(e.target.value)}
            className="h-9 rounded-md border border-border bg-white px-2 text-sm"
          >
            <option value="">No category</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <FormLabel>Description</FormLabel>
          <Input value={description ?? ""} onChange={(e) => setDescription(e.target.value)} />
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

function CategoriesModal({
  open,
  onClose,
  workspaceId,
  categories,
  onChange,
}: {
  open: boolean;
  onClose: () => void;
  workspaceId: string;
  categories: LabelCategory[];
  onChange: (c: LabelCategory[]) => void;
}) {
  const [name, setName] = useState("");
  const [color, setColor] = useState("#3B82F6");
  const [loading, setLoading] = useState(false);

  async function create() {
    if (!name.trim()) return;
    setLoading(true);
    try {
      const r = await labelsApi.createCategory(workspaceId, { name, color });
      onChange([...categories, r.data as LabelCategory]);
      setName("");
    } finally {
      setLoading(false);
    }
  }

  async function remove(id: string) {
    if (!confirm("Delete this category? Labels stay but become uncategorized.")) return;
    await labelsApi.deleteCategory(workspaceId, id);
    onChange(categories.filter((c) => c.id !== id));
  }

  return (
    <Modal open={open} onClose={onClose} title="Label categories">
      <div className="flex flex-col gap-3">
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <FormLabel>New category</FormLabel>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Prioridade" />
          </div>
          <Input type="color" value={color} onChange={(e) => setColor(e.target.value)} className="h-9 w-12 p-1" />
          <Button onClick={create} loading={loading} disabled={!name.trim()}>
            Add
          </Button>
        </div>
        <div className="flex max-h-72 flex-col gap-1.5 overflow-y-auto">
          {categories.map((c) => (
            <div key={c.id} className="flex items-center justify-between rounded-md border border-border px-3 py-2">
              <div className="flex items-center gap-2">
                {c.color && <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: c.color }} />}
                <span className="text-sm">{c.name}</span>
              </div>
              <button className="text-muted hover:text-danger" onClick={() => remove(c.id)}>
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
          {categories.length === 0 && <p className="text-xs text-muted">No categories yet.</p>}
        </div>
      </div>
    </Modal>
  );
}
