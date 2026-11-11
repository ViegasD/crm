"use client";
import { useEffect, useMemo, useState } from "react";
import { conversationsApi, workspacesApi } from "@/lib/api";
import type { ConversationEvent, ConversationParticipant, WorkspaceMember } from "@/types/conversation";
import { Button } from "@/components/ui/button";
import { Avatar } from "@/components/ui/avatar";
import { Clock3, FileText, GitBranch, Plus, Trash2, Users } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { ContactTimelineDrawer } from "./contact-timeline-drawer";

interface Props {
  workspaceId: string;
  conversationId: string;
  /**
   * Contact id of the current conversation. When provided the side panel shows
   * the "Timeline" button that opens the contact-wide timeline modal (every
   * past protocol/conversation for the same contact).
   */
  contactId?: string;
  contactName?: string;
}

export function ConversationSidePanel({
  workspaceId,
  conversationId,
  contactId,
  contactName,
}: Props) {
  const [timelineOpen, setTimelineOpen] = useState(false);
  const [logOpen, setLogOpen] = useState(true);
  const [events, setEvents] = useState<ConversationEvent[]>([]);
  const [participants, setParticipants] = useState<ConversationParticipant[]>([]);
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [pickerUserId, setPickerUserId] = useState("");

  useEffect(() => {
    conversationsApi.events(workspaceId, conversationId).then((r) => setEvents(r.data ?? []));
    conversationsApi.participants(workspaceId, conversationId).then((r) => setParticipants(r.data ?? []));
  }, [workspaceId, conversationId]);

  useEffect(() => {
    workspacesApi.listMembers(workspaceId).then((r) => setMembers(r.data ?? []));
  }, [workspaceId]);

  const participantUserIds = useMemo(
    () => new Set(participants.map((p) => p.userId)),
    [participants],
  );
  const availableMembers = useMemo(
    () => members.filter((m) => !participantUserIds.has(m.userId)),
    [members, participantUserIds],
  );

  async function addParticipant() {
    if (!pickerUserId) return;
    const r = await conversationsApi.addParticipant(workspaceId, conversationId, pickerUserId);
    setParticipants((prev) => {
      const filtered = prev.filter((p) => p.userId !== pickerUserId);
      return [...filtered, r.data as ConversationParticipant];
    });
    setPickerUserId("");
    // Refresh timeline so the new participant_added event shows up
    conversationsApi.events(workspaceId, conversationId).then((r) => setEvents(r.data ?? []));
  }

  async function removeParticipant(userId: string) {
    await conversationsApi.removeParticipant(workspaceId, conversationId, userId);
    setParticipants((prev) => prev.filter((p) => p.userId !== userId));
    conversationsApi.events(workspaceId, conversationId).then((r) => setEvents(r.data ?? []));
  }

  return (
    <aside className="hidden w-80 shrink-0 border-l border-border bg-white xl:flex xl:flex-col">
      <section className="border-b border-border p-4">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-900">
          <Users className="h-4 w-4" /> Participants
        </div>
        <div className="flex gap-2">
          <select
            value={pickerUserId}
            onChange={(e) => setPickerUserId(e.target.value)}
            className="h-8 flex-1 rounded-md border border-border bg-white px-2 text-xs"
          >
            <option value="">Select member…</option>
            {availableMembers.map((m) => (
              <option key={m.userId} value={m.userId}>
                {m.user?.name ?? m.userId}
              </option>
            ))}
          </select>
          <Button size="icon" onClick={addParticipant} disabled={!pickerUserId}>
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        <div className="mt-3 flex flex-col gap-2">
          {participants.map((participant) => (
            <div key={participant.id} className="flex items-center justify-between gap-2 text-xs text-slate-700">
              <div className="flex min-w-0 items-center gap-2">
                <Avatar name={participant.user?.name ?? participant.userId} size="sm" />
                <span className="truncate">{participant.user?.name ?? participant.userId}</span>
              </div>
              <button
                className="text-muted hover:text-danger"
                onClick={() => removeParticipant(participant.userId)}
                aria-label="Remove participant"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
          {participants.length === 0 && <p className="text-xs text-muted">No observers</p>}
        </div>
      </section>
      <section className="border-b border-border p-3">
        <div className="grid grid-cols-2 gap-2">
          {contactId && (
            <Button
              size="sm"
              variant="primary"
              onClick={() => setTimelineOpen(true)}
              className="w-full"
            >
              <GitBranch className="mr-1.5 h-3.5 w-3.5" /> Timeline
            </Button>
          )}
          <Button
            size="sm"
            variant={logOpen ? "secondary" : "outline"}
            onClick={() => setLogOpen((v) => !v)}
            className="w-full"
            aria-pressed={logOpen}
          >
            <FileText className="mr-1.5 h-3.5 w-3.5" /> Log
          </Button>
        </div>
      </section>
      {logOpen && (
        <section className="min-h-0 flex-1 overflow-y-auto p-4">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-900">
            <Clock3 className="h-4 w-4" /> Log da conversa
          </div>
          <Timeline events={events} members={members} />
        </section>
      )}
      {!logOpen && <div className="flex-1" />}
      {timelineOpen && contactId && (
        <ContactTimelineDrawer
          workspaceId={workspaceId}
          contactId={contactId}
          contactName={contactName}
          activeConversationId={conversationId}
          onClose={() => setTimelineOpen(false)}
        />
      )}
    </aside>
  );
}

function Timeline({ events, members }: { events: ConversationEvent[]; members: WorkspaceMember[] }) {
  const userById = useMemo(() => {
    const map = new Map<string, WorkspaceMember>();
    for (const m of members) map.set(m.userId, m);
    return map;
  }, [members]);

  if (events.length === 0) {
    return <p className="text-xs text-muted">No activity yet</p>;
  }

  const grouped = groupByDay(events);
  return (
    <div className="flex flex-col gap-4">
      {grouped.map(([day, dayEvents]) => (
        <div key={day} className="flex flex-col gap-3">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-muted">{day}</div>
          {dayEvents.map((event) => (
            <TimelineRow key={event.id} event={event} userById={userById} />
          ))}
        </div>
      ))}
    </div>
  );
}

function TimelineRow({
  event,
  userById,
}: {
  event: ConversationEvent;
  userById: Map<string, WorkspaceMember>;
}) {
  const actorName = event.actorName ?? (event.actorType === "system" ? "System" : "Someone");
  const label = describeEvent(event, userById);
  return (
    <div className="flex items-start gap-2 border-l border-border pl-3">
      <Avatar name={actorName} size="sm" />
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-slate-800">
          <span className="font-semibold">{actorName}</span> {label}
        </p>
        <p className="text-[11px] text-muted">
          {event.createdAt ? formatDistanceToNow(new Date(event.createdAt), { addSuffix: true }) : ""}
        </p>
      </div>
    </div>
  );
}

function describeEvent(event: ConversationEvent, userById: Map<string, WorkspaceMember>): string {
  const payload = (event.payload ?? {}) as Record<string, string | null | undefined>;
  const nameFor = (id: string | null | undefined): string | undefined =>
    id ? userById.get(id)?.user?.name ?? id : undefined;
  switch (event.type) {
    case "opened":
      return "opened the conversation";
    case "resolved":
      return "marked as resolved";
    case "reopened":
      return "reopened the conversation";
    case "assigned":
      return `assigned to ${nameFor(payload.to) ?? "an agent"}`;
    case "unassigned":
      return "removed the assignee";
    case "transferred": {
      const to = nameFor(payload.to_agent) ?? payload.to_sector ?? "another agent";
      return `transferred to ${to}${payload.note ? ` — “${payload.note}”` : ""}`;
    }
    case "label_added":
      return `added label “${payload.label_name ?? ""}”`;
    case "label_removed":
      return `removed label “${payload.label_name ?? ""}”`;
    case "note_added":
      return "added an internal note";
    case "mention":
      return `mentioned ${payload.mentioned_user_name ?? "someone"}`;
    case "participant_added":
      return `added ${nameFor(payload.user_id) ?? "an observer"} as observer`;
    case "participant_removed":
      return `removed ${nameFor(payload.user_id) ?? "an observer"} from observers`;
    case "bot_handed_off":
      return "handed off from bot";
    case "bot_took_over":
      return "bot took over";
    default:
      return event.type.replace(/_/g, " ");
  }
}

function groupByDay(events: ConversationEvent[]): [string, ConversationEvent[]][] {
  const map = new Map<string, ConversationEvent[]>();
  for (const event of events) {
    const day = new Date(event.createdAt).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
    if (!map.has(day)) map.set(day, []);
    map.get(day)!.push(event);
  }
  return Array.from(map.entries());
}
