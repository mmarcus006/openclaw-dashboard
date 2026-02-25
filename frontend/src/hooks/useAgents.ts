/**
 * useAgents hook — wraps agentStore actions with polling.
 */

import { useEffect, useCallback } from 'react';
import { useAgentStore } from '@/stores/agentStore';

const POLL_INTERVAL_MS = 5000;

export function useAgents(): {
  agents: ReturnType<typeof useAgentStore.getState>['agents'];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
} {
  const agents = useAgentStore((s) => s.agents);
  const loading = useAgentStore((s) => s.loading);
  const error = useAgentStore((s) => s.error);
  const fetchAgents = useAgentStore((s) => s.fetchAgents);

  const refresh = useCallback(() => fetchAgents(), [fetchAgents]);

  useEffect(() => {
    void fetchAgents();
    const interval = setInterval(() => {
      void fetchAgents();
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchAgents]);

  return { agents, loading, error, refresh };
}
