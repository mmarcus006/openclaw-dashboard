import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import AgentsPage from '@/pages/AgentsPage';
import { useAgentStore } from '@/stores/agentStore';
import type { AgentSummary } from '@/types';

// Mock useWebSocket to prevent WS connections in tests
vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: () => {},
}));

// Mock useAgents to prevent API polling — AgentsPage reads from the store directly
vi.mock('@/hooks/useAgents', () => ({
  useAgents: () => ({
    agents: [],    // AgentsPage doesn't use this — it reads filtered agents via useMemo
    loading: false,
    error: null,
    refresh: async () => {},
  }),
}));

const mockAgents: AgentSummary[] = [
  { id: 'main', name: 'Main Agent', model: 'claude-opus-4-6', status: 'active', last_activity: '2026-02-26T10:00:00Z' },
  { id: 'helper', name: 'Helper Bot', model: 'gpt-5.3-codex', status: 'idle', last_activity: '2026-02-25T08:00:00Z' },
  { id: 'backup', name: 'Backup Agent', model: 'claude-opus-4-6', status: 'stopped', last_activity: null },
];

function renderPage() {
  return render(
    <MemoryRouter>
      <AgentsPage />
    </MemoryRouter>,
  );
}

describe('AgentsPage', () => {
  beforeEach(() => {
    useAgentStore.setState({
      agents: mockAgents,
      loading: false,
      error: null,
      searchTerm: '',
      statusFilter: 'all',
      sortBy: 'name',
    });
  });

  it('filters agents by search term', async () => {
    const user = userEvent.setup();
    renderPage();

    // All 3 agents visible initially
    expect(screen.getByText('Main Agent')).toBeInTheDocument();
    expect(screen.getByText('Helper Bot')).toBeInTheDocument();
    expect(screen.getByText('Backup Agent')).toBeInTheDocument();

    // Type into search
    const searchInput = screen.getByPlaceholderText(/search agents/i);
    await user.type(searchInput, 'helper');

    // Only Helper Bot visible
    expect(screen.getByText('Helper Bot')).toBeInTheDocument();
    expect(screen.queryByText('Main Agent')).not.toBeInTheDocument();
    expect(screen.queryByText('Backup Agent')).not.toBeInTheDocument();
  });

  it('filters agents by status', async () => {
    const user = userEvent.setup();
    renderPage();

    // Select "Active" status filter
    const statusSelect = screen.getByLabelText('Filter by status');
    await user.selectOptions(statusSelect, 'active');

    // Only the active agent should be visible
    expect(screen.getByText('Main Agent')).toBeInTheDocument();
    expect(screen.queryByText('Helper Bot')).not.toBeInTheDocument();
    expect(screen.queryByText('Backup Agent')).not.toBeInTheDocument();
  });
});
