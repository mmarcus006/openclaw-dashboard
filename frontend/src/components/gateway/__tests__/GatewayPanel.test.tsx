import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { GatewayPanel } from '@/components/gateway/GatewayPanel';
import { useGatewayStore } from '@/stores/gatewayStore';

// Mock useWebSocket to prevent WS connections
vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: () => {},
}));

// Mock gateway API to prevent real fetches
vi.mock('@/api/gateway', () => ({
  gatewayApi: {
    status: vi.fn().mockResolvedValue({ data: { running: false } }),
    action: vi.fn().mockResolvedValue({ data: { success: true, message: 'ok' } }),
    history: vi.fn().mockResolvedValue({ data: { commands: [], total: 0 } }),
    cronJobs: vi.fn().mockResolvedValue({ data: { jobs: [], total: 0 } }),
  },
}));

describe('GatewayPanel', () => {
  beforeEach(() => {
    useGatewayStore.setState({
      status: null,
      loading: false,
      actionLoading: false,
      lastRefresh: null,
      error: null,
      lastCommandOutput: null,
      timedOut: false,
      history: [],
    });
  });

  it('shows error state on timeout instead of infinite spinner', () => {
    useGatewayStore.setState({
      status: null,
      loading: false,
      timedOut: true,
      error: 'Gateway status request timed out',
    });

    render(<GatewayPanel />);

    expect(screen.getByText('Gateway Status Unavailable')).toBeInTheDocument();
    expect(screen.getByText(/timed out after 5 seconds/)).toBeInTheDocument();
    // Should NOT show a spinner
    expect(screen.queryByText('Loading gateway status…')).not.toBeInTheDocument();
  });

  it('shows prominent Start button when gateway is stopped', () => {
    useGatewayStore.setState({
      status: { running: false, pid: null, uptime: null, channels: {}, error: null },
      loading: false,
      timedOut: false,
    });

    render(<GatewayPanel />);

    expect(screen.getByText('Gateway Stopped')).toBeInTheDocument();
    expect(screen.getByText('Start Gateway')).toBeInTheDocument();
    // Stop button should be disabled
    const stopButton = screen.getByText('Stop').closest('button');
    expect(stopButton).toBeDisabled();
  });
});
