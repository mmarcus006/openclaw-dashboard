import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { SessionViewer } from '@/components/sessions/SessionViewer';
import { useSessionStore } from '@/stores/sessionStore';
import type { SessionMessage } from '@/api/sessions';

// Mock useWebSocket
vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: () => {},
}));

const mockMessages: SessionMessage[] = [
  {
    id: 'msg-1',
    role: 'user',
    content: [],
    content_text: 'Hello, how are you?',
    timestamp: '2026-01-01T00:01:00Z',
    parent_id: null,
  },
  {
    id: 'msg-2',
    role: 'assistant',
    content: [
      { type: 'thinking', thinking: 'Let me consider this...', text: null, id: null, name: null, arguments: null, tool_call_id: null, content: null },
      { type: 'text', text: 'I am doing well!', thinking: null, id: null, name: null, arguments: null, tool_call_id: null, content: null },
    ],
    content_text: 'Let me consider this...\n\nI am doing well!',
    timestamp: '2026-01-01T00:02:00Z',
    parent_id: 'msg-1',
  },
];

describe('SessionViewer', () => {
  beforeEach(() => {
    useSessionStore.setState({
      messages: mockMessages,
      messagesLoading: false,
      messagesError: null,
      messagesTotal: 2,
      messagesHasMore: false,
      selectedSessionId: 'agent:main:main',
    });
  });

  it('renders messages with correct roles (user right, assistant left)', () => {
    render(
      <MemoryRouter>
        <SessionViewer />
      </MemoryRouter>,
    );

    expect(screen.getByText('User')).toBeInTheDocument();
    expect(screen.getByText('Assistant')).toBeInTheDocument();
    expect(screen.getByText('2 messages')).toBeInTheDocument();
  });

  it('renders content blocks with type-specific rendering', () => {
    render(
      <MemoryRouter>
        <SessionViewer />
      </MemoryRouter>,
    );

    // Thinking block renders with details toggle
    expect(screen.getByText('Thinking...')).toBeInTheDocument();
    // Text block renders inline
    expect(screen.getByText('I am doing well!')).toBeInTheDocument();
  });
});
