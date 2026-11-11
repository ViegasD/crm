"use client";
import { useEffect, useRef } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { useConversationStore } from "@/stores/conversation-store";
import { ConversationList, MessageThread, ReplyBox, ConversationHeader, ConversationSidePanel } from "@/components/inbox";
import { WorkspaceSocket } from "@/lib/websocket";
import { conversationsApi, messagesApi } from "@/lib/api";
import type { Conversation, Message } from "@/types/conversation";

function hasPendingAttachments(message: Message): boolean {
  return (message.attachments ?? []).some((attachment) => attachment.ready === false || !attachment.url);
}

function normalizeSocketMessage(raw: Record<string, unknown>): Message {
  return {
    id: String(raw.id ?? ""),
    conversationId: String(raw.conversation_id ?? raw.conversationId ?? ""),
    senderType: String(raw.sender_type ?? raw.senderType ?? "system") as Message["senderType"],
    senderId: raw.sender_id ? String(raw.sender_id) : raw.senderId ? String(raw.senderId) : undefined,
    senderName: raw.sender_name ? String(raw.sender_name) : raw.senderName ? String(raw.senderName) : undefined,
    origin: raw.origin ? String(raw.origin) : undefined,
    content: raw.content ? String(raw.content) : undefined,
    type: String(raw.type ?? "text") as Message["type"],
    attachments: Array.isArray(raw.attachments) ? (raw.attachments as Message["attachments"]) : [],
    isRead: Boolean(raw.is_read ?? raw.isRead),
    providerStatus: raw.provider_status ? String(raw.provider_status) : raw.providerStatus ? String(raw.providerStatus) : null,
    providerStatusUpdatedAt: raw.provider_status_updated_at
      ? String(raw.provider_status_updated_at)
      : raw.providerStatusUpdatedAt
      ? String(raw.providerStatusUpdatedAt)
      : null,
    providerStatusError: raw.provider_status_error
      ? String(raw.provider_status_error)
      : raw.providerStatusError
      ? String(raw.providerStatusError)
      : null,
    createdAt: String(raw.created_at ?? raw.createdAt ?? new Date().toISOString()),
  };
}

export default function InboxPage() {
  const { currentWorkspace, accessToken } = useAuthStore();
  const { activeId, upsertConversation, appendMessage, updateMessage, conversations } = useConversationStore();
  const pendingRefreshesRef = useRef<Map<string, number>>(new Map());

  // WebSocket — connect once per workspace
  useEffect(() => {
    if (!currentWorkspace || !accessToken) return;
    const pendingRefreshes = pendingRefreshesRef.current;
    const socket = new WorkspaceSocket(currentWorkspace.id, accessToken);
    socket.connect();

    const fetchConversationMessage = async (conversationId: string, messageId: string): Promise<Message | null> => {
      const r = await messagesApi.list(currentWorkspace.id, conversationId, { page_size: 10 });
      const messages = (r.data.items ?? []) as Message[];
      return messages.find((item) => item.id === messageId) ?? null;
    };

    const schedulePendingRefresh = (conversationId: string, messageId: string, attempt = 1): void => {
      if (attempt > 5 || pendingRefreshes.has(messageId)) {
        return;
      }

      const timeoutId = window.setTimeout(async () => {
        pendingRefreshes.delete(messageId);
        try {
          const refreshed = await fetchConversationMessage(conversationId, messageId);
          if (!refreshed) {
            return;
          }
          updateMessage(refreshed);
          if (hasPendingAttachments(refreshed)) {
            schedulePendingRefresh(conversationId, messageId, attempt + 1);
          }
        } catch {
          schedulePendingRefresh(conversationId, messageId, attempt + 1);
        }
      }, attempt * 1500);

      pendingRefreshes.set(messageId, timeoutId);
    };

    const unsub = socket.on(async (event) => {
      if (event.type === "message.new") {
        const convId = event.conversation_id as string;
        const messageId = event.message_id as string;
        // Fetch the new message
        try {
          const freshMessage = await fetchConversationMessage(convId, messageId);
          if (freshMessage) {
            appendMessage(freshMessage);
            if (hasPendingAttachments(freshMessage)) {
              schedulePendingRefresh(convId, freshMessage.id);
            }
          }
        } catch { /* ignore */ }
      }
      if (event.type === "message.updated") {
        const rawMessage = event.message;
        if (rawMessage && typeof rawMessage === "object") {
          updateMessage(normalizeSocketMessage(rawMessage as Record<string, unknown>));
        }
      }
      if (event.type === "conversation.updated") {
        const convId = event.conversation_id as string;
        try {
          const r = await conversationsApi.get(currentWorkspace.id, convId);
          upsertConversation(r.data as Conversation);
        } catch { /* ignore */ }
      }
    });

    return () => {
      for (const timeoutId of pendingRefreshes.values()) {
        window.clearTimeout(timeoutId);
      }
      pendingRefreshes.clear();
      unsub();
      socket.disconnect();
    };
  }, [currentWorkspace?.id, accessToken]); // eslint-disable-line react-hooks/exhaustive-deps

  const activeConversation = conversations.find((c) => c.id === activeId);

  if (!currentWorkspace) {
    return (
      <div className="flex h-full items-center justify-center text-muted text-sm">
        No workspace selected
      </div>
    );
  }

  return (
    <div className="flex h-full">
      {/* Conversation list */}
      <ConversationList workspaceId={currentWorkspace.id} />

      {/* Message panel */}
      <div className="flex flex-1 flex-col min-w-0">
        {activeConversation ? (
          <>
            <ConversationHeader workspaceId={currentWorkspace.id} conversation={activeConversation} />
            <MessageThread workspaceId={currentWorkspace.id} conversationId={activeConversation.id} />
            {activeConversation.status !== "resolved" && (
              <ReplyBox workspaceId={currentWorkspace.id} conversationId={activeConversation.id} />
            )}
          </>
        ) : (
          <div className="flex flex-1 items-center justify-center text-muted text-sm">
            Select a conversation
          </div>
        )}
      </div>
      {activeConversation && (
        <ConversationSidePanel
          workspaceId={currentWorkspace.id}
          conversationId={activeConversation.id}
          contactId={activeConversation.contactId}
          contactName={activeConversation.contactName}
        />
      )}
    </div>
  );
}

