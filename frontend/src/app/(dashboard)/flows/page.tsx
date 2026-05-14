"use client";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { flowsApi } from "@/lib/api";
import type { Flow } from "@/types/flow";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { Input, Label } from "@/components/ui/form";
import { Plus, Play, Pause, Pencil, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";

export default function FlowsPage() {
  const { currentWorkspace } = useAuthStore();
  const [flows, setFlows] = useState<Flow[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (!currentWorkspace) return;
    setLoading(true);
    flowsApi.list(currentWorkspace.id)
      .then((r) => setFlows(r.data ?? []))
      .finally(() => setLoading(false));
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function toggleActive(flow: Flow) {
    if (!currentWorkspace) return;
    if (flow.isActive) {
      const r = await flowsApi.deactivate(currentWorkspace.id, flow.id);
      setFlows((prev) => prev.map((f) => f.id === flow.id ? { ...f, isActive: false } : f));
    } else {
      const r = await flowsApi.activate(currentWorkspace.id, flow.id);
      setFlows((prev) => prev.map((f) => f.id === flow.id ? { ...f, isActive: true } : f));
    }
  }

  async function deleteFlow(id: string) {
    if (!currentWorkspace) return;
    if (!confirm("Delete this flow?")) return;
    await flowsApi.delete(currentWorkspace.id, id);
    setFlows((prev) => prev.filter((f) => f.id !== id));
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-border bg-white px-6 py-3">
        <h1 className="text-base font-semibold text-slate-900">Flows</h1>
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus className="h-3.5 w-3.5" /> New flow
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        {loading && <p className="text-sm text-muted">Loading…</p>}
        <div className="flex flex-col gap-3 max-w-2xl">
          {flows.map((flow) => (
            <div key={flow.id} className="flex items-center justify-between rounded-lg border border-border bg-white p-4">
              <div>
                <div className="flex items-center gap-2">
                  <p className="font-medium text-slate-900">{flow.name}</p>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${flow.isActive ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-500"}`}>
                    {flow.isActive ? "ACTIVE" : "DRAFT"}
                  </span>
                </div>
                {flow.description && <p className="text-xs text-muted">{flow.description}</p>}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => router.push(`/flows/${flow.id}`)}
                  title="Edit"
                >
                  <Pencil className="h-3.5 w-3.5" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => toggleActive(flow)}
                  title={flow.isActive ? "Pause" : "Activate"}
                >
                  {flow.isActive ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
                </Button>
                <Button variant="ghost" size="sm" onClick={() => deleteFlow(flow.id)} title="Delete">
                  <Trash2 className="h-3.5 w-3.5 text-danger" />
                </Button>
              </div>
            </div>
          ))}
          {!loading && flows.length === 0 && (
            <div className="rounded-lg border border-dashed border-border p-12 text-center text-sm text-muted">
              No flows yet. Create one to automate conversations.
            </div>
          )}
        </div>
      </div>

      <CreateFlowModal
        open={createOpen}
        workspaceId={currentWorkspace?.id ?? ""}
        onClose={() => setCreateOpen(false)}
        onCreated={(f) => {
          setFlows((prev) => [...prev, f]);
          router.push(`/flows/${f.id}`);
        }}
      />
    </div>
  );
}

function CreateFlowModal({ open, onClose, workspaceId, onCreated }: {
  open: boolean; onClose: () => void; workspaceId: string; onCreated: (f: Flow) => void;
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
      const r = await flowsApi.create(workspaceId, { name, description });
      onCreated(r.data as Flow);
      onClose();
      setName(""); setDescription(""); setError("");
    } catch {
      setError("Failed to create flow");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="New Flow">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label>Name *</Label>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Welcome flow" />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Description</Label>
          <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What this flow does" />
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

