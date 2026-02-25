/**
 * WebSocket store — singleton connection state.
 * Prevents multiple WS connections when multiple components call useWebSocket.
 */

import { create } from 'zustand';
import type { WsConnectionState } from '@/types';

interface WsState {
  connectionState: WsConnectionState;
  setConnectionState: (state: WsConnectionState) => void;
}

export const useWsStore = create<WsState>((set) => ({
  connectionState: 'disconnected',
  setConnectionState: (connectionState: WsConnectionState) => set({ connectionState }),
}));
