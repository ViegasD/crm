"use client";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { channelsApi, webhookOpsApi } from "@/lib/api";
import type {
  ChannelCircuit,
  CircuitState,
  LatencyStats,
  WebhookIpAllowlistRow,
} from "@/types/conversation";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { Input, Label } from "@/components/ui/form";
import { Activity, AlertOctagon, KeyRound, Plus, RefreshCw, ShieldAlert, Trash2 } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

type SubTab = "latency" | "circuits" | "allowlist" | "rotation";

export function WebhookOpsTab() {
  const [tab, setTab] = useState<SubTab>("latency");
  return (
    <div className="max-w-5xl">
      <div className="mb-4 flex items-center gap-3">
        {(
          [
            { v: "latency", label: "Latency", icon: <Activity className="h-3.5 w-3.5" /> },
            { v: "circuits", label: "Circuits", icon: <AlertOctagon className="h-3.5 w-3.5" /> },
            { v: "allowlist", label: "IP allowlist", icon: <ShieldAlert className="h-3.5 w-3.5" /> },
            { v: "rotation", label: "Secret rotation", icon: <KeyRound className="h-3.5 w-3.5" /> },
          ] as { v: SubTab; label: string; icon: React.ReactNode }[]
        ).map((s) => (
          <button
            key={s.v}
            onClick={() => setTab(s.v)}
            className={`flex items-center gap-1 text-sm font-medium ${
              tab === s.v ? "text-primary" : "text-muted hover:text-slate-900"
            }`}
          >
            {s.icon} {s.label}
          </button>
        ))}
      </div>
      {tab === "latency" && <LatencyPanel />}
      {tab === "circuits" && <CircuitsPanel />}
      {tab === "allowlist" && <AllowlistPanel />}
      {tab === "rotation" && <RotationPanel />}
    </div>
  );
}

function LatencyPanel() {
  const { currentWorkspace } = useAuthStore();
  const [windowMinutes, setWindowMinutes] = useState(60);
  const [stats, setStats] = useState<LatencyStats | null>(null);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    if (!currentWorkspace) return;
    setLoading(true);
    try {
      const r = await webhookOpsApi.latency(currentWorkspace.id, windowMinutes);
      setStats(r.data as LatencyStats);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [currentWorkspace?.id, windowMinutes]); // eslint-disable-line react-hooks/exhaustive-deps

  function fmt(ms?: number | null) {
    if (ms == null) return "—";
    if (ms < 1000) return `${Math.round(ms)} ms`;
    return `${(ms / 1000).toFixed(2)} s`;
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm text-muted">
          End-to-end processing latency for inbound webhooks (parse → adapter → persist).
        </p>
        <div className="flex items-center gap-2">
          <select
            value={windowMinutes}
            onChange={(e) => setWindowMinutes(Number(e.target.value))}
            className="h-8 rounded-md border border-border bg-white px-2 text-xs"
          >
            <option value={15}>last 15 min</option>
            <option value={60}>last hour</option>
            <option value={360}>last 6h</option>
            <option value={1440}>last 24h</option>
          </select>
          <Button variant="outline" size="sm" onClick={refresh} loading={loading}>
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </Button>
        </div>
      </div>
      <div className="grid grid-cols-5 gap-2">
        {(
          [
            ["p50", stats?.p50Ms],
            ["p95", stats?.p95Ms],
            ["p99", stats?.p99Ms],
            ["avg", stats?.avgMs],
            ["max", stats?.maxMs],
          ] as [string, number | null | undefined][]
        ).map(([label, value]) => (
          <div key={label} className="rounded-lg border border-border bg-white p-4">
            <div className="text-[11px] uppercase text-muted">{label}</div>
            <div className="mt-1 text-2xl font-semibold text-slate-900">{fmt(value)}</div>
          </div>
        ))}
      </div>
      <p className="mt-3 text-[11px] text-muted">
        Samples: {stats?.sampleSize ?? 0} attempts in the last {windowMinutes} min.
      </p>
    </div>
  );
}

function CircuitsPanel() {
  const { currentWorkspace } = useAuthStore();
  const [items, setItems] = useState<ChannelCircuit[]>([]);
  const [channelNames, setChannelNames] = useState<Record<string, string>>({});

  async function refresh() {
    if (!currentWorkspace) return;
    const [c, ch] = await Promise.all([
      webhookOpsApi.listCircuits(currentWorkspace.id),
      channelsApi.list(currentWorkspace.id),
    ]);
    setItems(c.data ?? []);
    const map: Record<string, string> = {};
    (ch.data ?? []).forEach((a: { id: string; displayName?: string; display_name?: string }) => {
      map[a.id] = a.displayName ?? a.display_name ?? a.id;
    });
    setChannelNames(map);
  }

  useEffect(() => {
    refresh();
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function reset(id: string) {
    if (!currentWorkspace) return;
    await webhookOpsApi.resetCircuit(currentWorkspace.id, id);
    refresh();
  }

  function stateBadge(state: CircuitState) {
    const cls = {
      closed: "bg-green-100 text-green-700",
      half_open: "bg-amber-100 text-amber-700",
      open: "bg-red-100 text-red-700",
    }[state];
    return <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${cls}`}>{state}</span>;
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm text-muted">
          Per-channel breakers. After 10 consecutive failures the channel opens for 5 min, then a probe decides.
        </p>
        <Button variant="outline" size="sm" onClick={refresh}>
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </Button>
      </div>
      <div className="overflow-hidden rounded-lg border border-border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-surface-2 text-xs uppercase text-muted">
            <tr>
              <th className="px-3 py-2 text-left">Channel</th>
              <th className="px-3 py-2 text-left">State</th>
              <th className="px-3 py-2 text-left">Failures</th>
              <th className="px-3 py-2 text-left">Opened</th>
              <th className="px-3 py-2 text-left">Next probe</th>
              <th className="px-3 py-2 text-left">Last error</th>
              <th className="px-3 py-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.id} className="border-t border-border">
                <td className="px-3 py-2 font-medium text-slate-900">
                  {channelNames[c.channelAccountId] ?? c.channelAccountId.slice(0, 8)}
                </td>
                <td className="px-3 py-2">{stateBadge(c.state)}</td>
                <td className="px-3 py-2 text-xs">{c.failureCount}</td>
                <td className="px-3 py-2 text-xs text-muted">
                  {c.openedAt ? formatDistanceToNow(new Date(c.openedAt), { addSuffix: true }) : "—"}
                </td>
                <td className="px-3 py-2 text-xs text-muted">
                  {c.nextProbeAt ? formatDistanceToNow(new Date(c.nextProbeAt), { addSuffix: true }) : "—"}
                </td>
                <td className="max-w-xs truncate px-3 py-2 text-xs text-muted" title={c.lastErrorMessage ?? ""}>
                  {c.lastErrorMessage ?? "—"}
                </td>
                <td className="px-3 py-2 text-right">
                  {c.state !== "closed" && (
                    <button className="text-xs text-primary hover:underline" onClick={() => reset(c.channelAccountId)}>
                      Reset
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={7} className="px-3 py-8 text-center text-sm text-muted">
                  All channels nominal.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AllowlistPanel() {
  const { currentWorkspace } = useAuthStore();
  const [items, setItems] = useState<WebhookIpAllowlistRow[]>([]);
  const [addOpen, setAddOpen] = useState(false);
  const [provider, setProvider] = useState("meta_cloud");

  async function refresh() {
    if (!currentWorkspace) return;
    const r = await webhookOpsApi.listIpAllowlist(currentWorkspace.id);
    setItems(r.data ?? []);
  }

  useEffect(() => {
    refresh();
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function remove(id: string) {
    if (!currentWorkspace) return;
    if (!confirm("Remove this CIDR from the allowlist?")) return;
    await webhookOpsApi.deleteIpAllowlist(currentWorkspace.id, id);
    setItems((prev) => prev.filter((i) => i.id !== id));
  }

  const grouped = items.reduce<Record<string, WebhookIpAllowlistRow[]>>((acc, row) => {
    (acc[row.provider] = acc[row.provider] ?? []).push(row);
    return acc;
  }, {});

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm text-muted">
          If at least one CIDR exists for a provider, only those IPs may post webhooks for that provider.
        </p>
        <Button size="sm" onClick={() => setAddOpen(true)}>
          <Plus className="h-3.5 w-3.5" /> Add CIDR
        </Button>
      </div>
      {Object.keys(grouped).length === 0 && (
        <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted">
          No allowlist — all IPs accepted (signature still enforced).
        </div>
      )}
      {Object.entries(grouped).map(([provider, rows]) => (
        <div key={provider} className="mb-4">
          <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted">{provider}</div>
          <div className="overflow-hidden rounded-lg border border-border bg-white">
            <table className="w-full text-sm">
              <thead className="bg-surface-2 text-xs uppercase text-muted">
                <tr>
                  <th className="px-3 py-2 text-left">CIDR</th>
                  <th className="px-3 py-2 text-left">Description</th>
                  <th className="px-3 py-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id} className="border-t border-border">
                    <td className="px-3 py-2 font-mono text-xs">{r.cidr}</td>
                    <td className="px-3 py-2 text-xs text-muted">{r.description ?? "—"}</td>
                    <td className="px-3 py-2 text-right">
                      <button className="text-muted hover:text-danger" onClick={() => remove(r.id)}>
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}

      <AddAllowlistModal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        workspaceId={currentWorkspace?.id ?? ""}
        defaultProvider={provider}
        onAdded={(row) => {
          setItems((prev) => [...prev, row]);
          setProvider(row.provider);
        }}
      />
    </div>
  );
}

function AddAllowlistModal({
  open,
  onClose,
  workspaceId,
  defaultProvider,
  onAdded,
}: {
  open: boolean;
  onClose: () => void;
  workspaceId: string;
  defaultProvider: string;
  onAdded: (row: WebhookIpAllowlistRow) => void;
}) {
  const [provider, setProvider] = useState(defaultProvider);
  const [cidr, setCidr] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!cidr.trim()) {
      setError("CIDR required");
      return;
    }
    setLoading(true);
    try {
      const r = await webhookOpsApi.addIpAllowlist(workspaceId, {
        provider,
        cidr,
        description: description || null,
      });
      onAdded(r.data as WebhookIpAllowlistRow);
      onClose();
      setCidr("");
      setDescription("");
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(detail ?? "Failed to add");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Add CIDR to allowlist">
      <form onSubmit={submit} className="flex flex-col gap-3">
        <div className="flex flex-col gap-1.5">
          <Label>Provider</Label>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            className="h-9 rounded-md border border-border bg-white px-2 text-sm"
          >
            <option value="meta_cloud">meta_cloud</option>
            <option value="evolution">evolution</option>
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>CIDR *</Label>
          <Input value={cidr} onChange={(e) => setCidr(e.target.value)} placeholder="173.252.0.0/16" />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Description</Label>
          <Input value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
        {error && <p className="text-sm text-danger">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button variant="outline" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={loading}>
            Add
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function RotationPanel() {
  const { currentWorkspace } = useAuthStore();
  const workspaceId = currentWorkspace?.id;
  const [channels, setChannels] = useState<{ id: string; displayName: string; provider?: string | null }[]>([]);
  const [rotateOpen, setRotateOpen] = useState(false);
  const [picked, setPicked] = useState<{ id: string; displayName: string; provider?: string | null } | null>(null);

  useEffect(() => {
    if (!workspaceId) return;
    channelsApi.list(workspaceId).then((r) => {
      setChannels(
        (r.data ?? []).map((c: { id: string; displayName?: string; display_name?: string; provider?: string }) => ({
          id: c.id,
          displayName: c.displayName ?? c.display_name ?? c.id,
          provider: c.provider,
        })),
      );
    });
  }, [workspaceId]);

  async function finalize(channel: { id: string; provider?: string | null }) {
    if (!currentWorkspace) return;
    if (!confirm("Drop the previous secret now? Webhooks signed with the old key will fail.")) return;
    const type = channel.provider === "meta_cloud" ? "meta_cloud" : "evolution";
    await webhookOpsApi.finalizeRotation(currentWorkspace.id, channel.id, type);
    alert("Previous secret removed");
  }

  return (
    <div>
      <p className="mb-3 text-sm text-muted">
        Rotate a channel credential with a grace window: both the old and the new secrets are accepted until the
        window ends, then the old one is dropped.
      </p>
      <div className="overflow-hidden rounded-lg border border-border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-surface-2 text-xs uppercase text-muted">
            <tr>
              <th className="px-3 py-2 text-left">Channel</th>
              <th className="px-3 py-2 text-left">Provider</th>
              <th className="px-3 py-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {channels.map((c) => (
              <tr key={c.id} className="border-t border-border">
                <td className="px-3 py-2 font-medium text-slate-900">{c.displayName}</td>
                <td className="px-3 py-2 font-mono text-xs">{c.provider ?? "—"}</td>
                <td className="px-3 py-2 text-right">
                  <button
                    className="text-xs text-primary hover:underline"
                    onClick={() => {
                      setPicked(c);
                      setRotateOpen(true);
                    }}
                  >
                    Rotate
                  </button>
                  <button
                    className="ml-3 text-xs text-muted hover:text-danger"
                    onClick={() => finalize(c)}
                  >
                    Finalize
                  </button>
                </td>
              </tr>
            ))}
            {channels.length === 0 && (
              <tr>
                <td colSpan={3} className="px-3 py-8 text-center text-sm text-muted">
                  No channels.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <RotateModal
        open={rotateOpen}
        onClose={() => setRotateOpen(false)}
        workspaceId={currentWorkspace?.id ?? ""}
        channel={picked}
      />
    </div>
  );
}

function RotateModal({
  open,
  onClose,
  workspaceId,
  channel,
}: {
  open: boolean;
  onClose: () => void;
  workspaceId: string;
  channel: { id: string; displayName: string; provider?: string | null } | null;
}) {
  const [graceHours, setGraceHours] = useState(24);
  const [payloadJson, setPayloadJson] = useState("{}");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!channel) return null;
  const credType = channel.provider === "meta_cloud" ? "meta_cloud" : "evolution";

  async function submit() {
    setError("");
    let payload: Record<string, unknown>;
    try {
      payload = JSON.parse(payloadJson);
    } catch {
      setError("Invalid JSON");
      return;
    }
    setLoading(true);
    try {
      await webhookOpsApi.rotateCredential(workspaceId, channel!.id, {
        credential_type: credType,
        payload,
        grace_hours: graceHours,
      });
      onClose();
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(detail ?? "Failed to rotate");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={`Rotate ${channel.displayName}`}>
      <div className="flex flex-col gap-3">
        <p className="text-xs text-muted">
          Provide the new credential JSON. Example for {credType}:
          <code className="ml-1 font-mono">
            {credType === "meta_cloud"
              ? `{"app_secret":"new_secret","access_token":"..."}`
              : `{"webhook_secret":"new","evolution_api_key":"...","evolution_base_url":"..."}`}
          </code>
        </p>
        <div className="flex flex-col gap-1.5">
          <Label>New payload (JSON)</Label>
          <textarea
            value={payloadJson}
            onChange={(e) => setPayloadJson(e.target.value)}
            rows={6}
            className="w-full rounded-md border border-border bg-white px-3 py-2 font-mono text-xs"
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Grace period (hours)</Label>
          <Input
            type="number"
            min={1}
            max={168}
            value={graceHours}
            onChange={(e) => setGraceHours(Number(e.target.value))}
          />
        </div>
        {error && <p className="text-sm text-danger">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button variant="outline" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={submit} loading={loading}>
            Rotate
          </Button>
        </div>
      </div>
    </Modal>
  );
}
