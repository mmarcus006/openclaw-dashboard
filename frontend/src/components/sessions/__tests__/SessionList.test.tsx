import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { SessionList } from '@/components/sessions/SessionList';
import { useSessionStore } from '@/stores/sessionStore';
import type { SessionSummary } from '@/api/sessions';

// Mock useWebSocket
vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: () => {},
}));

const mockSessions: SessionSummary[] = [
  {
    session_id: 'agent:main:main',
    updated_at: 1772031239308,
    model: 'claude-opus-4-6',
    model_provider: 'anthropic',
    label: null,
    spawned_by: null,
    total_tokens: 5000,
    input_tokens: 2000,
    output_tokens: 3000,
    cache_read: null,
    message_count: null,
    session_file: '/path/to/session.jsonl',
  },
  {
    session_id: 'agent:main:telegram:123',
    updated_at: 1772020000000,
    model: 'claude-sonnet-4-6',
    model_provider: 'anthropic',
    label: 'Telegram Chat',
    spawned_by: null,
    total_tokens: 1000,
    input_tokens: 500,
    output_tokens: 500,
    cache_read: null,
    message_count: null,
    session_file: '/path/to/session2.jsonl',
  },
];

describe('SessionList', () => {
  beforeEach(() => {
    useSessionStore.setState({
      sessions: mockSessions,
      loading: false,
      error: null,
      total: 2,
      warning: null,
      selectedSessionId: null,
      selectedAgentId: 'main',
      fetchSessions: vi.fn(),
    });
  });

  it('renders session list with mock data', () => {
    render(
      <MemoryRouter>
        <SessionList agentId="main" />
      </MemoryRouter>,
    );

    // Should show both sessions
    expect(screen.getByText('main')).toBeInTheDocument();
    expect(screen.getByText('Telegram Chat')).toBeInTheDocument();
    expect(screen.getByText('2 sessions')).toBeInTheDocument();
  });

  it('shows empty state when no sessions', () => {
    useSessionStore.setState({
      sessions: [],
      loading: false,
      total: 0,
    });

    render(
      <MemoryRouter>
        <SessionList agentId="main" />
      </MemoryRouter>,
    );

    expect(screen.getByText('No sessions found')).toBeInTheDocument();
  });
});
