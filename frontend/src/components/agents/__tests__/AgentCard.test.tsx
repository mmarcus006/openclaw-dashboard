import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AgentCard } from '../AgentCard';
import type { AgentSummary } from '@/types';

function makeAgent(overrides: Partial<AgentSummary> = {}): AgentSummary {
  return {
    id: 'main',
    name: 'Main',
    model: 'claude-opus-4-6',
    status: 'active',
    last_activity: new Date().toISOString(),
    ...overrides,
  };
}

describe('AgentCard', () => {
  it('renders green border for active status', () => {
    const { container } = render(
      <MemoryRouter>
        <AgentCard agent={makeAgent({ status: 'active' })} onClick={vi.fn()} />
      </MemoryRouter>,
    );
    const card = container.querySelector('[role="button"]')!;
    expect(card.className).toContain('border-l-success');
  });

  it('renders amber border for idle status', () => {
    const { container } = render(
      <MemoryRouter>
        <AgentCard agent={makeAgent({ status: 'idle' })} onClick={vi.fn()} />
      </MemoryRouter>,
    );
    const card = container.querySelector('[role="button"]')!;
    expect(card.className).toContain('border-l-warning');
  });

  it('renders gray border for stopped status', () => {
    const { container } = render(
      <MemoryRouter>
        <AgentCard agent={makeAgent({ status: 'stopped' })} onClick={vi.fn()} />
      </MemoryRouter>,
    );
    const card = container.querySelector('[role="button"]')!;
    expect(card.className).toContain('border-l-text-secondary');
  });

  it('shows "No sessions yet" when last_activity is null', () => {
    render(
      <MemoryRouter>
        <AgentCard agent={makeAgent({ last_activity: null })} onClick={vi.fn()} />
      </MemoryRouter>,
    );
    expect(screen.getByText('No sessions yet')).toBeInTheDocument();
  });

  it('shows model name without provider prefix', () => {
    render(
      <MemoryRouter>
        <AgentCard agent={makeAgent({ model: 'anthropic/claude-opus-4-6' })} onClick={vi.fn()} />
      </MemoryRouter>,
    );
    expect(screen.getByText('claude-opus-4-6')).toBeInTheDocument();
  });
});
