/**
 * useGateway hook — wraps gatewayStore + periodic polling.
 */

import { useEffect, useCallback } from 'react';
import { useGatewayStore } from '@/stores/gatewayStore';
import type { GatewayAction, GatewayStatusResponse, CommandResponse } from '@/types';

const POLL_INTERVAL_MS = 10_000;

export function useGateway(): {
  status: GatewayStatusResponse | null;
  loading: boolean;
  actionLoading: boolean;
  error: string | null;
  lastCommandOutput: string | null;
  refresh: () => Promise<void>;
  performAction: (action: GatewayAction) => Promise<CommandResponse | null>;
} {
  const status = useGatewayStore((s) => s.status);
  const loading = useGatewayStore((s) => s.loading);
  const actionLoading = useGatewayStore((s) => s.actionLoading);
  const error = useGatewayStore((s) => s.error);
  const lastCommandOutput = useGatewayStore((s) => s.lastCommandOutput);
  const fetchStatus = useGatewayStore((s) => s.fetchStatus);
  const performAction = useGatewayStore((s) => s.performAction);

  const refresh = useCallback(() => fetchStatus(), [fetchStatus]);

  useEffect(() => {
    void fetchStatus();
    const interval = setInterval(() => {
      void fetchStatus();
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  return { status, loading, actionLoading, error, lastCommandOutput, refresh, performAction };
}
