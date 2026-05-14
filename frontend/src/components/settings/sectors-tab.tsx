"use client";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { sectorsApi } from "@/lib/api";
import type { Sector } from "@/types/workspace";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { Input, Label } from "@/components/ui/form";
import { Plus, Trash2 } from "lucide-react";

export function SectorsTab() {
  const { currentWorkspace } = useAuthStore();
  const [sectors, setSectors] = useState<Sector[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);

  useEffect(() => {
    if (!currentWorkspace) return;
    setLoading(true);
    sectorsApi.list(currentWorkspace.id)
      .then((r) => setSectors(r.data ?? []))
      .finally(() => setLoading(false));
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function deleteSector(id: string) {
    if (!currentWorkspace) return;
    if (!confirm("Delete this sector?")) return;
    await sectorsApi.delete(currentWorkspace.id, id);
    setSectors((prev) => prev.filter((s) => s.id !== id));
  }

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="font-semibold text-slate-900">Sectors</h2>
          <p className="text-sm text-muted">Organize agents into teams or departments</p>
        </div>
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus className="h-3.5 w-3.5" /> Add sector
        </Button>
      </div>

      {loading && <p className="text-sm text-muted">Loading…</p>}
      <div className="flex flex-col gap-2">
        {sectors.map((s) => (
          <div key={s.id} className="flex items-center justify-between rounded-lg border border-border bg-white p-4">
            <div>
              <p className="font-medium text-slate-900">{s.name}</p>
              {s.description && <p className="text-xs text-muted">{s.description}</p>}
            </div>
            <button onClick={() => deleteSector(s.id)} className="text-muted hover:text-danger">
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
        {!loading && sectors.length === 0 && (
          <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted">
            No sectors yet.
          </div>
        )}
      </div>

      <CreateSectorModal
        open={createOpen}
        workspaceId={currentWorkspace?.id ?? ""}
        onClose={() => setCreateOpen(false)}
        onCreated={(s) => setSectors((prev) => [...prev, s])}
      />
    </div>
  );
}

function CreateSectorModal({ open, onClose, workspaceId, onCreated }: {
  open: boolean; onClose: () => void; workspaceId: string; onCreated: (s: Sector) => void;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name) { setError("Name required"); return; }
    setLoading(true);
    try {
      const r = await sectorsApi.create(workspaceId, name, description);
      onCreated(r.data as Sector);
      onClose();
      setName(""); setDescription(""); setError("");
    } catch {
      setError("Failed to create sector");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="New Sector">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label>Name *</Label>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Sales" />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Description</Label>
          <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional description" />
        </div>
        {error && <p className="text-sm text-danger">{error}</p>}
        <div className="flex gap-2 justify-end">
          <Button variant="outline" type="button" onClick={onClose}>Cancel</Button>
          <Button type="submit" loading={loading}>Create</Button>
        </div>
      </form>
    </Modal>
  );
}
