"use client";
import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { Avatar } from "@/components/ui/avatar";
import { messagesApi } from "@/lib/api";
import { useConversationStore } from "@/stores/conversation-store";
import type { Attachment, Message, MessageType } from "@/types/conversation";
import { format } from "date-fns";
import { Download, FileAudioIcon, FileIcon, FileVideoIcon, ImageIcon, LoaderCircle } from "lucide-react";

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
  const statusLabel = getProviderStatusLabel(msg.providerStatus, msg.providerStatusError);

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
            <AttachmentPreview key={i} attachment={att} messageType={msg.type} tone={isAgent ? "agent" : "contact"} />
          ))}
        </div>
        <div className="px-1 text-[10px] text-muted flex items-center gap-2">
          <span>{format(new Date(msg.createdAt), "HH:mm")}</span>
          {isAgent && statusLabel && <span>{statusLabel}</span>}
        </div>
      </div>
    </div>
  );
}

function getProviderStatusLabel(status?: string | null, error?: string | null): string | null {
  switch (status) {
    case "queued":
      return "Queued";
    case "sent":
      return "Sent";
    case "delivered":
      return "Delivered";
    case "read":
      return "Read";
    case "failed":
      return error ? `Failed: ${error}` : "Failed";
    default:
      return null;
  }
}

function AttachmentPreview({ attachment, messageType, tone }: { attachment: Attachment; messageType: MessageType; tone: "agent" | "contact" }) {
  const { mimeType, url, name, ready } = attachment;
  const kind = getAttachmentKind(attachment, messageType);

  if (ready === false || !url) {
    const Icon = getAttachmentIcon(kind);
    return (
      <div
        className={cn(
          "mt-2 flex min-w-[220px] items-center gap-3 rounded-2xl border px-3 py-3 text-xs",
          tone === "agent"
            ? "border-white/20 bg-white/10 text-white"
            : "border-slate-200 bg-slate-50 text-slate-700"
        )}
      >
        <div
          className={cn(
            "flex h-10 w-10 items-center justify-center rounded-full",
            tone === "agent" ? "bg-white/15" : "bg-white"
          )}
        >
          <Icon className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium">{name ?? getAttachmentLabel(kind)}</p>
          <div className="mt-1 flex items-center gap-1.5 opacity-80">
            <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
            <span>Processing...</span>
          </div>
        </div>
      </div>
    );
  }

  if (kind === "image") {
    return (
      <div className="mt-2 overflow-hidden rounded-2xl border border-slate-200 bg-slate-50">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={url} alt={name ?? "Image attachment"} className="max-h-[260px] w-full max-w-[280px] object-cover" />
        {name && <div className="px-3 py-2 text-xs text-slate-600">{name}</div>}
      </div>
    );
  }

  if (kind === "sticker") {
    return (
      <div className="mt-2 inline-flex max-w-[180px] items-center justify-center rounded-2xl p-1">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={url} alt={name ?? "Sticker"} className="max-h-[160px] w-auto max-w-[160px] object-contain" />
      </div>
    );
  }

  if (kind === "audio") {
    return (
      <div className="mt-2 w-full min-w-[260px] max-w-[320px] rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3 text-slate-900">
        <div className="mb-2 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white shadow-sm">
            <FileAudioIcon className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{name ?? "Audio message"}</p>
            <p className="text-xs text-slate-500">Voice note</p>
          </div>
        </div>
        <audio controls preload="metadata" className="h-10 w-full max-w-full">
          <source src={url} type={mimeType} />
        </audio>
      </div>
    );
  }

  if (kind === "video") {
    return (
      <div className="mt-2 overflow-hidden rounded-2xl border border-slate-200 bg-slate-950">
        <video controls preload="metadata" className="max-h-[280px] w-full max-w-[320px] bg-black">
          <source src={url} type={mimeType} />
        </video>
        {name && <div className="px-3 py-2 text-xs text-slate-300">{name}</div>}
      </div>
    );
  }

  const Icon = getAttachmentIcon(kind);
  return (
    <a
      href={url}
      target="_blank"
      rel="noreferrer"
      className="mt-2 flex min-w-[240px] items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3 text-left text-slate-900 transition-colors hover:bg-slate-100"
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white shadow-sm">
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{name ?? "Attachment"}</p>
        <p className="text-xs text-slate-500">Open file</p>
      </div>
      <Download className="h-4 w-4 shrink-0 text-slate-500" />
    </a>
  );
}

function getAttachmentKind(attachment: Attachment, messageType: MessageType): "audio" | "video" | "image" | "sticker" | "file" {
  if (messageType === "sticker" || attachment.type === "sticker") return "sticker";
  const mimeType = attachment.mimeType;
  if (mimeType?.startsWith("audio/")) return "audio";
  if (mimeType?.startsWith("video/")) return "video";
  if (mimeType?.startsWith("image/")) return "image";
  return "file";
}

function getAttachmentIcon(kind: "audio" | "video" | "image" | "sticker" | "file") {
  switch (kind) {
    case "audio":
      return FileAudioIcon;
    case "video":
      return FileVideoIcon;
    case "sticker":
    case "image":
      return ImageIcon;
    default:
      return FileIcon;
  }
}

function getAttachmentLabel(kind: "audio" | "video" | "image" | "sticker" | "file") {
  switch (kind) {
    case "audio":
      return "Audio message";
    case "video":
      return "Video attachment";
    case "sticker":
      return "Sticker";
    case "image":
      return "Image attachment";
    default:
      return "Attachment";
  }
}
