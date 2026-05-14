"use client";
import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { Avatar } from "@/components/ui/avatar";
import { messagesApi } from "@/lib/api";
import { useConversationStore } from "@/stores/conversation-store";
import type { Message } from "@/types/conversation";
import { format } from "date-fns";
import { FileIcon, ImageIcon, FileAudioIcon, FileVideoIcon } from "lucide-react";

interface Props {
  workspaceId: string;
  conversationId: string;
}

export function MessageThread({ workspaceId, conversationId }: Props) {
  const { messages, setMessages, clearUnread } = useConversationStore();
  const convMessages = messages[conversationId] ?? [];
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesApi
      .list(workspaceId, conversationId, { page_size: 100 })
      .then((r) => {
        const msgs = (r.data.items ?? []).reverse() as Message[];
        setMessages(conversationId, msgs);
      });
    messagesApi.markRead(workspaceId, conversationId);
    clearUnread(conversationId);
  }, [conversationId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [convMessages.length]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-3">
      {convMessages.map((msg) => (
        <MessageBubble key={msg.id} msg={msg} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}

function MessageBubble({ msg }: { msg: Message }) {
  const isAgent = msg.senderType === "agent";
  const isNote = msg.type === "internal_note";
  const isSystem = msg.type === "activity" || msg.senderType === "system";

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <span className="text-xs text-muted bg-surface-3 rounded-full px-3 py-1">{msg.content}</span>
      </div>
    );
  }

  return (
    <div className={cn("flex items-end gap-2", isAgent ? "flex-row-reverse" : "flex-row")}>
      {!isAgent && <Avatar name={msg.senderName} size="sm" />}
      <div className={cn("max-w-[70%] flex flex-col gap-0.5", isAgent ? "items-end" : "items-start")}>
        <div
          className={cn(
            "rounded-2xl px-3.5 py-2 text-sm leading-snug",
            isNote
              ? "bg-amber-50 border border-amber-200 text-amber-900"
              : isAgent
              ? "bg-primary text-white rounded-br-sm"
              : "bg-white border border-border text-slate-900 rounded-bl-sm"
          )}
        >
          {isNote && <p className="text-[10px] font-semibold mb-1 text-amber-600">INTERNAL NOTE</p>}
          {msg.content && <p className="whitespace-pre-wrap">{msg.content}</p>}
          {msg.attachments?.map((att, i) => (
            <AttachmentPreview key={i} attachment={att} />
          ))}
        </div>
        <span className="text-[10px] text-muted px-1">
          {format(new Date(msg.createdAt), "HH:mm")}
        </span>
      </div>
    </div>
  );
}

function AttachmentPreview({ attachment }: { attachment: { mimeType?: string; url?: string; name?: string } }) {
  const { mimeType, url, name } = attachment;
  if (mimeType?.startsWith("image/") && url) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img src={url} alt={name} className="mt-1 rounded-lg max-w-[240px] max-h-[180px] object-cover" />
    );
  }
  const Icon = mimeType?.startsWith("audio/")
    ? FileAudioIcon
    : mimeType?.startsWith("video/")
    ? FileVideoIcon
    : mimeType?.startsWith("image/")
    ? ImageIcon
    : FileIcon;
  return (
    <a
      href={url}
      target="_blank"
      rel="noreferrer"
      className="mt-1 flex items-center gap-2 text-xs underline opacity-80"
    >
      <Icon className="h-4 w-4" />
      {name ?? "Attachment"}
    </a>
  );
}
