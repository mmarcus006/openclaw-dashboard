/**
 * Gateway store — gateway status, loading, last refresh.
 */

import { create } from 'zustand';
import { gatewayApi } from '@/api/gateway';
import type { GatewayStatusResponse, GatewayAction, CommandResponse } from '@/types';

interface GatewayState {
  status: GatewayStatusResponse | null;
  loading: boolean;
  actionLoading: boolean;
  lastRefresh: Date | null;
  error: string | null;
  lastCommandOutput: string | null;

  fetchStatus: () => Promise<void>;
  performAction: (action: GatewayAction) => Promise<CommandResponse | null>;
}

export const useGatewayStore = create<GatewayState>((set) => ({
  status: null,
  loading: false,
  actionLoading: false,
  lastRefresh: null,
  error: null,
  lastCommandOutput: null,

  fetchStatus: async () => {
    set({ loading: true, error: null });
    try {
      const { data } = await gatewayApi.status();
      set({ status: data, loading: false, lastRefresh: new Date() });
    } catch (e) {
      set({ error: String(e), loading: false });
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
      // Refresh status after action
      const { data: statusData } = await gatewayApi.status();
      set({ status: statusData, lastRefresh: new Date() });
      return data;
    } catch (e) {
      set({ error: String(e), actionLoading: false });
      return null;
    }
  },
}));
