"use client";
import { useRef, useState, useEffect, useMemo } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/form";
import { cannedResponsesApi, messagesApi, mediaApi } from "@/lib/api";
import { useConversationStore } from "@/stores/conversation-store";
import type { CannedResponse, Message } from "@/types/conversation";
import { Send, Paperclip, StickyNote, MessageSquareText } from "lucide-react";

interface Props {
  workspaceId: string;
  conversationId: string;
}

export function ReplyBox({ workspaceId, conversationId }: Props) {
  const [text, setText] = useState("");
  const [isNote, setIsNote] = useState(false);
  const [sending, setSending] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [cannedResponses, setCannedResponses] = useState<CannedResponse[]>([]);
  const [caretIndex, setCaretIndex] = useState(0);
  const [selectedResponseIndex, setSelectedResponseIndex] = useState(0);
  const [slashMenuDismissed, setSlashMenuDismissed] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { appendMessage } = useConversationStore();

  useEffect(() => {
    cannedResponsesApi.list(workspaceId).then((r) => setCannedResponses(r.data ?? [])).catch(() => setCannedResponses([]));
  }, [workspaceId]);

  const slashState = useMemo(() => getSlashState(text, caretIndex), [text, caretIndex]);
  const filteredResponses = useMemo(() => {
    if (!slashState) return [];
    const query = normalizeSearch(slashState.query);
    return cannedResponses
      .filter((response) => {
        if (!query) return true;
        return [response.shortcut, response.title, response.content]
          .some((value) => normalizeSearch(value).includes(query));
      })
      .slice(0, 6);
  }, [cannedResponses, slashState]);

  const slashMenuOpen = !isNote && !slashMenuDismissed && !!slashState && filteredResponses.length > 0;
  const selectedResponse = filteredResponses[selectedResponseIndex];
  const mentionHint = isNote && /@[A-Za-z0-9_.\-]+/.test(text);

  useEffect(() => {
    setSelectedResponseIndex(0);
  }, [slashState?.query, filteredResponses.length]);

  async function applyCannedResponse(response: CannedResponse) {
    let body = response.content;
    try {
      const rendered = await cannedResponsesApi.render(workspaceId, response.id, {
        conversation_id: conversationId,
      });
      if (rendered.data?.content) body = rendered.data.content;
    } catch {
      /* fallback to raw template */
    }
    if (!slashState) {
      setText(body);
      setCaretIndex(body.length);
      return;
    }

    const nextText = [
      text.slice(0, slashState.tokenStart),
      body,
      text.slice(slashState.caret),
    ].join("");
    const nextCaretIndex = slashState.tokenStart + body.length;
    setText(nextText);
    setCaretIndex(nextCaretIndex);
    setSlashMenuDismissed(false);

    requestAnimationFrame(() => {
      textareaRef.current?.focus();
      textareaRef.current?.setSelectionRange(nextCaretIndex, nextCaretIndex);
    });
  }

  function handleTextChange(value: string, nextCaretIndex: number | null) {
    setText(value);
    setCaretIndex(nextCaretIndex ?? value.length);
    setSlashMenuDismissed(false);
  }

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
      setCaretIndex(0);
      setSlashMenuDismissed(false);
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
    if (slashMenuOpen) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedResponseIndex((index) => (index + 1) % filteredResponses.length);
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedResponseIndex((index) => (index - 1 + filteredResponses.length) % filteredResponses.length);
        return;
      }
      if ((e.key === "Enter" || e.key === "Tab") && selectedResponse) {
        e.preventDefault();
        applyCannedResponse(selectedResponse);
        return;
      }
      if (e.key === "Escape") {
        e.preventDefault();
        setSlashMenuDismissed(true);
        return;
      }
    }

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
      <div className="flex flex-wrap gap-2 mb-1.5">
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
        <div className="relative flex-1">
          {slashMenuOpen && (
            <div className="absolute bottom-[calc(100%+0.5rem)] left-0 z-20 max-h-64 w-full max-w-xl overflow-y-auto rounded-md border border-border bg-white shadow-lg">
              {filteredResponses.map((response, index) => (
                <button
                  key={response.id}
                  type="button"
                  onMouseDown={(event) => {
                    event.preventDefault();
                    applyCannedResponse(response);
                  }}
                  onMouseEnter={() => setSelectedResponseIndex(index)}
                  className={cn(
                    "flex w-full items-start gap-2 border-b border-border/60 px-3 py-2 text-left last:border-b-0",
                    index === selectedResponseIndex ? "bg-blue-50" : "hover:bg-surface-2"
                  )}
                >
                  <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-surface-3 text-primary">
                    <MessageSquareText className="h-4 w-4" />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-primary">{response.shortcut}</span>
                      <span className="truncate text-sm font-medium text-slate-900">{response.title}</span>
                    </span>
                    <span
                      className="mt-0.5 block overflow-hidden text-xs leading-5 text-muted"
                      style={{ display: "-webkit-box", WebkitBoxOrient: "vertical", WebkitLineClamp: 2 }}
                    >
                      {response.content}
                    </span>
                  </span>
                </button>
              ))}
            </div>
          )}
          <Textarea
            ref={textareaRef}
            rows={2}
            placeholder={isNote ? "Add an internal note…" : "Reply to customer…"}
            value={text}
            onChange={(e) => handleTextChange(e.currentTarget.value, e.currentTarget.selectionStart)}
            onClick={(e) => setCaretIndex(e.currentTarget.selectionStart)}
            onKeyUp={(e) => setCaretIndex(e.currentTarget.selectionStart)}
            onSelect={(e) => setCaretIndex(e.currentTarget.selectionStart)}
            onKeyDown={handleKeyDown}
            className={cn("flex-1 text-sm resize-none", isNote && "border-amber-300 focus:ring-amber-400")}
          />
        </div>
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
      {mentionHint && (
        <p className="mt-1 text-[11px] text-amber-700">
          Mentions detected — observers will be notified when you send this note.
        </p>
      )}
    </div>
  );
}

function getSlashState(value: string, caret: number) {
  if (caret < 0 || caret > value.length) return null;
  const beforeCaret = value.slice(0, caret);
  const tokenStart = Math.max(
    beforeCaret.lastIndexOf(" "),
    beforeCaret.lastIndexOf("\n"),
    beforeCaret.lastIndexOf("\t")
  ) + 1;
  const token = beforeCaret.slice(tokenStart);
  if (!token.startsWith("/") || token.includes(" ")) return null;
  return { tokenStart, caret, query: token.slice(1) };
}

function normalizeSearch(value: string) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}
