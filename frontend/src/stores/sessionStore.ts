/**
 * Session store — manages session list and message viewer state.
 * Uses AbortController for stale-fetch prevention.
 */

import { create } from 'zustand';
import { sessionsApi } from '@/api/sessions';
import type { SessionSummary, SessionMessage } from '@/api/sessions';

let abortController: AbortController | null = null;

interface SessionState {
  sessions: SessionSummary[];
  selectedAgentId: string | null;
  loading: boolean;
  error: string | null;
  total: number;
  warning: string | null;

  // Message viewer
  messages: SessionMessage[];
  messagesLoading: boolean;
  messagesError: string | null;
  messagesTotal: number;
  messagesHasMore: boolean;
  selectedSessionId: string | null;

  fetchSessions: (agentId: string, offset?: number) => Promise<void>;
  loadMoreSessions: () => Promise<void>;
  fetchMessages: (sessionId: string, offset?: number, full?: boolean) => Promise<void>;
  loadMoreMessages: () => Promise<void>;
  selectSession: (sessionId: string | null) => void;
  clearSessions: () => void;
}

export const useSessionStore = create<SessionState>((set, get) => ({
  sessions: [],
  selectedAgentId: null,
  loading: false,
  error: null,
  total: 0,
  warning: null,

  messages: [],
  messagesLoading: false,
  messagesError: null,
  messagesTotal: 0,
  messagesHasMore: false,
  selectedSessionId: null,

  fetchSessions: async (agentId: string, offset = 0) => {
    // Cancel any in-flight request for a different agent
    if (abortController) abortController.abort();
    abortController = new AbortController();

    if (offset === 0) {
      set({ sessions: [], loading: true, error: null, selectedAgentId: agentId, total: 0 });
    } else {
      set({ loading: true, error: null });
    }

    try {
      const { data } = await sessionsApi.list(agentId, offset);
      const prev = offset > 0 ? get().sessions : [];
      set({
        sessions: [...prev, ...data.sessions],
        total: data.total,
        warning: data.warning,
        loading: false,
      });
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') return;
      set({ error: String(e), loading: false });
    }
  },

  loadMoreSessions: async () => {
    const { selectedAgentId, sessions } = get();
    if (!selectedAgentId) return;
    await get().fetchSessions(selectedAgentId, sessions.length);
  },

  fetchMessages: async (sessionId: string, offset = 0, full = false) => {
    if (offset === 0) {
      set({ messages: [], messagesLoading: true, messagesError: null, selectedSessionId: sessionId });
    } else {
      set({ messagesLoading: true, messagesError: null });
    }

    try {
      const { data } = await sessionsApi.getMessages(sessionId, offset, 50, full);
      const prev = offset > 0 ? get().messages : [];
      set({
        messages: [...prev, ...data.messages],
        messagesTotal: data.total,
        messagesHasMore: data.has_more,
        messagesLoading: false,
      });
    } catch (e) {
      set({ messagesError: String(e), messagesLoading: false });
    }
  },

  loadMoreMessages: async () => {
    const { selectedSessionId, messages } = get();
    if (!selectedSessionId) return;
    await get().fetchMessages(selectedSessionId, messages.length);
  },

  selectSession: (sessionId: string | null) => {
    set({ selectedSessionId: sessionId, messages: [], messagesTotal: 0, messagesHasMore: false });
    if (sessionId) {
      void get().fetchMessages(sessionId);
    }
  },

  clearSessions: () => {
    if (abortController) abortController.abort();
    set({
      sessions: [],
      selectedAgentId: null,
      loading: false,
      error: null,
      total: 0,
      warning: null,
      messages: [],
      messagesLoading: false,
      messagesError: null,
      messagesTotal: 0,
      messagesHasMore: false,
      selectedSessionId: null,
    });
  },
}));
