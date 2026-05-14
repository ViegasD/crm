"use client";
import { useRef, useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/form";
import { messagesApi, mediaApi } from "@/lib/api";
import { useConversationStore } from "@/stores/conversation-store";
import type { Message } from "@/types/conversation";
import { Send, Paperclip, StickyNote } from "lucide-react";

interface Props {
  workspaceId: string;
  conversationId: string;
}

export function ReplyBox({ workspaceId, conversationId }: Props) {
  const [text, setText] = useState("");
  const [isNote, setIsNote] = useState(false);
  const [sending, setSending] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const { appendMessage } = useConversationStore();

  async function send() {
    if (!text.trim() && !sending) return;
    setSending(true);
    try {
      const r = await messagesApi.send(workspaceId, conversationId, {
        content: text,
        type: "text",
        is_note: isNote,
      });
      appendMessage(r.data as Message);
      setText("");
    } finally {
      setSending(false);
    }
  }

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const upload = await mediaApi.upload(workspaceId, file);
      const { key, url } = upload.data;
      const r = await messagesApi.send(workspaceId, conversationId, {
        type: file.type.startsWith("image/") ? "image" : file.type.startsWith("audio/") ? "audio" : "file",
        attachments: [{ key, url, name: file.name, mimeType: file.type }],
        is_note: isNote,
      });
      appendMessage(r.data as Message);
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <div
      className={cn(
        "border-t border-border bg-white px-3 py-2",
        isNote && "bg-amber-50 border-amber-200"
      )}
    >
      {/* Mode toggle */}
      <div className="flex gap-2 mb-1.5">
        <button
          onClick={() => setIsNote(false)}
          className={cn(
            "text-xs px-2 py-0.5 rounded-full font-medium transition-colors",
            !isNote ? "bg-primary text-white" : "text-muted hover:text-slate-700"
          )}
        >
          Reply
        </button>
        <button
          onClick={() => setIsNote(true)}
          className={cn(
            "text-xs px-2 py-0.5 rounded-full font-medium transition-colors flex items-center gap-1",
            isNote ? "bg-amber-500 text-white" : "text-muted hover:text-slate-700"
          )}
        >
          <StickyNote className="h-3 w-3" /> Note
        </button>
      </div>

      <div className="flex items-end gap-2">
        <Textarea
          rows={2}
          placeholder={isNote ? "Add an internal note…" : "Reply to customer…"}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          className={cn("flex-1 text-sm resize-none", isNote && "border-amber-300 focus:ring-amber-400")}
        />
        <div className="flex flex-col gap-1">
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="h-8 w-8 flex items-center justify-center rounded-md text-muted hover:text-slate-700 hover:bg-surface-3 transition-colors"
            title="Attach file"
          >
            <Paperclip className="h-4 w-4" />
          </button>
          <Button size="icon" onClick={send} loading={sending} disabled={!text.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
      <input ref={fileRef} type="file" className="hidden" onChange={handleFile} />
    </div>
  );
}
