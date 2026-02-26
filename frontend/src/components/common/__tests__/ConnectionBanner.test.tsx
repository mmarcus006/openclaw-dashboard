/**
 * ConnectionBanner tests — show/hide based on WS connection state.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ConnectionBanner } from '../ConnectionBanner';
import { useWsStore } from '@/stores/wsStore';

beforeEach(() => {
  useWsStore.setState({ connectionState: 'connected' });
});

describe('ConnectionBanner', () => {
  it('is hidden when connected', () => {
    const { container } = render(<ConnectionBanner />);
    expect(container.firstChild).toBeNull();
  });

  it('shows amber banner when disconnected', () => {
    useWsStore.setState({ connectionState: 'disconnected' });
    render(<ConnectionBanner />);
    expect(screen.getByText(/Connection lost/)).toBeInTheDocument();
  });

  it('shows reconnecting banner when connecting', () => {
    useWsStore.setState({ connectionState: 'connecting' });
    render(<ConnectionBanner />);
    expect(screen.getByText(/Reconnecting/)).toBeInTheDocument();
  });
});
