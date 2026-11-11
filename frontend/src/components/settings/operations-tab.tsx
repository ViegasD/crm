"use client";
import { useEffect, useMemo, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { sectorsApi, slaApi, stage9Api, workspacesApi } from "@/lib/api";
import type {
  AgentPauseReason,
  AutoResolveRule,
  BusinessHoliday,
  BusinessHours,
  CsatSummary,
  ExternalWebhookSubscription,
  HeatmapData,
  IdleRule,
  NotificationChannel,
  NotificationKind,
  RoutingRule,
  SlaEscalationRule,
  SlaPolicy,
} from "@/types/sla";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { Input, Label, Textarea } from "@/components/ui/form";
import {
  Activity,
  AlarmClockOff,
  Bell,
  CalendarRange,
  CalendarX,
  GitFork,
  Globe,
  KeySquare,
  Plus,
  Repeat2,
  Smile,
  Trash2,
  TrendingUp,
} from "lucide-react";

type SubTab =
  | "routing"
  | "hours"
  | "holidays"
  | "autoresolve"
  | "pause"
  | "capacity"
  | "idle"
  | "escalations"
  | "notifications"
  | "outbound"
  | "csat"
  | "heatmap";

const SUBTABS: { v: SubTab; label: string; icon: React.ReactNode }[] = [
  { v: "routing", label: "Routing", icon: <GitFork className="h-3.5 w-3.5" /> },
  { v: "hours", label: "Business hours", icon: <CalendarRange className="h-3.5 w-3.5" /> },
  { v: "holidays", label: "Holidays", icon: <CalendarX className="h-3.5 w-3.5" /> },
  { v: "autoresolve", label: "Auto-resolve", icon: <Repeat2 className="h-3.5 w-3.5" /> },
  { v: "pause", label: "Pause reasons", icon: <AlarmClockOff className="h-3.5 w-3.5" /> },
  { v: "capacity", label: "Capacity", icon: <TrendingUp className="h-3.5 w-3.5" /> },
  { v: "idle", label: "Idle", icon: <Activity className="h-3.5 w-3.5" /> },
  { v: "escalations", label: "Escalations", icon: <KeySquare className="h-3.5 w-3.5" /> },
  { v: "notifications", label: "Notifications", icon: <Bell className="h-3.5 w-3.5" /> },
  { v: "outbound", label: "API webhooks", icon: <Globe className="h-3.5 w-3.5" /> },
  { v: "csat", label: "CSAT", icon: <Smile className="h-3.5 w-3.5" /> },
  { v: "heatmap", label: "Heatmap", icon: <TrendingUp className="h-3.5 w-3.5" /> },
];

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function OperationsTab() {
  const [sub, setSub] = useState<SubTab>("routing");
  return (
    <div className="max-w-6xl">
      <div className="mb-4 flex flex-wrap items-center gap-3 border-b border-border pb-2">
        {SUBTABS.map((s) => (
          <button
            key={s.v}
            onClick={() => setSub(s.v)}
            className={`flex items-center gap-1 text-xs font-medium ${
              sub === s.v ? "text-primary" : "text-muted hover:text-slate-900"
            }`}
          >
            {s.icon} {s.label}
          </button>
        ))}
      </div>
      {sub === "routing" && <RoutingPanel />}
      {sub === "hours" && <HoursPanel />}
      {sub === "holidays" && <HolidaysPanel />}
      {sub === "autoresolve" && <AutoResolvePanel />}
      {sub === "pause" && <PauseReasonsPanel />}
      {sub === "capacity" && <CapacityPanel />}
      {sub === "idle" && <IdlePanel />}
      {sub === "escalations" && <EscalationsPanel />}
      {sub === "notifications" && <NotificationsPanel />}
      {sub === "outbound" && <OutboundPanel />}
      {sub === "csat" && <CsatPanel />}
      {sub === "heatmap" && <HeatmapPanel />}
    </div>
  );
}

// ── Routing ────────────────────────────────────────────────────────────────

function RoutingPanel() {
  const { currentWorkspace } = useAuthStore();
  const [rules, setRules] = useState<RoutingRule[]>([]);
  const [sectors, setSectors] = useState<{ id: string; name: string }[]>([]);

  useEffect(() => {
    if (!currentWorkspace) return;
    slaApi.listRoutingRules(currentWorkspace.id).then((r) => setRules(r.data ?? []));
    sectorsApi.list(currentWorkspace.id).then((r) => setSectors(r.data ?? []));
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function save(rule: RoutingRule) {
    if (!currentWorkspace) return;
    await slaApi.upsertRoutingRule(currentWorkspace.id, {
      sector_id: rule.sectorId,
      strategy: rule.strategy,
      tiebreaker: rule.tiebreaker,
      sticky_hours: rule.stickyHours,
      auto_reassign_minutes: rule.autoReassignMinutes,
      reopen_window_hours: rule.reopenWindowHours,
    });
    const r = await slaApi.listRoutingRules(currentWorkspace.id);
    setRules(r.data ?? []);
  }

  const rows = useMemo(() => {
    const map = new Map<string | null, RoutingRule>();
    for (const r of rules) map.set(r.sectorId ?? null, r);
    const defaults: RoutingRule[] = [
      {
        id: "default",
        workspaceId: currentWorkspace?.id ?? "",
        sectorId: null,
        strategy: map.get(null)?.strategy ?? "least_busy",
        tiebreaker: map.get(null)?.tiebreaker ?? "oldest_idle",
        stickyHours: map.get(null)?.stickyHours ?? 24,
        autoReassignMinutes: map.get(null)?.autoReassignMinutes ?? 10,
        reopenWindowHours: map.get(null)?.reopenWindowHours ?? 24,
      },
    ];
    for (const sector of sectors) {
      const existing = map.get(sector.id);
      defaults.push(
        existing ?? {
          id: `sector-${sector.id}`,
          workspaceId: currentWorkspace?.id ?? "",
          sectorId: sector.id,
          strategy: "least_busy",
          tiebreaker: "oldest_idle",
          stickyHours: 24,
          autoReassignMinutes: 10,
          reopenWindowHours: 24,
        },
      );
    }
    return defaults;
  }, [rules, sectors, currentWorkspace?.id]);

  return (
    <div>
      <p className="mb-3 text-sm text-muted">
        Routing strategy per sector. Workspace default applies when no sector-specific rule exists.
      </p>
      <div className="overflow-hidden rounded-lg border border-border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-surface-2 text-xs uppercase text-muted">
            <tr>
              <th className="px-3 py-2 text-left">Scope</th>
              <th className="px-3 py-2 text-left">Strategy</th>
              <th className="px-3 py-2 text-left">Tiebreaker</th>
              <th className="px-3 py-2 text-left">Sticky h</th>
              <th className="px-3 py-2 text-left">Auto-reassign m</th>
              <th className="px-3 py-2 text-left">Reopen window h</th>
              <th className="px-3 py-2 text-right">Save</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((rule) => (
              <RoutingRow
                key={rule.sectorId ?? "default"}
                rule={rule}
                sectorName={
                  rule.sectorId ? sectors.find((s) => s.id === rule.sectorId)?.name ?? "Sector" : "Workspace default"
                }
                onSave={save}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RoutingRow({
  rule,
  sectorName,
  onSave,
}: {
  rule: RoutingRule;
  sectorName: string;
  onSave: (rule: RoutingRule) => Promise<void>;
}) {
  const [draft, setDraft] = useState(rule);
  useEffect(() => setDraft(rule), [rule]);
  return (
    <tr className="border-t border-border">
      <td className="px-3 py-2 font-medium text-slate-900">{sectorName}</td>
      <td className="px-3 py-2">
        <select
          value={draft.strategy}
          onChange={(e) => setDraft({ ...draft, strategy: e.target.value as RoutingRule["strategy"] })}
          className="h-8 rounded-md border border-border bg-white px-2 text-xs"
        >
          <option value="least_busy">least_busy</option>
          <option value="round_robin">round_robin</option>
          <option value="sticky_agent">sticky_agent</option>
          <option value="manual">manual</option>
        </select>
      </td>
      <td className="px-3 py-2">
        <select
          value={draft.tiebreaker}
          onChange={(e) => setDraft({ ...draft, tiebreaker: e.target.value })}
          className="h-8 rounded-md border border-border bg-white px-2 text-xs"
        >
          <option value="oldest_idle">oldest_idle</option>
          <option value="lowest_load">lowest_load</option>
          <option value="alphabetical">alphabetical</option>
        </select>
      </td>
      <td className="px-3 py-2">
        <Input
          type="number"
          value={draft.stickyHours}
          onChange={(e) => setDraft({ ...draft, stickyHours: Number(e.target.value) })}
          className="h-8 w-20 text-xs"
        />
      </td>
      <td className="px-3 py-2">
        <Input
          type="number"
          value={draft.autoReassignMinutes}
          onChange={(e) => setDraft({ ...draft, autoReassignMinutes: Number(e.target.value) })}
          className="h-8 w-20 text-xs"
        />
      </td>
      <td className="px-3 py-2">
        <Input
          type="number"
          value={draft.reopenWindowHours}
          onChange={(e) => setDraft({ ...draft, reopenWindowHours: Number(e.target.value) })}
          className="h-8 w-20 text-xs"
        />
      </td>
      <td className="px-3 py-2 text-right">
        <Button size="sm" onClick={() => onSave(draft)}>
          Save
        </Button>
      </td>
    </tr>
  );
}

// ── Business hours grid editor ─────────────────────────────────────────────

function HoursPanel() {
  const { currentWorkspace } = useAuthStore();
  const [sectors, setSectors] = useState<{ id: string; name: string }[]>([]);
  const [sectorId, setSectorId] = useState<string>("");
  const [grid, setGrid] = useState<Record<number, { start: string; end: string; active: boolean }>>({});
  const [timezone, setTimezone] = useState("America/Sao_Paulo");

  async function load(sId: string | null) {
    if (!currentWorkspace) return;
    const r = await slaApi.listBusinessHours(currentWorkspace.id, { sector_id: sId ?? undefined });
    const next: Record<number, { start: string; end: string; active: boolean }> = {};
    for (let d = 0; d < 7; d++) {
      next[d] = { start: "09:00", end: "18:00", active: false };
    }
    for (const row of r.data as BusinessHours[]) {
      if ((sId ?? null) !== (row.sectorId ?? null)) continue;
      next[row.weekday] = {
        start: minutesToHHMM(row.startMinute),
        end: minutesToHHMM(row.endMinute),
        active: row.active,
      };
      if (row.timezone) setTimezone(row.timezone);
    }
    setGrid(next);
  }

  useEffect(() => {
    if (!currentWorkspace) return;
    sectorsApi.list(currentWorkspace.id).then((r) => setSectors(r.data ?? []));
    load(null);
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    load(sectorId || null);
  }, [sectorId]); // eslint-disable-line react-hooks/exhaustive-deps

  async function save() {
    if (!currentWorkspace) return;
    const rows: Array<Record<string, unknown>> = [];
    for (let d = 0; d < 7; d++) {
      const slot = grid[d];
      if (!slot?.active) continue;
      rows.push({
        weekday: d,
        start_minute: hhmmToMinutes(slot.start),
        end_minute: hhmmToMinutes(slot.end),
        timezone,
        active: true,
      });
    }
    await slaApi.replaceBusinessHours(currentWorkspace.id, rows, sectorId || null);
    alert("Saved");
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm text-muted">
          Weekly business hours grid. Used by SLA when <code>business_hours_only=true</code>.
        </p>
        <div className="flex items-center gap-2">
          <select
            value={sectorId}
            onChange={(e) => setSectorId(e.target.value)}
            className="h-8 rounded-md border border-border bg-white px-2 text-xs"
          >
            <option value="">Workspace default</option>
            {sectors.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <Input
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            className="h-8 w-44 text-xs"
            placeholder="Timezone"
          />
          <Button size="sm" onClick={save}>
            Save grid
          </Button>
        </div>
      </div>
      <div className="grid grid-cols-7 gap-2">
        {WEEKDAYS.map((label, d) => {
          const slot = grid[d] ?? { start: "09:00", end: "18:00", active: false };
          return (
            <div key={d} className="rounded-lg border border-border bg-white p-3">
              <div className="mb-2 flex items-center justify-between text-xs font-semibold text-slate-900">
                <span>{label}</span>
                <input
                  type="checkbox"
                  checked={slot.active}
                  onChange={(e) =>
                    setGrid({ ...grid, [d]: { ...slot, active: e.target.checked } })
                  }
                />
              </div>
              <Input
                type="time"
                value={slot.start}
                onChange={(e) =>
                  setGrid({ ...grid, [d]: { ...slot, start: e.target.value } })
                }
                className="mb-1 h-8 text-xs"
                disabled={!slot.active}
              />
              <Input
                type="time"
                value={slot.end}
                onChange={(e) =>
                  setGrid({ ...grid, [d]: { ...slot, end: e.target.value } })
                }
                className="h-8 text-xs"
                disabled={!slot.active}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}

function minutesToHHMM(m: number): string {
  const h = Math.floor(m / 60).toString().padStart(2, "0");
  const mm = (m % 60).toString().padStart(2, "0");
  return `${h}:${mm}`;
}
function hhmmToMinutes(s: string): number {
  const [h, m] = s.split(":").map((x) => parseInt(x, 10));
  return (h || 0) * 60 + (m || 0);
}

// ── Holidays ───────────────────────────────────────────────────────────────

function HolidaysPanel() {
  const { currentWorkspace } = useAuthStore();
  const [items, setItems] = useState<BusinessHoliday[]>([]);
  const [addOpen, setAddOpen] = useState(false);
  const [draft, setDraft] = useState({ label: "", holiday_date: "", treat_as: "closed" });

  async function refresh() {
    if (!currentWorkspace) return;
    const r = await stage9Api.listHolidays(currentWorkspace.id);
    setItems(r.data ?? []);
  }
  useEffect(() => {
    refresh();
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function create() {
    if (!currentWorkspace) return;
    if (!draft.label || !draft.holiday_date) return;
    await stage9Api.createHoliday(currentWorkspace.id, draft);
    setAddOpen(false);
    setDraft({ label: "", holiday_date: "", treat_as: "closed" });
    refresh();
  }

  async function remove(id: string) {
    if (!currentWorkspace) return;
    if (!confirm("Delete this holiday?")) return;
    await stage9Api.deleteHoliday(currentWorkspace.id, id);
    setItems((prev) => prev.filter((h) => h.id !== id));
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm text-muted">Days excluded from business-hours calculations.</p>
        <Button size="sm" onClick={() => setAddOpen(true)}>
          <Plus className="h-3.5 w-3.5" /> Add
        </Button>
      </div>
      <div className="flex flex-col gap-2">
        {items.map((h) => (
          <div key={h.id} className="flex items-center justify-between rounded-lg border border-border bg-white p-3">
            <div>
              <p className="font-medium text-slate-900">{h.label}</p>
              <p className="text-xs text-muted">
                {h.holidayDate} · {h.treatAs}
              </p>
            </div>
            <button className="text-muted hover:text-danger" onClick={() => remove(h.id)}>
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
        {items.length === 0 && (
          <div className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted">
            No holidays configured.
          </div>
        )}
      </div>
      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="New holiday">
        <div className="flex flex-col gap-3">
          <div>
            <Label>Date</Label>
            <Input
              type="date"
              value={draft.holiday_date}
              onChange={(e) => setDraft({ ...draft, holiday_date: e.target.value })}
            />
          </div>
          <div>
            <Label>Label</Label>
            <Input
              value={draft.label}
              onChange={(e) => setDraft({ ...draft, label: e.target.value })}
              placeholder="Natal"
            />
          </div>
          <div>
            <Label>Treat as</Label>
            <select
              value={draft.treat_as}
              onChange={(e) => setDraft({ ...draft, treat_as: e.target.value })}
              className="h-9 w-full rounded-md border border-border bg-white px-2 text-sm"
            >
              <option value="closed">closed</option>
              <option value="half_day">half day</option>
              <option value="custom">custom</option>
            </select>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setAddOpen(false)}>
              Cancel
            </Button>
            <Button onClick={create}>Save</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

// ── Auto-resolve ───────────────────────────────────────────────────────────

function AutoResolvePanel() {
  const { currentWorkspace } = useAuthStore();
  const [items, setItems] = useState<AutoResolveRule[]>([]);
  const [sectors, setSectors] = useState<{ id: string; name: string }[]>([]);
  const [addOpen, setAddOpen] = useState(false);
  const [draft, setDraft] = useState({
    sector_id: "",
    inactivity_hours: 72,
    status_from: ["pending", "open"],
    active: false,
  });

  async function refresh() {
    if (!currentWorkspace) return;
    const r = await slaApi.listAutoResolveRules(currentWorkspace.id);
    setItems(r.data ?? []);
  }
  useEffect(() => {
    if (!currentWorkspace) return;
    refresh();
    sectorsApi.list(currentWorkspace.id).then((r) => setSectors(r.data ?? []));
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function create() {
    if (!currentWorkspace) return;
    await slaApi.createAutoResolveRule(currentWorkspace.id, {
      sector_id: draft.sector_id || null,
      inactivity_hours: draft.inactivity_hours,
      status_from: draft.status_from,
      active: draft.active,
    });
    setAddOpen(false);
    refresh();
  }

  async function toggle(rule: AutoResolveRule) {
    if (!currentWorkspace) return;
    await slaApi.updateAutoResolveRule(currentWorkspace.id, rule.id, { active: !rule.active });
    refresh();
  }

  async function remove(rule: AutoResolveRule) {
    if (!currentWorkspace) return;
    if (!confirm("Delete this rule?")) return;
    await slaApi.deleteAutoResolveRule(currentWorkspace.id, rule.id);
    refresh();
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm text-muted">
          Conversations with no inbound activity for N hours auto-transition to resolved (worker runs every 15 min).
        </p>
        <Button size="sm" onClick={() => setAddOpen(true)}>
          <Plus className="h-3.5 w-3.5" /> New rule
        </Button>
      </div>
      <div className="flex flex-col gap-2">
        {items.map((rule) => (
          <div key={rule.id} className="flex items-center justify-between rounded-lg border border-border bg-white p-3">
            <div>
              <p className="font-medium text-slate-900">
                {rule.sectorId
                  ? sectors.find((s) => s.id === rule.sectorId)?.name ?? "Sector"
                  : "Workspace default"}
              </p>
              <p className="text-xs text-muted">
                After {rule.inactivityHours}h with status in {rule.statusFrom.join("/")} → {rule.statusTo}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-1 text-xs">
                <input type="checkbox" checked={rule.active} onChange={() => toggle(rule)} /> active
              </label>
              <button className="text-muted hover:text-danger" onClick={() => remove(rule)}>
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
        {items.length === 0 && (
          <div className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted">
            No rules.
          </div>
        )}
      </div>
      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="New auto-resolve rule">
        <div className="flex flex-col gap-3">
          <div>
            <Label>Sector (blank = workspace default)</Label>
            <select
              value={draft.sector_id}
              onChange={(e) => setDraft({ ...draft, sector_id: e.target.value })}
              className="h-9 w-full rounded-md border border-border bg-white px-2 text-sm"
            >
              <option value="">Workspace default</option>
              {sectors.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Inactivity hours</Label>
            <Input
              type="number"
              value={draft.inactivity_hours}
              onChange={(e) => setDraft({ ...draft, inactivity_hours: Number(e.target.value) })}
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={draft.active}
              onChange={(e) => setDraft({ ...draft, active: e.target.checked })}
            />
            Active immediately
          </label>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setAddOpen(false)}>
              Cancel
            </Button>
            <Button onClick={create}>Create</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

// ── Pause reasons CRUD ─────────────────────────────────────────────────────

function PauseReasonsPanel() {
  const { currentWorkspace } = useAuthStore();
  const [items, setItems] = useState<AgentPauseReason[]>([]);
  const [draft, setDraft] = useState("");

  async function refresh() {
    if (!currentWorkspace) return;
    const r = await slaApi.listPauseReasons(currentWorkspace.id);
    setItems(r.data ?? []);
  }
  useEffect(() => {
    refresh();
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function create() {
    if (!currentWorkspace || !draft.trim()) return;
    await slaApi.createPauseReason(currentWorkspace.id, { label: draft });
    setDraft("");
    refresh();
  }

  async function toggle(item: AgentPauseReason) {
    if (!currentWorkspace) return;
    await slaApi.updatePauseReason(currentWorkspace.id, item.id, { active: !item.active });
    refresh();
  }

  async function remove(item: AgentPauseReason) {
    if (!currentWorkspace) return;
    if (!confirm("Delete this reason?")) return;
    await slaApi.deletePauseReason(currentWorkspace.id, item.id);
    refresh();
  }

  return (
    <div className="max-w-2xl">
      <p className="mb-3 text-sm text-muted">Reasons agents pick when entering on_break.</p>
      <div className="mb-3 flex items-end gap-2">
        <div className="flex-1">
          <Label>New reason</Label>
          <Input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Lunch" />
        </div>
        <Button onClick={create}>Add</Button>
      </div>
      <div className="flex flex-col gap-2">
        {items.map((r) => (
          <div key={r.id} className="flex items-center justify-between rounded-lg border border-border bg-white p-3">
            <span className="text-sm">
              {r.label} {!r.active && <span className="ml-1 text-xs text-muted">(inactive)</span>}
            </span>
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-1 text-xs">
                <input type="checkbox" checked={r.active} onChange={() => toggle(r)} />
                active
              </label>
              <button className="text-muted hover:text-danger" onClick={() => remove(r)}>
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Capacity (weighted) ────────────────────────────────────────────────────

interface MemberRow {
  userId: string;
  name: string;
  email: string;
}
interface CapacityRow {
  userId: string;
  maxConversations: number;
  maxWeight: number;
  priorityWeights: Record<string, number>;
}

function CapacityPanel() {
  const { currentWorkspace } = useAuthStore();
  const [members, setMembers] = useState<MemberRow[]>([]);
  const [caps, setCaps] = useState<Record<string, CapacityRow>>({});
  const [saving, setSaving] = useState<string | null>(null);

  async function refresh() {
    if (!currentWorkspace) return;
    const [m, c] = await Promise.all([
      workspacesApi.listMembers(currentWorkspace.id),
      slaApi.listCapacity(currentWorkspace.id),
    ]);
    setMembers(
      (m.data ?? []).map((row: { userId: string; user?: { name?: string; email?: string } }) => ({
        userId: row.userId,
        name: row.user?.name ?? row.userId,
        email: row.user?.email ?? "",
      })),
    );
    const map: Record<string, CapacityRow> = {};
    for (const row of c.data ?? []) {
      map[row.userId] = {
        userId: row.userId,
        maxConversations: row.maxConversations,
        maxWeight: row.maxWeight,
        priorityWeights: row.priorityWeights ?? {},
      };
    }
    setCaps(map);
  }

  useEffect(() => {
    refresh();
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function save(userId: string, draft: CapacityRow) {
    if (!currentWorkspace) return;
    setSaving(userId);
    try {
      await slaApi.setCapacity(currentWorkspace.id, {
        user_id: userId,
        max_conversations: draft.maxConversations,
        max_weight: draft.maxWeight,
        priority_weights: draft.priorityWeights,
      });
      await refresh();
    } finally {
      setSaving(null);
    }
  }

  return (
    <div>
      <p className="mb-3 text-sm text-muted">
        Capacity per agent. Conversations are weighted (urgent=2, high=1.5, medium=1, low=0.75 by default; pending
        × 0.5). `max_weight` is the soft ceiling for routing.
      </p>
      <div className="overflow-hidden rounded-lg border border-border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-surface-2 text-xs uppercase text-muted">
            <tr>
              <th className="px-3 py-2 text-left">Agent</th>
              <th className="px-3 py-2 text-left">Max conversations</th>
              <th className="px-3 py-2 text-left">Max weight</th>
              <th className="px-3 py-2 text-left">Priority weights (JSON)</th>
              <th className="px-3 py-2 text-right">Save</th>
            </tr>
          </thead>
          <tbody>
            {members.map((m) => {
              const c = caps[m.userId] ?? {
                userId: m.userId,
                maxConversations: 10,
                maxWeight: 10,
                priorityWeights: { low: 0.75, medium: 1, high: 1.5, urgent: 2 },
              };
              return <CapacityRowEdit key={m.userId} member={m} initial={c} onSave={save} saving={saving === m.userId} />;
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CapacityRowEdit({
  member,
  initial,
  onSave,
  saving,
}: {
  member: MemberRow;
  initial: CapacityRow;
  onSave: (userId: string, draft: CapacityRow) => Promise<void>;
  saving: boolean;
}) {
  const [draft, setDraft] = useState(initial);
  const [weightsJson, setWeightsJson] = useState(JSON.stringify(initial.priorityWeights, null, 0));
  useEffect(() => {
    setDraft(initial);
    setWeightsJson(JSON.stringify(initial.priorityWeights, null, 0));
  }, [initial]);
  return (
    <tr className="border-t border-border">
      <td className="px-3 py-2">
        <div className="font-medium text-slate-900">{member.name}</div>
        <div className="text-[11px] text-muted">{member.email}</div>
      </td>
      <td className="px-3 py-2">
        <Input
          type="number"
          value={draft.maxConversations}
          onChange={(e) => setDraft({ ...draft, maxConversations: Number(e.target.value) })}
          className="h-8 w-20 text-xs"
        />
      </td>
      <td className="px-3 py-2">
        <Input
          type="number"
          step="0.5"
          value={draft.maxWeight}
          onChange={(e) => setDraft({ ...draft, maxWeight: Number(e.target.value) })}
          className="h-8 w-20 text-xs"
        />
      </td>
      <td className="px-3 py-2">
        <Input
          value={weightsJson}
          onChange={(e) => setWeightsJson(e.target.value)}
          className="h-8 w-full font-mono text-[11px]"
        />
      </td>
      <td className="px-3 py-2 text-right">
        <Button
          size="sm"
          loading={saving}
          onClick={() => {
            try {
              const parsed = JSON.parse(weightsJson || "{}");
              onSave(member.userId, { ...draft, priorityWeights: parsed });
            } catch {
              alert("Priority weights must be valid JSON");
            }
          }}
        >
          Save
        </Button>
      </td>
    </tr>
  );
}

// ── Idle ───────────────────────────────────────────────────────────────────

function IdlePanel() {
  const { currentWorkspace } = useAuthStore();
  const [rule, setRule] = useState<IdleRule | null>(null);
  const [draft, setDraft] = useState({ idle_minutes: 10, offline_minutes: 30, active: true });

  useEffect(() => {
    if (!currentWorkspace) return;
    stage9Api.getIdleRule(currentWorkspace.id).then((r) => {
      const d = r.data as IdleRule | null;
      setRule(d);
      if (d) setDraft({ idle_minutes: d.idleMinutes, offline_minutes: d.offlineMinutes, active: d.active });
    });
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function save() {
    if (!currentWorkspace) return;
    const r = await stage9Api.upsertIdleRule(currentWorkspace.id, draft);
    setRule(r.data as IdleRule);
  }

  return (
    <div className="max-w-md">
      <p className="mb-3 text-sm text-muted">
        Auto-flip agents to <code>away</code> after N inactive minutes, then to <code>offline</code> after M minutes.
      </p>
      <div className="flex flex-col gap-3 rounded-lg border border-border bg-white p-4">
        <div>
          <Label>Idle threshold (minutes)</Label>
          <Input
            type="number"
            value={draft.idle_minutes}
            onChange={(e) => setDraft({ ...draft, idle_minutes: Number(e.target.value) })}
          />
        </div>
        <div>
          <Label>Offline threshold (minutes)</Label>
          <Input
            type="number"
            value={draft.offline_minutes}
            onChange={(e) => setDraft({ ...draft, offline_minutes: Number(e.target.value) })}
          />
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={draft.active}
            onChange={(e) => setDraft({ ...draft, active: e.target.checked })}
          />
          Active
        </label>
        <Button onClick={save}>Save</Button>
        {rule && (
          <p className="text-[11px] text-muted">Last saved {new Date().toLocaleString()}.</p>
        )}
      </div>
    </div>
  );
}

// ── Escalations ────────────────────────────────────────────────────────────

function EscalationsPanel() {
  const { currentWorkspace } = useAuthStore();
  const [policies, setPolicies] = useState<SlaPolicy[]>([]);
  const [policyId, setPolicyId] = useState<string>("");
  const [draft, setDraft] = useState<SlaEscalationRule[]>([]);

  useEffect(() => {
    if (!currentWorkspace) return;
    slaApi.listPolicies(currentWorkspace.id).then((r) => {
      setPolicies(r.data ?? []);
      if ((r.data ?? []).length > 0) setPolicyId(r.data[0].id);
    });
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!currentWorkspace || !policyId) return;
    slaApi.listEscalations(currentWorkspace.id, policyId).then((r) => {
      setDraft(r.data ?? []);
    });
  }, [policyId, currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  function addLevel() {
    if (draft.length >= 3) return;
    setDraft([
      ...draft,
      {
        thresholdPct: 80 + draft.length * 30,
        action: "notify",
        targetRole: "supervisor",
        targetUserId: null,
        webhookUrl: null,
        position: draft.length,
        active: true,
      },
    ]);
  }
  function updateLevel(idx: number, patch: Partial<SlaEscalationRule>) {
    setDraft((prev) => {
      const copy = prev.slice();
      copy[idx] = { ...copy[idx], ...patch };
      return copy;
    });
  }
  function removeLevel(idx: number) {
    setDraft((prev) => prev.filter((_, i) => i !== idx));
  }
  async function save() {
    if (!currentWorkspace || !policyId) return;
    await slaApi.replaceEscalations(
      currentWorkspace.id,
      policyId,
      draft.map((r, i) => ({
        threshold_pct: r.thresholdPct,
        action: r.action,
        target_role: r.targetRole,
        target_user_id: r.targetUserId,
        webhook_url: r.webhookUrl,
        position: i,
        active: r.active,
      })),
    );
    const r = await slaApi.listEscalations(currentWorkspace.id, policyId);
    setDraft(r.data ?? []);
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <select
          value={policyId}
          onChange={(e) => setPolicyId(e.target.value)}
          className="h-9 rounded-md border border-border bg-white px-2 text-sm"
        >
          {policies.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <Button size="sm" variant="outline" onClick={addLevel} disabled={draft.length >= 3}>
          <Plus className="h-3.5 w-3.5" /> Add level
        </Button>
      </div>
      <div className="flex flex-col gap-2">
        {draft.map((rule, idx) => (
          <div key={idx} className="rounded-lg border border-border bg-white p-3">
            <div className="grid grid-cols-5 items-center gap-2">
              <div>
                <Label>Threshold %</Label>
                <Input
                  type="number"
                  value={rule.thresholdPct}
                  onChange={(e) => updateLevel(idx, { thresholdPct: Number(e.target.value) })}
                  className="h-8 text-xs"
                />
              </div>
              <div>
                <Label>Action</Label>
                <select
                  value={rule.action}
                  onChange={(e) => updateLevel(idx, { action: e.target.value as SlaEscalationRule["action"] })}
                  className="h-8 w-full rounded-md border border-border bg-white px-2 text-xs"
                >
                  <option value="notify">notify</option>
                  <option value="reassign">reassign</option>
                  <option value="webhook">webhook</option>
                </select>
              </div>
              <div>
                <Label>Target role</Label>
                <select
                  value={rule.targetRole ?? ""}
                  onChange={(e) => updateLevel(idx, { targetRole: e.target.value || null })}
                  className="h-8 w-full rounded-md border border-border bg-white px-2 text-xs"
                >
                  <option value="">—</option>
                  <option value="supervisor">supervisor</option>
                  <option value="admin">admin</option>
                </select>
              </div>
              <div>
                <Label>Webhook URL</Label>
                <Input
                  value={rule.webhookUrl ?? ""}
                  onChange={(e) => updateLevel(idx, { webhookUrl: e.target.value || null })}
                  className="h-8 text-xs"
                  placeholder="https://…"
                />
              </div>
              <div className="flex items-end justify-end">
                <button className="text-muted hover:text-danger" onClick={() => removeLevel(idx)}>
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
        {draft.length === 0 && (
          <div className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted">
            No escalation levels.
          </div>
        )}
      </div>
      <div className="mt-3">
        <Button onClick={save}>Save chain</Button>
      </div>
    </div>
  );
}

// ── Notifications ──────────────────────────────────────────────────────────

function NotificationsPanel() {
  const { currentWorkspace } = useAuthStore();
  const [items, setItems] = useState<NotificationChannel[]>([]);
  const [addOpen, setAddOpen] = useState(false);

  async function refresh() {
    if (!currentWorkspace) return;
    const r = await stage9Api.listNotificationChannels(currentWorkspace.id);
    setItems(r.data ?? []);
  }
  useEffect(() => {
    refresh();
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function remove(id: string) {
    if (!currentWorkspace) return;
    if (!confirm("Delete channel?")) return;
    await stage9Api.deleteNotificationChannel(currentWorkspace.id, id);
    refresh();
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm text-muted">
          Channels to dispatch internal notifications (sla.violated, mention, agent.idle, …).
        </p>
        <Button size="sm" onClick={() => setAddOpen(true)}>
          <Plus className="h-3.5 w-3.5" /> Add channel
        </Button>
      </div>
      <div className="flex flex-col gap-2">
        {items.map((c) => (
          <div key={c.id} className="flex items-start justify-between rounded-lg border border-border bg-white p-3">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <p className="font-medium text-slate-900">{c.name}</p>
                <span className="rounded-full bg-surface-3 px-2 py-0.5 text-[10px] font-semibold uppercase text-muted">
                  {c.kind}
                </span>
                {!c.active && (
                  <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] uppercase text-amber-700">
                    inactive
                  </span>
                )}
              </div>
              <p className="mt-1 text-[11px] text-muted">
                Events: {c.events.length ? c.events.join(", ") : "all"}
              </p>
            </div>
            <button className="text-muted hover:text-danger" onClick={() => remove(c.id)}>
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
        {items.length === 0 && (
          <div className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted">
            No channels.
          </div>
        )}
      </div>
      <NotificationChannelModal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        onCreated={() => {
          setAddOpen(false);
          refresh();
        }}
      />
    </div>
  );
}

function NotificationChannelModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}) {
  const { currentWorkspace } = useAuthStore();
  const [name, setName] = useState("");
  const [kind, setKind] = useState<NotificationKind>("inapp");
  const [configJson, setConfigJson] = useState("{}");
  const [eventsCsv, setEventsCsv] = useState("");
  const [active, setActive] = useState(true);
  const [error, setError] = useState("");

  async function submit() {
    setError("");
    if (!currentWorkspace || !name.trim()) {
      setError("Name required");
      return;
    }
    let config: Record<string, unknown> = {};
    try {
      config = JSON.parse(configJson || "{}");
    } catch {
      setError("Config must be valid JSON");
      return;
    }
    await stage9Api.createNotificationChannel(currentWorkspace.id, {
      name,
      kind,
      config,
      events: eventsCsv
        .split(",")
        .map((e) => e.trim())
        .filter(Boolean),
      active,
    });
    onCreated();
    setName("");
    setConfigJson("{}");
    setEventsCsv("");
  }

  const exampleConfig =
    kind === "email"
      ? '{"recipients":["ops@yourdomain.com"]}'
      : kind === "slack_webhook"
        ? '{"url":"https://hooks.slack.com/services/..."}'
        : kind === "webhook"
          ? '{"url":"https://example.com/notify"}'
          : "{}";

  return (
    <Modal open={open} onClose={onClose} title="New notification channel">
      <div className="flex flex-col gap-3">
        <div>
          <Label>Name</Label>
          <Input value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div>
          <Label>Kind</Label>
          <select
            value={kind}
            onChange={(e) => setKind(e.target.value as NotificationKind)}
            className="h-9 w-full rounded-md border border-border bg-white px-2 text-sm"
          >
            <option value="inapp">in-app</option>
            <option value="email">email</option>
            <option value="slack_webhook">slack webhook</option>
            <option value="webhook">webhook</option>
          </select>
        </div>
        <div>
          <Label>Config (JSON)</Label>
          <Textarea
            rows={3}
            value={configJson}
            onChange={(e) => setConfigJson(e.target.value)}
            className="font-mono text-xs"
            placeholder={exampleConfig}
          />
          <p className="mt-1 text-[10px] text-muted">Example: {exampleConfig}</p>
        </div>
        <div>
          <Label>Events (comma-separated, empty = all)</Label>
          <Input
            value={eventsCsv}
            onChange={(e) => setEventsCsv(e.target.value)}
            placeholder="sla.violated, sla.at_risk, mention"
          />
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} />
          Active
        </label>
        {error && <p className="text-sm text-danger">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={submit}>Create</Button>
        </div>
      </div>
    </Modal>
  );
}

// ── Outbound API webhooks ─────────────────────────────────────────────────

function OutboundPanel() {
  const { currentWorkspace } = useAuthStore();
  const [items, setItems] = useState<ExternalWebhookSubscription[]>([]);
  const [addOpen, setAddOpen] = useState(false);
  const [draft, setDraft] = useState({ name: "", url: "", events: "", secret: "" });

  async function refresh() {
    if (!currentWorkspace) return;
    const r = await stage9Api.listApiWebhooks(currentWorkspace.id);
    setItems(r.data ?? []);
  }
  useEffect(() => {
    refresh();
  }, [currentWorkspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function create() {
    if (!currentWorkspace) return;
    if (!draft.name.trim() || !draft.url.trim()) return;
    await stage9Api.createApiWebhook(currentWorkspace.id, {
      name: draft.name,
      url: draft.url,
      secret: draft.secret || null,
      events: draft.events
        .split(",")
        .map((e) => e.trim())
        .filter(Boolean),
      active: true,
    });
    setAddOpen(false);
    setDraft({ name: "", url: "", events: "", secret: "" });
    refresh();
  }

  async function remove(id: string) {
    if (!currentWorkspace) return;
    if (!confirm("Delete subscription?")) return;
    await stage9Api.deleteApiWebhook(currentWorkspace.id, id);
    refresh();
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm text-muted">
          External integrations subscribe to internal events. Payloads are signed with HMAC-SHA256 in{" "}
          <code>X-CRM-Signature</code>.
        </p>
        <Button size="sm" onClick={() => setAddOpen(true)}>
          <Plus className="h-3.5 w-3.5" /> Subscribe
        </Button>
      </div>
      <div className="flex flex-col gap-2">
        {items.map((s) => (
          <div key={s.id} className="flex items-start justify-between rounded-lg border border-border bg-white p-3">
            <div className="min-w-0 flex-1">
              <p className="font-medium text-slate-900">{s.name}</p>
              <p className="break-all font-mono text-[11px] text-muted">{s.url}</p>
              <p className="mt-1 text-[11px] text-muted">
                Events: {s.events.length ? s.events.join(", ") : "all"}
              </p>
            </div>
            <button className="text-muted hover:text-danger" onClick={() => remove(s.id)}>
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
        {items.length === 0 && (
          <div className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted">
            No subscriptions yet.
          </div>
        )}
      </div>
      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="New webhook subscription">
        <div className="flex flex-col gap-3">
          <div>
            <Label>Name</Label>
            <Input value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
          </div>
          <div>
            <Label>URL</Label>
            <Input value={draft.url} onChange={(e) => setDraft({ ...draft, url: e.target.value })} placeholder="https://…" />
          </div>
          <div>
            <Label>Secret (leave empty to auto-generate)</Label>
            <Input value={draft.secret} onChange={(e) => setDraft({ ...draft, secret: e.target.value })} />
          </div>
          <div>
            <Label>Events (comma-separated, empty = all)</Label>
            <Input
              value={draft.events}
              onChange={(e) => setDraft({ ...draft, events: e.target.value })}
              placeholder="sla.violated, conversation.resolved, message.received"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setAddOpen(false)}>
              Cancel
            </Button>
            <Button onClick={create}>Create</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

// ── CSAT ───────────────────────────────────────────────────────────────────

function CsatPanel() {
  const { currentWorkspace } = useAuthStore();
  const [data, setData] = useState<CsatSummary | null>(null);
  const [onlyResponded, setOnlyResponded] = useState(false);

  async function refresh() {
    if (!currentWorkspace) return;
    const r = await stage9Api.listCsat(currentWorkspace.id, { only_responded: onlyResponded });
    setData(r.data as CsatSummary);
  }
  useEffect(() => {
    refresh();
  }, [currentWorkspace?.id, onlyResponded]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <p className="text-sm text-muted">CSAT surveys dispatched on conversation resolve.</p>
          {data?.averageScore != null && (
            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700">
              avg {data.averageScore}/5
            </span>
          )}
        </div>
        <label className="flex items-center gap-1 text-xs">
          <input
            type="checkbox"
            checked={onlyResponded}
            onChange={(e) => setOnlyResponded(e.target.checked)}
          />
          Only responded
        </label>
      </div>
      <div className="overflow-hidden rounded-lg border border-border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-surface-2 text-xs uppercase text-muted">
            <tr>
              <th className="px-3 py-2 text-left">Conversation</th>
              <th className="px-3 py-2 text-left">Sent</th>
              <th className="px-3 py-2 text-left">Score</th>
              <th className="px-3 py-2 text-left">Feedback</th>
            </tr>
          </thead>
          <tbody>
            {(data?.items ?? []).map((item) => (
              <tr key={item.id} className="border-t border-border">
                <td className="px-3 py-2 font-mono text-xs">{item.conversationId.slice(0, 8)}</td>
                <td className="px-3 py-2 text-xs text-muted">{new Date(item.sentAt).toLocaleString()}</td>
                <td className="px-3 py-2">
                  {item.score != null ? (
                    <span
                      className={`rounded px-2 py-0.5 text-xs font-semibold ${
                        item.score >= 4
                          ? "bg-emerald-100 text-emerald-700"
                          : item.score >= 3
                            ? "bg-amber-100 text-amber-700"
                            : "bg-rose-100 text-rose-700"
                      }`}
                    >
                      {item.score}/5
                    </span>
                  ) : (
                    <span className="text-xs text-muted">pending</span>
                  )}
                </td>
                <td className="px-3 py-2 text-xs text-muted">{item.feedback ?? "—"}</td>
              </tr>
            ))}
            {(data?.items ?? []).length === 0 && (
              <tr>
                <td colSpan={4} className="px-3 py-8 text-center text-sm text-muted">
                  No surveys yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Heatmap ────────────────────────────────────────────────────────────────

function HeatmapPanel() {
  const { currentWorkspace } = useAuthStore();
  const [days, setDays] = useState(7);
  const [data, setData] = useState<HeatmapData | null>(null);

  useEffect(() => {
    if (!currentWorkspace) return;
    stage9Api.heatmap(currentWorkspace.id, days).then((r) => setData(r.data as HeatmapData));
  }, [currentWorkspace?.id, days]); // eslint-disable-line react-hooks/exhaustive-deps

  const grid = useMemo(() => {
    if (!data) return [];
    const byUser = new Map<string, { name: string; cells: Record<number, number> }>();
    for (const cell of data.cells) {
      const entry = byUser.get(cell.userId) ?? { name: cell.userName, cells: {} };
      entry.cells[cell.hour] = (entry.cells[cell.hour] ?? 0) + cell.minutesAssigned;
      byUser.set(cell.userId, entry);
    }
    return Array.from(byUser.entries()).map(([userId, e]) => ({ userId, ...e }));
  }, [data]);

  const maxMinutes = useMemo(() => {
    let max = 0;
    for (const row of grid) {
      for (const v of Object.values(row.cells)) if (v > max) max = v;
    }
    return max || 1;
  }, [grid]);

  function intensity(min: number): string {
    const pct = min / maxMinutes;
    if (pct === 0) return "bg-surface-2";
    if (pct < 0.25) return "bg-emerald-100";
    if (pct < 0.5) return "bg-emerald-300";
    if (pct < 0.75) return "bg-emerald-500";
    return "bg-emerald-700";
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm text-muted">Minutes assigned per agent × hour of day, over the last {days} days.</p>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="h-8 rounded-md border border-border bg-white px-2 text-xs"
        >
          <option value={1}>last 24h</option>
          <option value={7}>last 7d</option>
          <option value={30}>last 30d</option>
        </select>
      </div>
      <div className="overflow-x-auto rounded-lg border border-border bg-white p-2">
        <div className="min-w-[800px]">
          <div className="flex">
            <div className="w-32 shrink-0 text-[10px] text-muted">Agent / hour</div>
            {Array.from({ length: 24 }, (_, h) => (
              <div key={h} className="w-7 text-center text-[10px] text-muted">
                {h}
              </div>
            ))}
          </div>
          {grid.map((row) => (
            <div key={row.userId} className="mt-1 flex items-center">
              <div className="w-32 shrink-0 truncate text-xs">{row.name}</div>
              {Array.from({ length: 24 }, (_, h) => {
                const min = row.cells[h] ?? 0;
                return (
                  <div
                    key={h}
                    title={`${row.name} — ${h}h: ${min}min`}
                    className={`mx-px h-6 w-7 rounded ${intensity(min)}`}
                  />
                );
              })}
            </div>
          ))}
          {grid.length === 0 && (
            <p className="mt-4 text-center text-sm text-muted">No assignment data in this window.</p>
          )}
        </div>
      </div>
    </div>
  );
}
