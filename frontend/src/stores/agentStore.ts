/**
 * Agent store — agent list, selected agent, loading state, search/filter/sort.
 * Separate store prevents re-render storms from WebSocket updates. (R3)
 */

import { create } from 'zustand';
import { agentsApi } from '@/api/agents';
import type { AgentSummary, AgentDetailResponse } from '@/types';

export type StatusFilter = 'all' | 'active' | 'idle' | 'stopped';
export type SortField = 'name' | 'status' | 'last_activity';

interface AgentState {
  agents: AgentSummary[];
  selectedAgent: AgentDetailResponse | null;
  loading: boolean;
  detailLoading: boolean;
  error: string | null;

  // Search/filter/sort (W1.3)
  searchTerm: string;
  statusFilter: StatusFilter;
  sortBy: SortField;

  fetchAgents: () => Promise<void>;
  fetchAgent: (agentId: string) => Promise<void>;
  clearSelectedAgent: () => void;
  setSearchTerm: (term: string) => void;
  setStatusFilter: (filter: StatusFilter) => void;
  setSortBy: (field: SortField) => void;
}

export interface FilterParams {
  agents: AgentSummary[];
  searchTerm: string;
  statusFilter: StatusFilter;
  sortBy: SortField;
}

/** Apply search, status filter, and sort to agents list. */
export function filteredAgents(state: FilterParams): AgentSummary[] {
  let result = state.agents;

  // Search filter — match name, id, or model
  if (state.searchTerm) {
    const term = state.searchTerm.toLowerCase();
    result = result.filter(
      (a) =>
        a.name.toLowerCase().includes(term) ||
        a.id.toLowerCase().includes(term) ||
        a.model.toLowerCase().includes(term),
    );
  }

  // Status filter
  if (state.statusFilter !== 'all') {
    result = result.filter((a) => a.status === state.statusFilter);
  }

  // Sort
  result = [...result].sort((a, b) => {
    switch (state.sortBy) {
      case 'name':
        return a.name.localeCompare(b.name);
      case 'status':
        return a.status.localeCompare(b.status);
      case 'last_activity': {
        const aTime = a.last_activity ? new Date(a.last_activity).getTime() : 0;
        const bTime = b.last_activity ? new Date(b.last_activity).getTime() : 0;
        return bTime - aTime; // Most recent first
      }
      default:
        return 0;
    }
  });

  return result;
}

export const useAgentStore = create<AgentState>((set) => ({
  agents: [],
  selectedAgent: null,
  loading: false,
  detailLoading: false,
  error: null,
  searchTerm: '',
  statusFilter: 'all',
  sortBy: 'name',

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
  setSearchTerm: (term: string) => set({ searchTerm: term }),
  setStatusFilter: (filter: StatusFilter) => set({ statusFilter: filter }),
  setSortBy: (field: SortField) => set({ sortBy: field }),
}));
