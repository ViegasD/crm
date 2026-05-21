"use client";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { conversationsApi } from "@/lib/api";
import { useConversationStore } from "@/stores/conversation-store";
import type { Conversation } from "@/types/conversation";
import { CheckCheck } from "lucide-react";

interface Props {
  workspaceId: string;
  conversation: Conversation;
}

export function ConversationHeader({ workspaceId, conversation }: Props) {
  const { upsertConversation } = useConversationStore();
  const [resolving, setResolving] = useState(false);

  async function resolve() {
    setResolving(true);
    try {
      const r = await conversationsApi.update(workspaceId, conversation.id, { status: "resolved" });
      upsertConversation(r.data as Conversation);
    } finally {
      setResolving(false);
    }
  }

  async function reopen() {
    const r = await conversationsApi.update(workspaceId, conversation.id, { status: "open" });
    upsertConversation(r.data as Conversation);
  }

  const isResolved = conversation.status === "resolved";
  const displayName = conversation.contactName ?? conversation.contactPhone ?? "Unknown";

  return (
    <div className="flex items-center justify-between border-b border-border bg-white px-4 py-2.5 shrink-0">
      <div className="flex items-center gap-2">
        <span className="font-semibold text-slate-900">{displayName}</span>
        <Badge status={conversation.status}>{conversation.status}</Badge>
        {conversation.slaStatus && conversation.slaStatus !== "ok" && (
          <Badge status={conversation.slaStatus}>SLA {conversation.slaStatus}</Badge>
        )}
      </div>
      <div className="flex items-center gap-2">
        {isResolved ? (
          <Button variant="outline" size="sm" onClick={reopen}>Reopen</Button>
        ) : (
          <Button size="sm" loading={resolving} onClick={resolve}>
            <CheckCheck className="h-3.5 w-3.5" /> Resolve
          </Button>
        )}
      </div>
    </div>
  );
}
