/**
 * ConnectionBanner — amber bar when WebSocket is disconnected.
 */

import React from 'react';
import { WifiOff } from 'lucide-react';
import { useWsStore } from '@/stores/wsStore';

export function ConnectionBanner(): React.ReactElement | null {
  const connectionState = useWsStore((s) => s.connectionState);

  if (connectionState === 'connected') return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="bg-warning/15 border-b border-warning/30 px-4 py-2 flex items-center gap-2 text-warning text-sm flex-shrink-0"
    >
      <WifiOff size={14} aria-hidden="true" />
      <span>
        {connectionState === 'connecting'
          ? 'Reconnecting to server…'
          : 'Connection lost — attempting to reconnect…'}
      </span>
    </div>
  );
}
