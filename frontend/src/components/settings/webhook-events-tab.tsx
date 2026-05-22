"use client";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { webhookEventsApi } from "@/lib/api";
import type { WebhookEvent, WebhookEventDetail, WebhookEventStatus } from "@/types/conversation";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { AlertTriangle, CheckCircle2, Clock, RefreshCw, XCircle } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

const STATUS_COLORS: Record<WebhookEventStatus, string> = {
  received: "bg-blue-100 text-blue-700",
  processing: "bg-amber-100 text-amber-700",
  processed: "bg-green-100 text-green-700",
  failed: "bg-orange-100 text-orange-700",
  ignored: "bg-slate-100 text-slate-600",
  dead_letter: "bg-red-100 text-red-700",
};

const STATUS_ICONS: Record<WebhookEventStatus, React.ReactNode> = {
  received: <Clock className="h-3 w-3" />,
  processing: <RefreshCw className="h-3 w-3 animate-spin" />,
  processed: <CheckCircle2 className="h-3 w-3" />,
  failed: <AlertTriangle className="h-3 w-3" />,
  ignored: <XCircle className="h-3 w-3" />,
  dead_letter: <AlertTriangle className="h-3 w-3" />,
};

const STATUSES: (WebhookEventStatus | "all")[] = [
  "all",
  "received",
  "failed",
  "processed",
  "dead_letter",
  "ignored",
];

export function WebhookEventsTab() {
  const { currentWorkspace } = useAuthStore();
  const [items, setItems] = useState<WebhookEvent[]>([]);
  const [stats, setStats] = useState<Record<string, number>>({});
  const [status, setStatus] = useState<WebhookEventStatus | "all">("all");
  const [provider, setProvider] = useState("");
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState<WebhookEventDetail | null>(null);
  const [retryingId, setRetryingId] = useState<string | null>(null);

  async function refresh() {
    if (!currentWorkspace) return;
    setLoading(true);
    try {
      const [list, st] = await Promise.all([
        webhookEventsApi.list(currentWorkspace.id, {
          status: status === "all" ? undefined : status,
          provider: provider || undefined,
          page_size: 100,
        }),
        webhookEventsApi.stats(currentWorkspace.id),
      ]);
      setItems(list.data?.items ?? []);
      setStats(st.data ?? {});
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [currentWorkspace?.id, status, provider]); // eslint-disable-line react-hooks/exhaustive-deps

  async function openDetail(id: string) {
    if (!currentWorkspace) return;
    const r = await webhookEventsApi.get(currentWorkspace.id, id);
    setDetail(r.data as WebhookEventDetail);
  }

  async function retry(id: string) {
    if (!currentWorkspace) return;
    setRetryingId(id);
    try {
      const r = await webhookEventsApi.retry(currentWorkspace.id, id);
      if (!r.data?.success) {
        alert(`Retry failed: ${r.data?.error ?? "unknown error"}`);
      }
      refresh();
      if (detail?.id === id) {
        const fresh = await webhookEventsApi.get(currentWorkspace.id, id);
        setDetail(fresh.data as WebhookEventDetail);
      }
    } finally {
      setRetryingId(null);
    }
  }

  return (
    <div className="max-w-5xl">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-slate-900">Webhook events</h2>
          <p className="text-sm text-muted">
            Durable log of every webhook received. Failed events retry automatically with exponential
            backoff; dead-lettered events need a manual replay.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={refresh}>
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </Button>
      </div>

      <div className="mb-3 grid grid-cols-6 gap-2">
        {STATUSES.filter((s) => s !== "all").map((s) => (
          <div
            key={s}
            className={`rounded-lg border border-border bg-white px-3 py-2 ${
              status === s ? "ring-2 ring-primary" : ""
            }`}
            onClick={() => setStatus(s)}
            role="button"
          >
            <div className={`mb-1 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${STATUS_COLORS[s as WebhookEventStatus]}`}>
              {STATUS_ICONS[s as WebhookEventStatus]} {s}
            </div>
            <div className="text-xl font-semibold text-slate-900">{stats[s] ?? 0}</div>
          </div>
        ))}
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-1">
        {STATUSES.map((s) => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
              status === s ? "bg-primary text-white" : "text-muted hover:text-slate-900"
            }`}
          >
            {s}
          </button>
        ))}
        <select
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
          className="h-7 rounded-md border border-border bg-white px-2 text-xs"
        >
          <option value="">All providers</option>
          <option value="meta_cloud">meta_cloud</option>
          <option value="evolution">evolution</option>
        </select>
      </div>

      {loading && <p className="text-sm text-muted">Loading…</p>}

      <div className="overflow-hidden rounded-lg border border-border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-surface-2 text-xs uppercase text-muted">
            <tr>
              <th className="px-3 py-2 text-left">Status</th>
              <th className="px-3 py-2 text-left">Provider</th>
              <th className="px-3 py-2 text-left">Attempts</th>
              <th className="px-3 py-2 text-left">Next retry</th>
              <th className="px-3 py-2 text-left">Last error</th>
              <th className="px-3 py-2 text-left">Received</th>
              <th className="px-3 py-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((e) => (
              <tr key={e.id} className="border-t border-border">
                <td className="px-3 py-2">
                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${STATUS_COLORS[e.status]}`}
                  >
                    {STATUS_ICONS[e.status]} {e.status}
                  </span>
                </td>
                <td className="px-3 py-2 font-mono text-xs">{e.provider}</td>
                <td className="px-3 py-2 text-xs">
                  {e.attempts}/{e.maxAttempts}
                </td>
                <td className="px-3 py-2 text-xs text-muted">
                  {e.nextRetryAt ? formatDistanceToNow(new Date(e.nextRetryAt), { addSuffix: true }) : "—"}
                </td>
                <td className="max-w-xs truncate px-3 py-2 text-xs text-muted" title={e.errorMessage ?? ""}>
                  {e.errorMessage ?? "—"}
                </td>
                <td className="px-3 py-2 text-xs text-muted">
                  {formatDistanceToNow(new Date(e.createdAt), { addSuffix: true })}
                </td>
                <td className="px-3 py-2 text-right">
                  <div className="flex justify-end gap-1">
                    <button className="text-xs text-primary hover:underline" onClick={() => openDetail(e.id)}>
                      View
                    </button>
                    {(e.status === "failed" || e.status === "dead_letter") && (
                      <button
                        className="text-xs text-primary hover:underline"
                        disabled={retryingId === e.id}
                        onClick={() => retry(e.id)}
                      >
                        {retryingId === e.id ? "Retrying…" : "Retry"}
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {!loading && items.length === 0 && (
              <tr>
                <td colSpan={7} className="px-3 py-8 text-center text-sm text-muted">
                  No webhook events with this filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <DetailModal event={detail} onClose={() => setDetail(null)} onRetry={(id) => retry(id)} retrying={retryingId} />
    </div>
  );
}

function DetailModal({
  event,
  onClose,
  onRetry,
  retrying,
}: {
  event: WebhookEventDetail | null;
  onClose: () => void;
  onRetry: (id: string) => void;
  retrying: string | null;
}) {
  if (!event) return null;
  return (
    <Modal open={!!event} onClose={onClose} title={`Webhook event ${event.id.slice(0, 8)}`} size="lg">
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <div className="text-[11px] uppercase text-muted">Status</div>
            <div className="font-medium">{event.status}</div>
          </div>
          <div>
            <div className="text-[11px] uppercase text-muted">Provider</div>
            <div className="font-mono">{event.provider}</div>
          </div>
          <div>
            <div className="text-[11px] uppercase text-muted">Attempts</div>
            <div className="font-medium">
              {event.attempts} / {event.maxAttempts}
            </div>
          </div>
          <div>
            <div className="text-[11px] uppercase text-muted">Next retry</div>
            <div className="text-xs">{event.nextRetryAt ? new Date(event.nextRetryAt).toLocaleString() : "—"}</div>
          </div>
          <div>
            <div className="text-[11px] uppercase text-muted">Received</div>
            <div className="text-xs">{new Date(event.createdAt).toLocaleString()}</div>
          </div>
          <div>
            <div className="text-[11px] uppercase text-muted">Processed</div>
            <div className="text-xs">{event.processedAt ? new Date(event.processedAt).toLocaleString() : "—"}</div>
          </div>
        </div>
        {event.errorMessage && (
          <div>
            <div className="text-[11px] uppercase text-muted">Last error</div>
            <pre className="mt-1 max-h-32 overflow-auto rounded-md bg-red-50 p-2 text-[11px] text-red-900">
              {event.errorMessage}
            </pre>
          </div>
        )}
        <div>
          <div className="text-[11px] uppercase text-muted">Headers</div>
          <pre className="mt-1 max-h-40 overflow-auto rounded-md bg-surface-2 p-2 text-[11px]">
            {JSON.stringify(event.headers, null, 2)}
          </pre>
        </div>
        <div>
          <div className="text-[11px] uppercase text-muted">Payload</div>
          <pre className="mt-1 max-h-64 overflow-auto rounded-md bg-surface-2 p-2 text-[11px]">
            {JSON.stringify(event.payload, null, 2)}
          </pre>
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
          {(event.status === "failed" || event.status === "dead_letter") && (
            <Button onClick={() => onRetry(event.id)} loading={retrying === event.id}>
              <RefreshCw className="h-3.5 w-3.5" /> Retry now
            </Button>
          )}
        </div>
      </div>
    </Modal>
  );
}
