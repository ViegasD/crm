"use client";
import { useEffect } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { useConversationStore } from "@/stores/conversation-store";
import { ConversationList, MessageThread, ReplyBox, ConversationHeader } from "@/components/inbox";
import { WorkspaceSocket } from "@/lib/websocket";
import { conversationsApi, messagesApi } from "@/lib/api";
import type { Conversation, Message } from "@/types/conversation";

export default function InboxPage() {
  const { currentWorkspace, accessToken } = useAuthStore();
  const { activeId, upsertConversation, appendMessage, conversations } = useConversationStore();

  // WebSocket — connect once per workspace
  useEffect(() => {
    if (!currentWorkspace || !accessToken) return;
    const socket = new WorkspaceSocket(currentWorkspace.id, accessToken);
    socket.connect();

    const unsub = socket.on(async (event) => {
      if (event.type === "message.new") {
        const convId = event.conversation_id as string;
        const msgId = event.message_id as string;
        // Fetch the new message
        try {
          const r = await messagesApi.list(currentWorkspace.id, convId, { page_size: 1 });
          const msgs = (r.data.items ?? []) as Message[];
          if (msgs.length > 0) appendMessage(msgs[0]);
        } catch { /* ignore */ }
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
    </div>
  );
}

