import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import DashboardPage from '@/pages/DashboardPage';
import { useAgentStore } from '@/stores/agentStore';
import { useGatewayStore } from '@/stores/gatewayStore';
import type { AgentSummary } from '@/types';

// Mock useWebSocket to prevent WS connections in tests
vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: () => {},
}));

// Mock the agents API to prevent real fetches
vi.mock('@/api/agents', () => ({
  agentsApi: {
    list: vi.fn().mockResolvedValue({ data: { agents: [] } }),
    get: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

const mockAgents: AgentSummary[] = [
  { id: 'main', name: 'Main Agent', model: 'claude-opus-4-6', status: 'active', last_activity: '2026-02-26T10:00:00Z' },
  { id: 'helper', name: 'Helper Bot', model: 'gpt-5.3-codex', status: 'idle', last_activity: '2026-02-25T08:00:00Z' },
  { id: 'backup', name: 'Backup Agent', model: 'claude-opus-4-6', status: 'stopped', last_activity: null },
];

function renderPage() {
  return render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>,
  );
}

describe('DashboardPage', () => {
  beforeEach(() => {
    useAgentStore.setState({
      agents: mockAgents,
      loading: false,
      error: null,
      searchTerm: '',
      statusFilter: 'all',
      sortBy: 'name',
    });
    useGatewayStore.setState({
      status: { running: true, pid: 1234, uptime: '2h', error: null },
    });
  });

  it('renders stat cards and recent activity, not the agent grid', () => {
    renderPage();

    // Stat cards present
    expect(screen.getByText('Total Agents')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();

    // "Gateway" appears in both sidebar and stat card — use getAllByText
    expect(screen.getAllByText('Gateway').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('On')).toBeInTheDocument(); // gateway running

    // Fleet section heading
    expect(screen.getByText('Fleet (3)')).toBeInTheDocument();

    // Recent activity shows agent names
    expect(screen.getByText('Main Agent')).toBeInTheDocument();
    expect(screen.getByText('Helper Bot')).toBeInTheDocument();

    // Quick nav cards present
    expect(screen.getByText('View All Agents')).toBeInTheDocument();
    expect(screen.getByText('Open Config')).toBeInTheDocument();

    // Agent grid should NOT be rendered (no search input)
    expect(screen.queryByPlaceholderText(/search/i)).not.toBeInTheDocument();
  });
});
