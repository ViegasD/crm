// Conversation list + active conversation state
"use client";
import { create } from "zustand";
import type { Conversation, Message } from "@/types/conversation";

interface ConversationStore {
  conversations: Conversation[];
  total: number;
  activeId: string | null;
  messages: Record<string, Message[]>; // keyed by conversation id
  unreadCounts: Record<string, number>;

  setConversations: (convs: Conversation[], total: number) => void;
  upsertConversation: (conv: Conversation) => void;
  setActiveId: (id: string | null) => void;
  setMessages: (convId: string, msgs: Message[]) => void;
  appendMessage: (msg: Message) => void;
  updateMessage: (msg: Message) => void;
  incrementUnread: (convId: string) => void;
  clearUnread: (convId: string) => void;
}

export const useConversationStore = create<ConversationStore>((set) => ({
  conversations: [],
  total: 0,
  activeId: null,
  messages: {},
  unreadCounts: {},

  setConversations: (conversations, total) => set({ conversations, total }),

  upsertConversation: (conv) =>
    set((s) => {
      const idx = s.conversations.findIndex((c) => c.id === conv.id);
      if (idx === -1) return { conversations: [conv, ...s.conversations] };
      const next = [...s.conversations];
      next[idx] = conv;
      return { conversations: next };
    }),

  setActiveId: (activeId) => set({ activeId }),

  setMessages: (convId, msgs) =>
    set((s) => ({ messages: { ...s.messages, [convId]: msgs } })),

  appendMessage: (msg) =>
    set((s) => {
      const existing = s.messages[msg.conversationId] ?? [];
      if (existing.some((m) => m.id === msg.id)) return s;
      return {
        messages: {
          ...s.messages,
          [msg.conversationId]: [...existing, msg],
        },
      };
    }),

  updateMessage: (msg) =>
    set((s) => {
      const existing = s.messages[msg.conversationId] ?? [];
      const idx = existing.findIndex((m) => m.id === msg.id);
      if (idx === -1) {
        return {
          messages: {
            ...s.messages,
            [msg.conversationId]: [...existing, msg],
          },
        };
      }

      const next = [...existing];
      next[idx] = { ...next[idx], ...msg };
      return {
        messages: {
          ...s.messages,
          [msg.conversationId]: next,
        },
      };
    }),

  incrementUnread: (convId) =>
    set((s) => ({
      unreadCounts: { ...s.unreadCounts, [convId]: (s.unreadCounts[convId] ?? 0) + 1 },
    })),

  clearUnread: (convId) =>
    set((s) => ({ unreadCounts: { ...s.unreadCounts, [convId]: 0 } })),
}));
