/**
 * useGateway hook — wraps gatewayStore + periodic polling.
 */

import { useEffect, useCallback } from 'react';
import { useGatewayStore } from '@/stores/gatewayStore';
import type { GatewayAction, GatewayStatusResponse, GatewayCommandEntry, CommandResponse } from '@/types';

const POLL_INTERVAL_MS = 10_000;

export function useGateway(): {
  status: GatewayStatusResponse | null;
  loading: boolean;
  actionLoading: boolean;
  error: string | null;
  timedOut: boolean;
  lastCommandOutput: string | null;
  history: GatewayCommandEntry[];
  refresh: () => Promise<void>;
  performAction: (action: GatewayAction) => Promise<CommandResponse | null>;
} {
  const status = useGatewayStore((s) => s.status);
  const loading = useGatewayStore((s) => s.loading);
  const actionLoading = useGatewayStore((s) => s.actionLoading);
  const error = useGatewayStore((s) => s.error);
  const timedOut = useGatewayStore((s) => s.timedOut);
  const lastCommandOutput = useGatewayStore((s) => s.lastCommandOutput);
  const history = useGatewayStore((s) => s.history);
  const fetchStatus = useGatewayStore((s) => s.fetchStatus);
  const fetchHistory = useGatewayStore((s) => s.fetchHistory);
  const performAction = useGatewayStore((s) => s.performAction);

  const refresh = useCallback(() => fetchStatus(), [fetchStatus]);

  useEffect(() => {
    void fetchStatus();
    void fetchHistory();
    const interval = setInterval(() => {
      void fetchStatus();
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchStatus, fetchHistory]);

  return { status, loading, actionLoading, error, timedOut, lastCommandOutput, history, refresh, performAction };
}
