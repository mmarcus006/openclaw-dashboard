/**
 * useWebSocket — WebSocket connection with exponential backoff reconnection.
 * Uses a module-level singleton so only ONE connection is created regardless
 * of how many components call this hook.
 *
 * Follows the protocol defined in PLAN-v2.md §5.5.
 */

import { useEffect } from 'react';
import type { WsMessage, WsConnectionState } from '@/types';
import { useGatewayStore } from '@/stores/gatewayStore';
import { useWsStore } from '@/stores/wsStore';

const WS_URL = (): string => `ws://${window.location.host}/ws/live`;
const MIN_RETRY_MS = 1_000;
const MAX_RETRY_MS = 30_000;
const BACKOFF_FACTOR = 2;

// Module-level singleton state — prevents multiple connections
let wsInstance: WebSocket | null = null;
let retryTimer: ReturnType<typeof setTimeout> | null = null;
let retryDelay = MIN_RETRY_MS;
let connectionCount = 0; // tracks active consumers
let isConnecting = false;

function getSetConnectionState(): (state: WsConnectionState) => void {
  return useWsStore.getState().setConnectionState;
}

function getFetchStatus(): () => Promise<void> {
  return useGatewayStore.getState().fetchStatus;
}

function clearRetryTimer(): void {
  if (retryTimer !== null) {
    clearTimeout(retryTimer);
    retryTimer = null;
  }
}

function scheduleReconnect(): void {
  clearRetryTimer();
  retryTimer = setTimeout(() => {
    retryDelay = Math.min(retryDelay * BACKOFF_FACTOR, MAX_RETRY_MS);
    connectWs();
  }, retryDelay);
}

function connectWs(): void {
  if (wsInstance?.readyState === WebSocket.OPEN || isConnecting) return;

  isConnecting = true;
  getSetConnectionState()('connecting');

  const ws = new WebSocket(WS_URL());
  wsInstance = ws;

  ws.onopen = () => {
    isConnecting = false;
    getSetConnectionState()('connected');
    retryDelay = MIN_RETRY_MS;
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data as string) as WsMessage;

      if (msg.type === 'ping') {
        ws.send(JSON.stringify({ type: 'pong' }));
        return;
      }

      if (msg.type === 'gateway_status') {
        void getFetchStatus()();
      }
    } catch {
      // Malformed message — ignore
    }
  };

  ws.onerror = () => {
    isConnecting = false;
  };

  ws.onclose = () => {
    isConnecting = false;
    wsInstance = null;
    if (connectionCount > 0) {
      getSetConnectionState()('disconnected');
      scheduleReconnect();
    }
  };
}

function disconnectWs(): void {
  clearRetryTimer();
  wsInstance?.close();
  wsInstance = null;
  isConnecting = false;
  getSetConnectionState()('disconnected');
}

/**
 * Hook — call from App root to establish the connection.
 * Safe to call from multiple components; only ONE connection is created.
 */
export function useWebSocket(): { connectionState: WsConnectionState } {
  const connectionState = useWsStore((s) => s.connectionState);

  useEffect(() => {
    connectionCount++;
    if (connectionCount === 1) {
      connectWs();
    }
    return () => {
      connectionCount--;
      if (connectionCount === 0) {
        disconnectWs();
      }
    };
  }, []);

  return { connectionState };
}
