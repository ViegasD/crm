"use client";
/**
 * Settings tab: Reopen / new-protocol policy.
 *
 * Lets workspace admins decide what happens when a contact sends a new
 * message to a conversation that was already resolved:
 *
 *   - "window": reopen if within N hours of resolved_at (default 24h),
 *     otherwise create a brand-new protocol
 *   - "always_reopen": always reopen the last conversation (Chatwoot-style)
 *   - "always_new": always create a new protocol/conversation (Opa-style)
 *
 * Per-sector overrides are supported below the workspace default.
 */
import { useEffect, useMemo, useState } from "react";
import { Save, Trash2 } from "lucide-react";

import { useAuthStore } from "@/stores/auth-store";
import { conversationPoliciesApi, sectorsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";

type ReopenMode = "window" | "always_reopen" | "always_new";

interface PolicyRow {
  id: string;
  workspace_id: string;
  sector_id: string | null;
  reopen_mode: ReopenMode;
  reopen_window_hours: number;
  inherit_assignee_on_new: boolean;
}

interface Sector {
  id: string;
  name: string;
}

export function ConversationPolicyTab() {
  const { currentWorkspace } = useAuthStore();
  const wsId = currentWorkspace?.id;
  const [rows, setRows] = useState<PolicyRow[]>([]);
  const [sectors, setSectors] = useState<Sector[]>([]);
  const [loading, setLoading] = useState(false);
  const [savingFor, setSavingFor] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function reload() {
    if (!wsId) return;
    setLoading(true);
    try {
      const [pol, sec] = await Promise.all([
        conversationPoliciesApi.list(wsId),
        sectorsApi.list(wsId),
      ]);
      setRows((pol.data ?? []) as PolicyRow[]);
      setSectors((sec.data ?? []) as Sector[]);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wsId]);

  const workspaceDefault = useMemo(
    () =>
      rows.find((r) => r.sector_id === null) ?? {
        id: "__draft_ws",
        workspace_id: wsId ?? "",
        sector_id: null,
        reopen_mode: "window" as ReopenMode,
        reopen_window_hours: 24,
        inherit_assignee_on_new: false,
      },
    [rows, wsId],
  );
  const sectorRows = useMemo(
    () => rows.filter((r) => r.sector_id !== null),
    [rows],
  );

  async function save(row: Pick<PolicyRow, "sector_id" | "reopen_mode" | "reopen_window_hours" | "inherit_assignee_on_new">) {
    if (!wsId) return;
    const key = row.sector_id ?? "__ws";
    setSavingFor(key);
    setErr(null);
    try {
      await conversationPoliciesApi.upsert(wsId, {
        sector_id: row.sector_id,
        reopen_mode: row.reopen_mode,
        reopen_window_hours: row.reopen_window_hours,
        inherit_assignee_on_new: row.inherit_assignee_on_new,
      });
      await reload();
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setSavingFor(null);
    }
  }

  async function remove(id: string) {
    if (!wsId) return;
    await conversationPoliciesApi.delete(wsId, id);
    await reload();
  }

  const sectorsWithoutOverride = sectors.filter(
    (s) => !sectorRows.some((r) => r.sector_id === s.id),
  );

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-base font-semibold text-slate-900">Reopen / new-protocol policy</h2>
        <p className="text-xs text-muted">
          Decide what happens when a contact sends a new message after their last
          conversation was already resolved. The workspace default applies unless a
          sector defines its own override.
        </p>
      </div>

      {err && <p className="text-xs text-danger">{err}</p>}

      <PolicyEditor
        title="Workspace default"
        sectors={sectors}
        row={workspaceDefault}
        showSectorPicker={false}
        onSave={(r) => save({ ...r, sector_id: null })}
        saving={savingFor === "__ws"}
      />

      <div>
        <h3 className="mb-2 text-sm font-semibold text-slate-900">Per-sector overrides</h3>
        <div className="flex flex-col gap-3">
          {sectorRows.map((r) => (
            <PolicyEditor
              key={r.id}
              title={sectorName(sectors, r.sector_id)}
              sectors={sectors}
              row={r}
              showSectorPicker={false}
              onSave={(updated) => save({ ...updated, sector_id: r.sector_id })}
              onDelete={() => remove(r.id)}
              saving={savingFor === r.sector_id}
            />
          ))}
          {sectorsWithoutOverride.length > 0 && (
            <PolicyEditor
              title="New sector override"
              sectors={sectorsWithoutOverride}
              row={{
                id: "__draft",
                workspace_id: wsId ?? "",
                sector_id: sectorsWithoutOverride[0]?.id ?? null,
                reopen_mode: "window",
                reopen_window_hours: 24,
                inherit_assignee_on_new: false,
              }}
              showSectorPicker
              onSave={save}
              saving={false}
            />
          )}
          {sectorRows.length === 0 && sectorsWithoutOverride.length === 0 && (
            <p className="text-xs text-muted">No sectors available.</p>
          )}
        </div>
      </div>
      {loading && <p className="text-xs text-muted">Loading…</p>}
    </div>
  );
}

function sectorName(sectors: Sector[], id: string | null): string {
  if (!id) return "Workspace default";
  return sectors.find((s) => s.id === id)?.name ?? id;
}

function PolicyEditor({
  title,
  sectors,
  row,
  showSectorPicker,
  onSave,
  onDelete,
  saving,
}: {
  title: string;
  sectors: Sector[];
  row: PolicyRow;
  showSectorPicker: boolean;
  onSave: (row: PolicyRow) => void;
  onDelete?: () => void;
  saving: boolean;
}) {
  const [local, setLocal] = useState<PolicyRow>(row);
  useEffect(() => setLocal(row), [row]);

  return (
    <div className="rounded-lg border border-border bg-white p-4">
      <div className="mb-3 flex items-center justify-between">
        <h4 className="text-sm font-semibold text-slate-900">{title}</h4>
        {onDelete && (
          <button
            onClick={onDelete}
            className="text-muted hover:text-danger"
            aria-label="Remove override"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        )}
      </div>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {showSectorPicker && (
          <label className="text-xs">
            <span className="text-muted">Sector</span>
            <select
              value={local.sector_id ?? ""}
              onChange={(e) =>
                setLocal((l) => ({ ...l, sector_id: e.target.value || null }))
              }
              className="mt-1 h-9 w-full rounded-md border border-border bg-white px-2"
            >
              {sectors.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </label>
        )}
        <label className="text-xs">
          <span className="text-muted">Mode</span>
          <select
            value={local.reopen_mode}
            onChange={(e) =>
              setLocal((l) => ({ ...l, reopen_mode: e.target.value as ReopenMode }))
            }
            className="mt-1 h-9 w-full rounded-md border border-border bg-white px-2"
          >
            <option value="window">Reopen within window (then new protocol)</option>
            <option value="always_reopen">Always reopen last conversation</option>
            <option value="always_new">Always create a new protocol</option>
          </select>
        </label>
        <label className="text-xs">
          <span className="text-muted">Window (hours)</span>
          <input
            type="number"
            min={0}
            max={720}
            disabled={local.reopen_mode !== "window"}
            value={local.reopen_window_hours}
            onChange={(e) =>
              setLocal((l) => ({ ...l, reopen_window_hours: Number(e.target.value) }))
            }
            className="mt-1 h-9 w-full rounded-md border border-border bg-white px-2 disabled:bg-slate-50 disabled:text-muted"
          />
        </label>
        <label className="flex items-center gap-2 text-xs">
          <input
            type="checkbox"
            checked={local.inherit_assignee_on_new}
            onChange={(e) =>
              setLocal((l) => ({ ...l, inherit_assignee_on_new: e.target.checked }))
            }
          />
          <span>
            Inherit the previous assignee when a brand-new protocol is created
          </span>
        </label>
      </div>
      <div className="mt-4 flex justify-end">
        <Button size="sm" onClick={() => onSave(local)} disabled={saving}>
          <Save className="mr-1.5 h-3.5 w-3.5" /> {saving ? "Saving…" : "Save"}
        </Button>
      </div>
    </div>
  );
}
