"use client";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Activity, AlertTriangle, RefreshCw, ShieldAlert, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/form";
import { slaApi } from "@/lib/api";
import { WorkspaceSocket, type WsEvent } from "@/lib/websocket";
import { useAuthStore } from "@/stores/auth-store";
import type { AgentPresence, SupervisorOverview } from "@/types/sla";

const STATUSES: AgentPresence[] = ["online", "busy", "in_call", "away", "on_break", "offline"];

export default function SupervisorPage() {
  const { currentWorkspace, accessToken } = useAuthStore();
  const [overview, setOverview] = useState<SupervisorOverview | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  async function refresh() {
    if (!currentWorkspace) return;
    setLoading(true);
    try {
      const r = await slaApi.supervisorOverview(currentWorkspace.id);
      setOverview(r.data as SupervisorOverview);
      setLastUpdated(new Date());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    if (!currentWorkspace || !accessToken) return;
    const socket = new WorkspaceSocket(currentWorkspace.id, accessToken);
    const off = socket.on((event: WsEvent) => {
      if (
        event.type === "agent.status.updated" ||
        event.type === "conversation.assigned" ||
        event.type === "conversation.updated" ||
        event.type === "sla.updated" ||
        event.type === "sla.escalated" ||
        event.type === "supervisor.metrics.updated"
      ) {
        refresh();
      }
    });
    socket.connect();
    const timer = window.setInterval(refresh, 20_000);
    return () => {
      off();
      socket.disconnect();
      window.clearInterval(timer);
    };
  }, [currentWorkspace?.id, accessToken]); // eslint-disable-line react-hooks/exhaustive-deps

  async function evaluate() {
    if (!currentWorkspace) return;
    await slaApi.evaluate(currentWorkspace.id);
    await refresh();
  }

  async function setStatus(userId: string, status: AgentPresence) {
    if (!currentWorkspace) return;
    await slaApi.setAgentStatus(currentWorkspace.id, userId, { status });
    await refresh();
  }

  const capacityPct = useMemo(() => {
    if (!overview || overview.totals.capacityTotal <= 0) return 0;
    return Math.min(100, Math.round((overview.totals.capacityUsed / overview.totals.capacityTotal) * 100));
  }, [overview]);

  return (
    <div className="flex h-full flex-col bg-surface-2">
      <header className="border-b border-border bg-white px-6 py-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-base font-semibold text-slate-900">Supervisor</h1>
            <p className="text-xs text-muted">
              {lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString()}` : "Loading workspace metrics"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={refresh} loading={loading}>
              <RefreshCw className="h-3.5 w-3.5" /> Refresh
            </Button>
            <Button size="sm" onClick={evaluate}>
              <Activity className="h-3.5 w-3.5" /> Evaluate SLA
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-6 py-5">
        <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          <Metric label="Queue" value={overview?.totals.queued ?? 0} tone="blue" />
          <Metric label="Active" value={overview?.totals.active ?? 0} tone="green" />
          <Metric label="At risk" value={overview?.totals.atRisk ?? 0} tone="amber" />
          <Metric label="Violated" value={overview?.totals.violated ?? 0} tone="red" />
          <div className="rounded-lg border border-border bg-white p-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs font-medium uppercase text-muted">Capacity</span>
              <span className="text-sm font-semibold text-slate-900">{capacityPct}%</span>
            </div>
            <div className="h-2 rounded-full bg-slate-100">
              <div className="h-2 rounded-full bg-primary" style={{ width: `${capacityPct}%` }} />
            </div>
            <p className="mt-2 text-xs text-muted">
              {overview?.totals.capacityUsed ?? 0}/{overview?.totals.capacityTotal ?? 0} weighted
            </p>
          </div>
        </section>

        <div className="mt-5 grid gap-5 xl:grid-cols-[1fr_360px]">
          <section className="rounded-lg border border-border bg-white">
            <div className="flex items-center gap-2 border-b border-border px-4 py-3">
              <Users className="h-4 w-4 text-primary" />
              <h2 className="text-sm font-semibold text-slate-900">Agent occupancy</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b border-border bg-surface-2 text-xs text-muted">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium">Agent</th>
                    <th className="px-4 py-2 text-left font-medium">Status</th>
                    <th className="px-4 py-2 text-right font-medium">Chats</th>
                    <th className="px-4 py-2 text-right font-medium">Weight</th>
                    <th className="px-4 py-2 text-right font-medium">SLA</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {(overview?.agents ?? []).map((agent) => (
                    <tr key={agent.userId}>
                      <td className="px-4 py-3">
                        <p className="font-medium text-slate-900">{agent.name}</p>
                        <p className="text-xs text-muted">{agent.email}</p>
                      </td>
                      <td className="px-4 py-3">
                        <Select
                          value={agent.status}
                          onChange={(event) => setStatus(agent.userId, event.target.value as AgentPresence)}
                          className="min-w-32"
                        >
                          {STATUSES.map((status) => (
                            <option key={status} value={status}>{status.replace("_", " ")}</option>
                          ))}
                        </Select>
                      </td>
                      <td className="px-4 py-3 text-right text-slate-700">
                        {agent.assignedOpen}/{agent.maxConversations}
                      </td>
                      <td className="px-4 py-3 text-right text-slate-700">
                        {agent.weightedLoad}/{agent.maxWeight}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className={agent.violated > 0 ? "text-red-600" : agent.atRisk > 0 ? "text-amber-600" : "text-green-700"}>
                          {agent.atRisk}/{agent.violated}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {overview && overview.agents.length === 0 && (
                    <tr>
                      <td className="px-4 py-8 text-center text-muted" colSpan={5}>No agents found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className="rounded-lg border border-border bg-white">
            <div className="flex items-center gap-2 border-b border-border px-4 py-3">
              <ShieldAlert className="h-4 w-4 text-primary" />
              <h2 className="text-sm font-semibold text-slate-900">Sectors</h2>
            </div>
            <div className="divide-y divide-border">
              {(overview?.sectors ?? []).map((sector) => (
                <div key={sector.sectorId ?? "workspace"} className="px-4 py-3">
                  <div className="mb-2 flex items-center justify-between">
                    <p className="font-medium text-slate-900">{sector.sectorName}</p>
                    <span className="text-xs text-muted">{sector.active} active</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center text-xs">
                    <span className="rounded-md bg-blue-50 py-1 text-blue-700">{sector.queued} queued</span>
                    <span className="rounded-md bg-amber-50 py-1 text-amber-700">{sector.atRisk} risk</span>
                    <span className="rounded-md bg-red-50 py-1 text-red-700">{sector.violated} violated</span>
                  </div>
                </div>
              ))}
              {overview && overview.sectors.length === 0 && (
                <div className="px-4 py-8 text-center text-sm text-muted">No sector activity.</div>
              )}
            </div>
          </section>
        </div>

        <section className="mt-5 rounded-lg border border-border bg-white">
          <div className="flex items-center gap-2 border-b border-border px-4 py-3">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
            <h2 className="text-sm font-semibold text-slate-900">SLA alerts</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-border bg-surface-2 text-xs text-muted">
                <tr>
                  <th className="px-4 py-2 text-left font-medium">Conversation</th>
                  <th className="px-4 py-2 text-left font-medium">Priority</th>
                  <th className="px-4 py-2 text-left font-medium">SLA</th>
                  <th className="px-4 py-2 text-left font-medium">Last message</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {(overview?.alerts ?? []).map((alert) => (
                  <tr key={alert.conversationId}>
                    <td className="px-4 py-3">
                      <Link href="/inbox" className="font-medium text-primary hover:underline">
                        {alert.contactName ?? "Unknown"}
                      </Link>
                    </td>
                    <td className="px-4 py-3 capitalize text-slate-700">{alert.priority}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${alert.slaStatus === "violated" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"}`}>
                        {alert.slaStatus.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-muted">
                      {alert.lastMessageAt ? new Date(alert.lastMessageAt).toLocaleString() : "-"}
                    </td>
                  </tr>
                ))}
                {overview && overview.alerts.length === 0 && (
                  <tr>
                    <td className="px-4 py-8 text-center text-muted" colSpan={4}>No SLA alerts.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}

function Metric({ label, value, tone }: { label: string; value: number; tone: "blue" | "green" | "amber" | "red" }) {
  const tones = {
    blue: "bg-blue-50 text-blue-700",
    green: "bg-green-50 text-green-700",
    amber: "bg-amber-50 text-amber-700",
    red: "bg-red-50 text-red-700",
  };
  return (
    <div className="rounded-lg border border-border bg-white p-4">
      <div className={`mb-3 inline-flex rounded-md px-2 py-1 text-xs font-semibold ${tones[tone]}`}>{label}</div>
      <div className="text-2xl font-semibold text-slate-900">{value}</div>
    </div>
  );
}
