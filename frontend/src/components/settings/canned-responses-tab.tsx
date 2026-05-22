"use client";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { cannedResponsesApi, sectorsApi } from "@/lib/api";
import type { CannedCategory, CannedResponse, CannedVisibility } from "@/types/conversation";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { Input, Label, Textarea } from "@/components/ui/form";
import { Pencil, Plus, Tag, Trash2 } from "lucide-react";

export function CannedResponsesTab() {
  const { currentWorkspace } = useAuthStore();
  const [items, setItems] = useState<CannedResponse[]>([]);
  const [categories, setCategories] = useState<CannedCategory[]>([]);
  const [filter, setFilter] = useState<string>(""); // category_id
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState<CannedResponse | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [manageCategories, setManageCategories] = useState(false);

  useEffect(() => {
    if (!currentWorkspace) return;
    setLoading(true);
    cannedResponsesApi
      .list(currentWorkspace.id, { category_id: filter || undefined })
      .then((r) => setItems(r.data ?? []))
      .finally(() => setLoading(false));
  }, [currentWorkspace?.id, filter]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!currentWorkspace) return;
    cannedResponsesApi.listCategories(currentWorkspace.id).then((r) => setCategories(r.data ?? []));
  }, [currentWorkspace?.id, manageCategories]); // eslint-disable-line react-hooks/exhaustive-deps

  async function remove(id: string) {
    if (!currentWorkspace) return;
    if (!confirm("Delete this canned response?")) return;
    await cannedResponsesApi.delete(currentWorkspace.id, id);
    setItems((prev) => prev.filter((r) => r.id !== id));
  }

  return (
    <div className="max-w-3xl">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-slate-900">Canned responses</h2>
          <p className="text-sm text-muted">
            Categories, variables (<code className="font-mono">{`{{contact.name}}`}</code>), conditionals (
            <code className="font-mono">{`{{#if contact.vip}}…{{/if}}`}</code>), and visibility scoping.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={() => setManageCategories(true)}>
            <Tag className="h-3.5 w-3.5" /> Categories
          </Button>
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="h-3.5 w-3.5" /> New
          </Button>
        </div>
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-1">
        <button
          onClick={() => setFilter("")}
          className={`rounded-full border px-2 py-0.5 text-[11px] font-medium ${
            !filter ? "border-primary text-primary" : "border-border text-muted hover:text-slate-700"
          }`}
        >
          All categories
        </button>
        {categories.map((c) => (
          <button
            key={c.id}
            onClick={() => setFilter(filter === c.id ? "" : c.id)}
            className={`flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${
              filter === c.id ? "border-slate-900 text-slate-900" : "border-border text-muted hover:text-slate-700"
            }`}
          >
            {c.color && (
              <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: c.color }} />
            )}
            {c.name}
          </button>
        ))}
      </div>

      {loading && <p className="text-sm text-muted">Loading…</p>}
      <div className="flex flex-col gap-2">
        {items.map((r) => (
          <div key={r.id} className="flex items-start justify-between gap-4 rounded-lg border border-border bg-white p-4">
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded bg-surface-3 px-1.5 py-0.5 font-mono text-xs text-primary">/{r.shortcut}</span>
                <p className="font-medium text-slate-900">{r.title}</p>
                <span className="rounded-full bg-surface-3 px-2 py-0.5 text-[10px] font-semibold uppercase text-muted">
                  {r.visibility}
                </span>
                {r.language && (
                  <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-semibold uppercase text-blue-700">
                    {r.language}
                  </span>
                )}
                {!r.active && (
                  <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-700">
                    inactive
                  </span>
                )}
              </div>
              <p className="mt-1 line-clamp-2 text-xs text-muted">{r.content}</p>
            </div>
            <div className="flex shrink-0 items-center gap-1">
              <button className="text-muted hover:text-slate-900" onClick={() => setEditing(r)} aria-label="Edit">
                <Pencil className="h-4 w-4" />
              </button>
              <button className="text-muted hover:text-danger" onClick={() => remove(r.id)} aria-label="Delete">
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
        {!loading && items.length === 0 && (
          <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted">
            No canned responses yet.
          </div>
        )}
      </div>

      <CannedFormModal
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
          setItems((prev) => {
            const idx = prev.findIndex((p) => p.id === saved.id);
            if (idx === -1) return [...prev, saved];
            const copy = prev.slice();
            copy[idx] = saved;
            return copy;
          })
        }
      />

      <CategoriesModal
        open={manageCategories}
        onClose={() => setManageCategories(false)}
        workspaceId={currentWorkspace?.id ?? ""}
        categories={categories}
        onChange={setCategories}
      />
    </div>
  );
}

function CannedFormModal({
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
  initial: CannedResponse | null;
  categories: CannedCategory[];
  onSaved: (r: CannedResponse) => void;
}) {
  const [title, setTitle] = useState(initial?.title ?? "");
  const [shortcut, setShortcut] = useState(initial?.shortcut ?? "");
  const [content, setContent] = useState(initial?.content ?? "");
  const [active, setActive] = useState(initial?.active ?? true);
  const [visibility, setVisibility] = useState<CannedVisibility>(initial?.visibility ?? "workspace");
  const [categoryId, setCategoryId] = useState(initial?.categoryId ?? "");
  const [language, setLanguage] = useState(initial?.language ?? "");
  const [sectorId, setSectorId] = useState(initial?.sectorId ?? "");
  const [sectors, setSectors] = useState<{ id: string; name: string }[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open || !workspaceId) return;
    sectorsApi.list(workspaceId).then((r) => setSectors(r.data ?? []));
  }, [open, workspaceId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !shortcut.trim() || !content.trim()) {
      setError("Title, shortcut and content are required");
      return;
    }
    setLoading(true);
    try {
      const payload = {
        title,
        shortcut,
        content,
        active,
        visibility,
        category_id: categoryId || null,
        language: language || null,
        sector_id: visibility === "sector" && sectorId ? sectorId : null,
      };
      const r = initial
        ? await cannedResponsesApi.update(workspaceId, initial.id, payload)
        : await cannedResponsesApi.create(workspaceId, payload);
      onSaved(r.data as CannedResponse);
      onClose();
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(detail ?? "Failed to save canned response");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={initial ? "Edit canned response" : "New canned response"} size="lg">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label>Title *</Label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Welcome" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Shortcut *</Label>
            <Input
              value={shortcut}
              onChange={(e) => setShortcut(e.target.value.replace(/[^a-z0-9_-]/gi, ""))}
              placeholder="welcome"
            />
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label>Visibility</Label>
            <select
              value={visibility}
              onChange={(e) => setVisibility(e.target.value as CannedVisibility)}
              className="h-9 rounded-md border border-border bg-white px-2 text-sm"
            >
              <option value="workspace">Workspace</option>
              <option value="sector">Sector</option>
              <option value="user">Personal</option>
            </select>
          </div>
          {visibility === "sector" && (
            <div className="flex flex-col gap-1.5">
              <Label>Sector</Label>
              <select
                value={sectorId ?? ""}
                onChange={(e) => setSectorId(e.target.value)}
                className="h-9 rounded-md border border-border bg-white px-2 text-sm"
              >
                <option value="">Select…</option>
                {sectors.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
          )}
          <div className="flex flex-col gap-1.5">
            <Label>Category</Label>
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
            <Label>Language</Label>
            <Input
              value={language ?? ""}
              onChange={(e) => setLanguage(e.target.value)}
              placeholder="pt-BR"
              maxLength={10}
            />
          </div>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Content *</Label>
          <Textarea
            rows={5}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Olá {{contact.first_name}}, hoje é {{date.today}}…"
          />
          <p className="text-[11px] text-muted">
            Vars: <code className="font-mono">{`{{contact.name}} {{contact.first_name}} {{contact.phone}} {{conversation.protocol}} {{agent.name}} {{date.today}}`}</code>
            <br />
            Cond: <code className="font-mono">{`{{#if contact.vip}}Atendimento prioritário{{/if}}`}</code>
          </p>
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
  categories: CannedCategory[];
  onChange: (cats: CannedCategory[]) => void;
}) {
  const [name, setName] = useState("");
  const [color, setColor] = useState("#3B82F6");
  const [loading, setLoading] = useState(false);

  async function create() {
    if (!name.trim()) return;
    setLoading(true);
    try {
      const r = await cannedResponsesApi.createCategory(workspaceId, { name, color });
      onChange([...categories, r.data as CannedCategory]);
      setName("");
    } finally {
      setLoading(false);
    }
  }

  async function remove(id: string) {
    if (!confirm("Delete this category?")) return;
    await cannedResponsesApi.deleteCategory(workspaceId, id);
    onChange(categories.filter((c) => c.id !== id));
  }

  return (
    <Modal open={open} onClose={onClose} title="Canned response categories">
      <div className="flex flex-col gap-3">
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <Label>New category</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Vendas" />
          </div>
          <Input
            type="color"
            value={color}
            onChange={(e) => setColor(e.target.value)}
            className="h-9 w-12 p-1"
          />
          <Button onClick={create} loading={loading} disabled={!name.trim()}>
            Add
          </Button>
        </div>
        <div className="flex flex-col gap-1.5 max-h-72 overflow-y-auto">
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
