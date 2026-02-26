/**
 * Gateway store — gateway status, loading, last refresh, command history.
 */

import { create } from 'zustand';
import { gatewayApi } from '@/api/gateway';
import type {
  GatewayStatusResponse,
  GatewayAction,
  GatewayCommandEntry,
  CommandResponse,
} from '@/types';

const STATUS_TIMEOUT_MS = 5_000;

interface GatewayState {
  status: GatewayStatusResponse | null;
  loading: boolean;
  actionLoading: boolean;
  lastRefresh: Date | null;
  error: string | null;
  lastCommandOutput: string | null;
  timedOut: boolean;
  history: GatewayCommandEntry[];

  fetchStatus: () => Promise<void>;
  fetchHistory: () => Promise<void>;
  performAction: (action: GatewayAction) => Promise<CommandResponse | null>;
}

export const useGatewayStore = create<GatewayState>((set) => ({
  status: null,
  loading: false,
  actionLoading: false,
  lastRefresh: null,
  error: null,
  lastCommandOutput: null,
  timedOut: false,
  history: [],

  fetchStatus: async () => {
    set({ loading: true, error: null });
    try {
      const timeoutPromise = new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('timeout')), STATUS_TIMEOUT_MS)
      );
      const { data } = await Promise.race([gatewayApi.status(), timeoutPromise]);
      set({ status: data, loading: false, lastRefresh: new Date(), timedOut: false });
    } catch (e) {
      const isTimeout = e instanceof Error && e.message === 'timeout';
      set({
        error: isTimeout ? 'Gateway status request timed out' : String(e),
        loading: false,
        timedOut: isTimeout,
      });
    }
  },

  fetchHistory: async () => {
    try {
      const { data } = await gatewayApi.history();
      set({ history: data.commands });
    } catch {
      // History is non-critical — silently fail
    }
  },

  performAction: async (action: GatewayAction) => {
    set({ actionLoading: true, error: null });
    try {
      const { data } = await gatewayApi.action(action);
      set({
        actionLoading: false,
        lastCommandOutput: data.output ?? data.message,
      });
      // Refresh status and history after action
      const { data: statusData } = await gatewayApi.status();
      set({ status: statusData, lastRefresh: new Date() });
      // Fetch updated history
      try {
        const { data: histData } = await gatewayApi.history();
        set({ history: histData.commands });
      } catch {
        // non-critical
      }
      return data;
    } catch (e) {
      set({ error: String(e), actionLoading: false });
      return null;
    }
  },
}));
