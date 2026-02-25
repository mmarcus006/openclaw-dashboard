/**
 * Agent store — agent list, selected agent, loading state.
 * Separate store prevents re-render storms from WebSocket updates. (R3)
 */

import { create } from 'zustand';
import { agentsApi } from '@/api/agents';
import type { AgentSummary, AgentDetailResponse } from '@/types';

interface AgentState {
  agents: AgentSummary[];
  selectedAgent: AgentDetailResponse | null;
  loading: boolean;
  detailLoading: boolean;
  error: string | null;
  fetchAgents: () => Promise<void>;
  fetchAgent: (agentId: string) => Promise<void>;
  clearSelectedAgent: () => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  agents: [],
  selectedAgent: null,
  loading: false,
  detailLoading: false,
  error: null,

  fetchAgents: async () => {
    set({ loading: true, error: null });
    try {
      const { data } = await agentsApi.list();
      set({ agents: data.agents, loading: false });
    } catch (e) {
      set({ error: String(e), loading: false });
    }
  },

  fetchAgent: async (agentId: string) => {
    set({ detailLoading: true, error: null });
    try {
      const { data } = await agentsApi.get(agentId);
      set({ selectedAgent: data, detailLoading: false });
    } catch (e) {
      set({ error: String(e), detailLoading: false });
    }
  },

  clearSelectedAgent: () => set({ selectedAgent: null }),
}));
