import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AgentDetail } from '../AgentDetail';
import type { AgentDetailResponse } from '@/types';

// Mock session store
vi.mock('@/stores/sessionStore', () => ({
  useSessionStore: () => vi.fn(),
}));

// Mock SessionList and SessionViewer to avoid loading session dependencies
vi.mock('@/components/sessions/SessionList', () => ({
  SessionList: () => <div data-testid="session-list" />,
}));
vi.mock('@/components/sessions/SessionViewer', () => ({
  SessionViewer: () => <div data-testid="session-viewer" />,
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

function makeAgent(overrides: Partial<AgentDetailResponse> = {}): AgentDetailResponse {
  return {
    id: 'main',
    name: 'Main Agent',
    model: 'claude-opus-4-6',
    status: 'active',
    workspace: '/home/.openclaw/workspace',
    files: [],
    last_activity: new Date().toISOString(),
    ...overrides,
  };
}

describe('AgentDetail', () => {
  it('back button navigates to /agents', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <AgentDetail agent={makeAgent()} loading={false} error={null} />
      </MemoryRouter>,
    );

    const backButton = screen.getByText('Back to fleet').closest('button')!;
    await user.click(backButton);

    expect(mockNavigate).toHaveBeenCalledWith('/agents');
  });
});
