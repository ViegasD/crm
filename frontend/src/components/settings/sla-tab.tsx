"use client";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { slaApi } from "@/lib/api";
import type { BusinessHours, RoutingRule, SlaPolicy } from "@/types/sla";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { Input, Label, Select } from "@/components/ui/form";
import { Clock, GitFork, Plus, Trash2, Zap } from "lucide-react";

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function SlaTab() {
  const { currentWorkspace } = useAuthStore();
  const [policies, setPolicies] = useState<SlaPolicy[]>([]);
  const [routingRules, setRoutingRules] = useState<RoutingRule[]>([]);
  const [hours, setHours] = useState<BusinessHours[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);

  async function refresh() {
    if (!currentWorkspace) return;
    setLoading(true);
    try {
      const [policyRes, routingRes, hoursRes] = await Promise.all([
        slaApi.listPolicies(currentWorkspace.id),
        slaApi.listRoutingRules(currentWorkspace.id),
        slaApi.listBusinessHours(currentWorkspace.id),
      ]);
      setPolicies(policyRes.data ?? []);
      setRoutingRules(routingRes.data ?? []);
      setHours(hoursRes.data ?? []);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function deletePolicy(id: string) {
    if (!currentWorkspace) return;
    if (!confirm("Delete this SLA policy?")) return;
    await slaApi.deletePolicy(currentWorkspace.id, id);
    setPolicies((prev) => prev.filter((p) => p.id !== id));
  }

  async function setDefaultRouting() {
    if (!currentWorkspace) return;
    const r = await slaApi.upsertRoutingRule(currentWorkspace.id, {
      sector_id: null,
      strategy: "least_busy",
      tiebreaker: "oldest_idle",
      sticky_hours: 24,
      auto_reassign_minutes: 10,
      reopen_window_hours: 24,
    });
    setRoutingRules((prev) => [r.data as RoutingRule, ...prev.filter((rule) => rule.sectorId)]);
  }

  async function seedBusinessHours() {
    if (!currentWorkspace) return;
    for (let weekday = 0; weekday < 5; weekday += 1) {
      await slaApi.createBusinessHours(currentWorkspace.id, {
        sector_id: null,
        weekday,
        start_minute: 9 * 60,
        end_minute: 18 * 60,
        timezone: "America/Sao_Paulo",
        active: true,
      });
    }
    refresh();
  }

  return (
    <div className="max-w-6xl">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-slate-900">SLA & Routing</h2>
          <p className="text-sm text-muted">Policies, business hours and queue dispatch</p>
        </div>
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus className="h-3.5 w-3.5" /> New policy
        </Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_340px]">
        <section className="rounded-lg border border-border bg-white">
          <div className="flex items-center gap-2 border-b border-border px-4 py-3">
            <Zap className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-semibold text-slate-900">Policies</h3>
          </div>
          {loading && <p className="px-4 py-3 text-sm text-muted">Loading…</p>}
          <div className="divide-y divide-border">
            {policies.map((p) => (
              <div key={p.id} className="flex items-start justify-between gap-3 px-4 py-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-medium text-slate-900">{p.name}</p>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${p.active ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-500"}`}>
                      {p.active ? "active" : "inactive"}
                    </span>
                    {p.priority && <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-700">{p.priority}</span>}
                  </div>
                  <p className="mt-1 text-xs text-muted">
                    First {p.firstResponseMinutes}m · Next {p.nextResponseMinutes ?? "off"}m · Resolution {p.resolutionMinutes}m · Risk {p.atRiskThresholdPct}%
                  </p>
                  <p className="mt-1 text-xs text-muted">
                    {p.businessHoursOnly ? "business hours" : "calendar time"} · customer-wait pause {p.pauseWhenWaitingCustomer ? "on" : "off"}
                  </p>
                </div>
                <button onClick={() => deletePolicy(p.id)} className="text-muted hover:text-danger" aria-label="Delete policy">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
            {!loading && policies.length === 0 && (
              <div className="p-8 text-center text-sm text-muted">No SLA policies yet.</div>
            )}
          </div>
        </section>

        <div className="space-y-4">
          <section className="rounded-lg border border-border bg-white">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <div className="flex items-center gap-2">
                <GitFork className="h-4 w-4 text-primary" />
                <h3 className="text-sm font-semibold text-slate-900">Routing</h3>
              </div>
              <Button size="sm" variant="outline" onClick={setDefaultRouting}>Default</Button>
            </div>
            <div className="px-4 py-3 text-sm">
              {routingRules.length === 0 ? (
                <p className="text-muted">No routing rules.</p>
              ) : (
                routingRules.map((rule) => (
                  <div key={rule.id} className="flex items-center justify-between py-1">
                    <span className="capitalize text-slate-700">{rule.sectorId ? "Sector" : "Workspace"}</span>
                    <span className="font-medium text-slate-900">{rule.strategy.replace("_", " ")}</span>
                  </div>
                ))
              )}
            </div>
          </section>

          <section className="rounded-lg border border-border bg-white">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-primary" />
                <h3 className="text-sm font-semibold text-slate-900">Business hours</h3>
              </div>
              <Button size="sm" variant="outline" onClick={seedBusinessHours}>9-18</Button>
            </div>
            <div className="px-4 py-3 text-sm">
              {hours.length === 0 ? (
                <p className="text-muted">No business hours.</p>
              ) : (
                hours.slice(0, 7).map((row) => (
                  <div key={row.id} className="flex items-center justify-between py-1">
                    <span className="text-slate-700">{WEEKDAYS[row.weekday] ?? row.weekday}</span>
                    <span className="font-medium text-slate-900">{fmtMinute(row.startMinute)}-{fmtMinute(row.endMinute)}</span>
                  </div>
                ))
              )}
            </div>
          </section>
        </div>
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
  const [firstResponse, setFirstResponse] = useState("30");
  const [nextResponse, setNextResponse] = useState("30");
  const [resolution, setResolution] = useState("480");
  const [priority, setPriority] = useState("");
  const [businessHoursOnly, setBusinessHoursOnly] = useState(true);
  const [pauseWhenWaiting, setPauseWhenWaiting] = useState(true);
  const [risk, setRisk] = useState("80");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name) { setError("Name required"); return; }
    setLoading(true);
    try {
      const r = await slaApi.createPolicy(workspaceId, {
        name,
        priority: priority || null,
        first_response_minutes: Number(firstResponse),
        next_response_minutes: nextResponse ? Number(nextResponse) : null,
        resolution_minutes: Number(resolution),
        business_hours_only: businessHoursOnly,
        pause_when_waiting_customer: pauseWhenWaiting,
        at_risk_threshold_pct: Number(risk),
      });
      onCreated(r.data as SlaPolicy);
      onClose();
      setName(""); setFirstResponse("30"); setNextResponse("30"); setResolution("480"); setPriority(""); setError("");
    } catch {
      setError("Failed to create policy");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="New SLA policy">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label>Name *</Label>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. WhatsApp priority" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label>First response</Label>
            <Input type="number" min={1} value={firstResponse} onChange={(e) => setFirstResponse(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Next response</Label>
            <Input type="number" min={1} value={nextResponse} onChange={(e) => setNextResponse(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Resolution</Label>
            <Input type="number" min={1} value={resolution} onChange={(e) => setResolution(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Risk %</Label>
            <Input type="number" min={1} max={99} value={risk} onChange={(e) => setRisk(e.target.value)} />
          </div>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Priority</Label>
          <Select value={priority} onChange={(e) => setPriority(e.target.value)}>
            <option value="">Any</option>
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
            <option value="urgent">urgent</option>
          </Select>
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input type="checkbox" checked={businessHoursOnly} onChange={(e) => setBusinessHoursOnly(e.target.checked)} />
          Count business hours only
        </label>
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input type="checkbox" checked={pauseWhenWaiting} onChange={(e) => setPauseWhenWaiting(e.target.checked)} />
          Pause next response when customer is holding
        </label>
        {error && <p className="text-sm text-danger">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button variant="outline" type="button" onClick={onClose}>Cancel</Button>
          <Button type="submit" loading={loading}>Create</Button>
        </div>
      </form>
    </Modal>
  );
}

function fmtMinute(value: number) {
  const hour = Math.floor(value / 60).toString().padStart(2, "0");
  const minute = (value % 60).toString().padStart(2, "0");
  return `${hour}:${minute}`;
}
