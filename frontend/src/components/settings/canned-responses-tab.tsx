"use client";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { cannedResponsesApi } from "@/lib/api";
import type { CannedResponse } from "@/types/conversation";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { Input, Label, Textarea } from "@/components/ui/form";
import { Pencil, Plus, Trash2 } from "lucide-react";

export function CannedResponsesTab() {
  const { currentWorkspace } = useAuthStore();
  const [items, setItems] = useState<CannedResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState<CannedResponse | null>(null);
  const [createOpen, setCreateOpen] = useState(false);

  useEffect(() => {
    if (!currentWorkspace) return;
    setLoading(true);
    cannedResponsesApi
      .list(currentWorkspace.id)
      .then((r) => setItems(r.data ?? []))
      .finally(() => setLoading(false));
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

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
            Pre-written templates with variables like <code className="font-mono">{`{{contact.name}}`}</code>.
            Trigger with <code className="font-mono">/shortcut</code> in the reply box.
          </p>
        </div>
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus className="h-3.5 w-3.5" /> New
        </Button>
      </div>

      {loading && <p className="text-sm text-muted">Loading…</p>}
      <div className="flex flex-col gap-2">
        {items.map((r) => (
          <div
            key={r.id}
            className="flex items-start justify-between gap-4 rounded-lg border border-border bg-white p-4"
          >
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="rounded bg-surface-3 px-1.5 py-0.5 font-mono text-xs text-primary">
                  /{r.shortcut}
                </span>
                <p className="font-medium text-slate-900">{r.title}</p>
                {!r.active && (
                  <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-700">
                    inactive
                  </span>
                )}
              </div>
              <p className="mt-1 line-clamp-2 text-xs text-muted">{r.content}</p>
            </div>
            <div className="flex shrink-0 items-center gap-1">
              <button
                className="text-muted hover:text-slate-900"
                onClick={() => setEditing(r)}
                aria-label="Edit canned response"
              >
                <Pencil className="h-4 w-4" />
              </button>
              <button
                className="text-muted hover:text-danger"
                onClick={() => remove(r.id)}
                aria-label="Delete canned response"
              >
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

function CannedFormModal({
  open,
  onClose,
  workspaceId,
  initial,
  onSaved,
}: {
  open: boolean;
  onClose: () => void;
  workspaceId: string;
  initial: CannedResponse | null;
  onSaved: (r: CannedResponse) => void;
}) {
  const [title, setTitle] = useState(initial?.title ?? "");
  const [shortcut, setShortcut] = useState(initial?.shortcut ?? "");
  const [content, setContent] = useState(initial?.content ?? "");
  const [active, setActive] = useState(initial?.active ?? true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !shortcut.trim() || !content.trim()) {
      setError("Title, shortcut and content are required");
      return;
    }
    setLoading(true);
    try {
      const payload = { title, shortcut, content, active };
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
    <Modal open={open} onClose={onClose} title={initial ? "Edit canned response" : "New canned response"}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label>Title *</Label>
          <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Welcome message" />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Shortcut *</Label>
          <Input
            value={shortcut}
            onChange={(e) => setShortcut(e.target.value.replace(/[^a-z0-9_-]/gi, ""))}
            placeholder="welcome"
          />
          <p className="text-[11px] text-muted">
            Use as <code className="font-mono">/{shortcut || "shortcut"}</code> in the reply box.
          </p>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Content *</Label>
          <Textarea
            rows={5}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Hello {{contact.name}}, how can I help you today?"
          />
          <p className="text-[11px] text-muted">
            Available variables: <code className="font-mono">{`{{contact.name}} {{contact.phone}} {{conversation.protocol}} {{agent.name}}`}</code>
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
