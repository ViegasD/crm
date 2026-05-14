"use client";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { slaApi } from "@/lib/api";
import type { SlaPolicy } from "@/types/sla";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { Input, Label } from "@/components/ui/form";
import { Plus, Trash2 } from "lucide-react";

export function SlaTab() {
  const { currentWorkspace } = useAuthStore();
  const [policies, setPolicies] = useState<SlaPolicy[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);

  useEffect(() => {
    if (!currentWorkspace) return;
    setLoading(true);
    slaApi.listPolicies(currentWorkspace.id)
      .then((r) => setPolicies(r.data ?? []))
      .finally(() => setLoading(false));
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function deletePolicy(id: string) {
    if (!currentWorkspace) return;
    if (!confirm("Delete this SLA policy?")) return;
    await slaApi.deletePolicy(currentWorkspace.id, id);
    setPolicies((prev) => prev.filter((p) => p.id !== id));
  }

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="font-semibold text-slate-900">SLA Policies</h2>
          <p className="text-sm text-muted">Define first response and resolution targets</p>
        </div>
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus className="h-3.5 w-3.5" /> New policy
        </Button>
      </div>

      {loading && <p className="text-sm text-muted">Loading…</p>}
      <div className="flex flex-col gap-2">
        {policies.map((p) => (
          <div key={p.id} className="flex items-center justify-between rounded-lg border border-border bg-white p-4">
            <div>
              <p className="font-medium text-slate-900">{p.name}</p>
              <p className="text-xs text-muted">
                First response: {p.firstResponseMinutes}min · Resolution: {p.resolutionMinutes}min
              </p>
            </div>
            <button onClick={() => deletePolicy(p.id)} className="text-muted hover:text-danger">
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
        {!loading && policies.length === 0 && (
          <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted">
            No SLA policies yet.
          </div>
        )}
      </div>

      <CreateSlaModal
        open={createOpen}
        workspaceId={currentWorkspace?.id ?? ""}
        onClose={() => setCreateOpen(false)}
        onCreated={(p) => setPolicies((prev) => [...prev, p])}
      />
    </div>
  );
}

function CreateSlaModal({ open, onClose, workspaceId, onCreated }: {
  open: boolean; onClose: () => void; workspaceId: string; onCreated: (p: SlaPolicy) => void;
}) {
  const [name, setName] = useState("");
  const [firstResponse, setFirstResponse] = useState("60");
  const [resolution, setResolution] = useState("480");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name) { setError("Name required"); return; }
    setLoading(true);
    try {
      const r = await slaApi.createPolicy(workspaceId, {
        name,
        first_response_minutes: Number(firstResponse),
        resolution_minutes: Number(resolution),
      });
      onCreated(r.data as SlaPolicy);
      onClose();
      setName(""); setFirstResponse("60"); setResolution("480"); setError("");
    } catch {
      setError("Failed to create policy");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="New SLA Policy">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label>Name *</Label>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Standard SLA" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label>First Response (min)</Label>
            <Input type="number" min={1} value={firstResponse} onChange={(e) => setFirstResponse(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Resolution (min)</Label>
            <Input type="number" min={1} value={resolution} onChange={(e) => setResolution(e.target.value)} />
          </div>
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
