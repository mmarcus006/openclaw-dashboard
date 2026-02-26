import { describe, it, expect } from 'vitest';
import { filteredAgents } from '@/stores/agentStore';
import type { FilterParams } from '@/stores/agentStore';
import type { AgentSummary } from '@/types';

const mockAgents: AgentSummary[] = [
  {
    id: 'main',
    name: 'Main Agent',
    model: 'claude-opus-4-6',
    status: 'active',
    last_activity: '2026-02-26T10:00:00Z',
  },
  {
    id: 'helper',
    name: 'Helper Bot',
    model: 'gpt-5.3-codex',
    status: 'idle',
    last_activity: '2026-02-25T08:00:00Z',
  },
  {
    id: 'backup',
    name: 'Backup Agent',
    model: 'claude-opus-4-6',
    status: 'stopped',
    last_activity: null,
  },
];

function buildParams(overrides: Partial<FilterParams> = {}): FilterParams {
  return {
    agents: mockAgents,
    searchTerm: '',
    statusFilter: 'all',
    sortBy: 'name',
    ...overrides,
  };
}

describe('filteredAgents', () => {
  it('filters by search term and status', () => {
    // Search for "claude" — should match Main Agent and Backup Agent
    const bySearch = filteredAgents(buildParams({ searchTerm: 'claude' }));
    expect(bySearch).toHaveLength(2);
    expect(bySearch.map((a) => a.id)).toEqual(['backup', 'main']); // sorted by name

    // Filter by status "idle" — should match only Helper Bot
    const byStatus = filteredAgents(buildParams({ statusFilter: 'idle' }));
    expect(byStatus).toHaveLength(1);
    expect(byStatus[0]!.id).toBe('helper');

    // Combined: search "agent" + status "active"
    const combined = filteredAgents(buildParams({ searchTerm: 'agent', statusFilter: 'active' }));
    expect(combined).toHaveLength(1);
    expect(combined[0]!.id).toBe('main');
  });

  it('sorts agents correctly by name, status, and last_activity', () => {
    // Sort by name (default)
    const byName = filteredAgents(buildParams({ sortBy: 'name' }));
    expect(byName.map((a) => a.name)).toEqual(['Backup Agent', 'Helper Bot', 'Main Agent']);

    // Sort by status
    const byStatus = filteredAgents(buildParams({ sortBy: 'status' }));
    expect(byStatus.map((a) => a.status)).toEqual(['active', 'idle', 'stopped']);

    // Sort by last_activity — most recent first, null last
    const byActivity = filteredAgents(buildParams({ sortBy: 'last_activity' }));
    expect(byActivity.map((a) => a.id)).toEqual(['main', 'helper', 'backup']);
  });
});
