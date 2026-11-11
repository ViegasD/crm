"use client";
/**
 * Contact timeline modal — Stage 3 final task.
 *
 * Centered modal that renders every prior atendimento (conversation/protocol)
 * of a contact in a vertical chronological line, Opa Suite-style. Each
 * protocol shows its header (id + opened-at) above a channel icon hung on the
 * central line, then the conversation's messages and key events rendered as
 * chat bubbles on either side of the line (customer ↔ agent).
 *
 * Two complementary widgets in the side panel:
 *   - "Timeline" button → this modal (cross-protocol visual history)
 *   - "Log" panel       → the inline list of operational events (assigns,
 *                         transfers, labels…) for the *current* conversation
 */
import { useEffect, useMemo, useState } from "react";
import {
  X,
  Loader2,
  RefreshCw,
  MessageCircle,
  Activity,
  ShieldCheck,
  Star,
  Tag,
  Users,
  UserPlus,
  RotateCcw,
  CheckCircle2,
  Send,
} from "lucide-react";

import { contactsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";

type TimelineItem =
  | {
      kind: "message";
      ts: string;
      id: string;
      direction: "inbound" | "outbound";
      sender_type: string | null;
      sender_id: string | null;
      type: string | null;
      content: string | null;
      attachments: unknown[];
    }
  | {
      kind: "event";
      ts: string;
      id: string;
      type: string;
      actor_id: string | null;
      actor_type: string | null;
      payload: Record<string, unknown>;
    };

interface TimelineConversation {
  id: string;
  channel_account_id: string;
  sector_id: string | null;
  assignee_id: string | null;
  status: string | null;
  priority: string | null;
  is_active: boolean;
  opened_at: string | null;
  resolved_at: string | null;
  resolve_note: string | null;
  items: TimelineItem[];
}

interface TimelineResponse {
  contact_id: string;
  conversations: TimelineConversation[];
}

interface Props {
  workspaceId: string;
  contactId: string;
  contactName?: string;
  activeConversationId?: string;
  onClose: () => void;
}

export function ContactTimelineDrawer({
  workspaceId,
  contactId,
  contactName,
  activeConversationId,
  onClose,
}: Props) {
  const [data, setData] = useState<TimelineResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [channelFilter, setChannelFilter] = useState<string>("");

  async function reload() {
    setLoading(true);
    setErr(null);
    try {
      const r = await contactsApi.timeline(workspaceId, contactId, {
        active_conversation_id: activeConversationId,
        channel_account_id: channelFilter || undefined,
      });
      setData(r.data as TimelineResponse);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId, contactId, activeConversationId, channelFilter]);

  const channels = useMemo(() => {
    const set = new Set<string>();
    data?.conversations.forEach((c) => set.add(c.channel_account_id));
    return Array.from(set);
  }, [data]);

  // Newest first → oldest last is more useful when scrolling history;
  // the central line keeps the same shape either way.
  const conversations = useMemo(
    () => (data?.conversations ?? []).slice().sort((a, b) => {
      const at = a.opened_at ?? "";
      const bt = b.opened_at ?? "";
      return bt.localeCompare(at);
    }),
    [data],
  );

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      role="dialog"
      aria-modal="true"
      onClick={onClose}
    >
      <div
        className="relative flex h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between border-b border-border bg-slate-50 px-5 py-3">
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-900">
              Timeline
            </h2>
            <p className="text-xs text-muted">
              {contactName
                ? `Atendimentos com ${contactName}`
                : "Histórico de atendimentos do contato"}
              {data ? ` · ${data.conversations.length} protocolos` : ""}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="icon"
              variant="ghost"
              onClick={reload}
              aria-label="Recarregar"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
            </Button>
            <Button size="icon" variant="ghost" onClick={onClose} aria-label="Fechar">
              <X className="h-4 w-4" />
            </Button>
          </div>
        </header>

        {channels.length > 1 && (
          <div className="border-b border-border bg-white px-5 py-2">
            <label className="flex items-center gap-2 text-xs text-muted">
              Canal:
              <select
                value={channelFilter}
                onChange={(e) => setChannelFilter(e.target.value)}
                className="h-7 rounded-md border border-border bg-white px-2"
              >
                <option value="">Todos</option>
                {channels.map((c) => (
                  <option key={c} value={c}>
                    {c.slice(0, 8)}…
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}

        <div className="relative min-h-0 flex-1 overflow-y-auto bg-slate-50">
          {err && <p className="p-5 text-xs text-danger">{err}</p>}
          {!err && !loading && conversations.length === 0 && (
            <p className="p-10 text-center text-sm text-muted">
              Sem histórico anterior para este contato.
            </p>
          )}

          {conversations.length > 0 && (
            <div className="relative mx-auto max-w-3xl px-6 py-8">
              {/* Central vertical line */}
              <div
                aria-hidden
                className="absolute left-1/2 top-0 bottom-0 -translate-x-1/2 border-l-2 border-dashed border-primary/40"
              />
              <ol className="relative flex flex-col gap-10">
                {conversations.map((conv) => (
                  <ProtocolBlock key={conv.id} conv={conv} />
                ))}
              </ol>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ProtocolBlock({ conv }: { conv: TimelineConversation }) {
  const messages = conv.items.filter(
    (i): i is Extract<TimelineItem, { kind: "message" }> => i.kind === "message",
  );
  const significantEvents = conv.items.filter(
    (i): i is Extract<TimelineItem, { kind: "event" }> =>
      i.kind === "event" &&
      i.type !== "message_inbound" &&
      i.type !== "message_outbound",
  );

  // Merge messages + significant events back together, sorted by ts
  const merged = [...messages, ...significantEvents].sort((a, b) =>
    (a.ts ?? "").localeCompare(b.ts ?? ""),
  );

  return (
    <li className="relative">
      {/* Protocol header — sits on top, hugs the line via a channel-icon node */}
      <div className="relative mb-4 flex flex-col items-center">
        <div
          className={`rounded-lg border px-4 py-2 text-center shadow-sm ${
            conv.is_active
              ? "border-primary bg-primary/5"
              : "border-border bg-white"
          }`}
        >
          <div className="text-sm font-semibold text-slate-900">
            {protocolLabel(conv)}
          </div>
          <div className="text-[11px] text-muted">
            {formatTs(conv.opened_at)}
            {conv.is_active && (
              <span className="ml-2 rounded-full bg-primary px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white">
                Atual
              </span>
            )}
          </div>
        </div>
        {/* Channel icon node on the line */}
        <div className="relative -mb-3 mt-2 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500 text-white shadow-lg ring-4 ring-slate-50">
          <MessageCircle className="h-5 w-5" />
        </div>
      </div>

      <ol className="flex flex-col gap-3">
        {merged.map((item) =>
          item.kind === "message" ? (
            <MessageBubble key={`m:${item.id}`} item={item} />
          ) : (
            <EventBubble key={`e:${item.id}`} item={item} />
          ),
        )}
        {merged.length === 0 && (
          <li className="text-center text-xs text-muted">
            Nenhuma atividade registrada neste protocolo.
          </li>
        )}
      </ol>

      {/* Resolved footer */}
      {conv.resolved_at && (
        <div className="mt-4 flex flex-col items-center">
          <div className="flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-[11px] font-medium text-emerald-700">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Resolvido — {formatTs(conv.resolved_at)}
            {conv.resolve_note ? ` · "${conv.resolve_note}"` : ""}
          </div>
        </div>
      )}
    </li>
  );
}

function MessageBubble({
  item,
}: {
  item: Extract<TimelineItem, { kind: "message" }>;
}) {
  const isOutbound = item.direction === "outbound";
  const side = isOutbound ? "left" : "right"; // agent on left, customer on right
  const bubbleColor = isOutbound
    ? "bg-primary text-white"
    : "bg-white text-slate-800 border border-border";
  return (
    <li
      className={`grid grid-cols-[1fr_auto_1fr] items-start gap-2 ${
        side === "left" ? "" : ""
      }`}
    >
      {side === "left" ? (
        <>
          <div className="flex justify-end">
            <Bubble color={bubbleColor}>
              {item.content || <em className="opacity-70">[mídia]</em>}
              <BubbleFooter
                who={authorLabel(item)}
                ts={item.ts}
                light={isOutbound}
              />
            </Bubble>
          </div>
          <div aria-hidden />
          <div />
        </>
      ) : (
        <>
          <div />
          <div aria-hidden />
          <div className="flex justify-start">
            <Bubble color={bubbleColor}>
              {item.content || <em className="opacity-70">[mídia]</em>}
              <BubbleFooter who={authorLabel(item)} ts={item.ts} />
            </Bubble>
          </div>
        </>
      )}
    </li>
  );
}

function EventBubble({
  item,
}: {
  item: Extract<TimelineItem, { kind: "event" }>;
}) {
  const meta = describeEvent(item);
  if (!meta) return null;
  return (
    <li className="flex flex-col items-center">
      <div className="flex items-center gap-2 rounded-full border border-border bg-white px-3 py-1 text-[11px] text-slate-700 shadow-sm">
        <meta.Icon className="h-3.5 w-3.5 text-slate-500" />
        <span>{meta.label}</span>
        <span className="text-muted">· {formatTs(item.ts)}</span>
      </div>
    </li>
  );
}

function Bubble({
  children,
  color,
}: {
  children: React.ReactNode;
  color: string;
}) {
  return (
    <div
      className={`max-w-[88%] rounded-2xl px-3 py-2 text-xs leading-relaxed shadow-sm ${color}`}
    >
      {children}
    </div>
  );
}

function BubbleFooter({
  who,
  ts,
  light,
}: {
  who: string;
  ts: string;
  light?: boolean;
}) {
  return (
    <p className={`mt-1 text-[10px] ${light ? "text-white/70" : "text-muted"}`}>
      {who} · {formatTs(ts)}
    </p>
  );
}

function authorLabel(item: Extract<TimelineItem, { kind: "message" }>): string {
  if (item.direction === "inbound") return "Cliente";
  if (item.sender_type === "agent") return "Agente";
  if (item.sender_type === "bot") return "Bot";
  return "Sistema";
}

function describeEvent(
  item: Extract<TimelineItem, { kind: "event" }>,
): { Icon: typeof Activity; label: string } | null {
  const p = item.payload ?? {};
  switch (item.type) {
    case "opened":
      return { Icon: Activity, label: "Atendimento aberto" };
    case "resolved":
      return { Icon: CheckCircle2, label: "Resolvido" };
    case "reopened":
      return { Icon: RotateCcw, label: "Reaberto manualmente" };
    case "auto_reopened":
      return {
        Icon: RotateCcw,
        label: `Reaberto automaticamente (${(p.policy_mode as string) ?? "janela"})`,
      };
    case "auto_resolved":
      return { Icon: CheckCircle2, label: "Resolvido por inatividade" };
    case "new_protocol_created":
      return { Icon: ShieldCheck, label: "Novo protocolo aberto" };
    case "assigned":
      return { Icon: UserPlus, label: "Atribuído" };
    case "unassigned":
      return { Icon: UserPlus, label: "Atribuição removida" };
    case "transferred":
      return {
        Icon: Users,
        label: `Transferido${p.note ? ` — "${p.note}"` : ""}`,
      };
    case "label_added":
      return {
        Icon: Tag,
        label: `Etiqueta adicionada${p.label_name ? `: ${p.label_name}` : ""}`,
      };
    case "label_removed":
      return { Icon: Tag, label: "Etiqueta removida" };
    case "note_added":
      return { Icon: Activity, label: "Nota interna" };
    case "mention":
      return {
        Icon: UserPlus,
        label: `Menção a ${p.mentioned_user_name ?? "alguém"}`,
      };
    case "template_sent":
      return {
        Icon: Send,
        label: `Template enviado${p.template_name ? `: ${p.template_name}` : ""}`,
      };
    case "sla_at_risk":
    case "sla_violated":
    case "sla_escalated":
      return {
        Icon: Activity,
        label: `SLA: ${item.type.replace("sla_", "").replace("_", " ")}`,
      };
    case "csat_submitted":
      return { Icon: Star, label: "Avaliação CSAT recebida" };
    default:
      return { Icon: Activity, label: item.type.replace(/_/g, " ") };
  }
}

function protocolLabel(conv: TimelineConversation): string {
  // Fallback while Stage 2.1 protocol_number isn't wired: use a short id.
  // Once Stage 2.1 lands, swap this for conv.protocol_display.
  return `Protocolo ${conv.id.slice(0, 8).toUpperCase()}`;
}

function formatTs(ts: string | null): string {
  if (!ts) return "";
  try {
    return new Date(ts).toLocaleString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return ts;
  }
}
