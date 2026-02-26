/**
 * Header — top bar with gateway status indicator + WS connection state.
 * Reads WS state from wsStore (not useWebSocket hook) to avoid duplicate connections.
 */

import React from 'react';
import { useGatewayStore } from '@/stores/gatewayStore';
import { useWsStore } from '@/stores/wsStore';

type DotColor = 'green' | 'amber' | 'red';

interface StatusDotProps {
  color: DotColor;
  label: string;
}

function StatusDot({ color, label }: StatusDotProps): React.ReactElement {
  const COLOR_MAP: Record<DotColor, string> = {
    green: 'bg-success',
    amber: 'bg-warning',
    red: 'bg-danger',
  };

  return (
    <span className="flex items-center gap-1.5">
      <span
        className={`w-2 h-2 rounded-full ${COLOR_MAP[color]}`}
        aria-label={label}
        title={label}
      />
      <span className="text-text-secondary text-xs hidden sm:inline">{label}</span>
    </span>
  );
}

interface HeaderProps {
  title?: string;
}

export function Header({ title }: HeaderProps): React.ReactElement {
  const gatewayStatus = useGatewayStore((s) => s.status);
  const connectionState = useWsStore((s) => s.connectionState);

  const gatewayColor: DotColor =
    gatewayStatus?.running ? 'green' : gatewayStatus === null ? 'amber' : 'red';
  const gatewayLabel = gatewayStatus?.running
    ? 'Gateway running'
    : gatewayStatus === null
    ? 'Gateway loading…'
    : 'Gateway stopped';

  const wsColor: DotColor =
    connectionState === 'connected' ? 'green' : connectionState === 'connecting' ? 'amber' : 'red';
  const wsLabel =
    connectionState === 'connected'
      ? 'Live'
      : connectionState === 'connecting'
      ? 'Reconnecting…'
      : 'Disconnected';

  return (
    <header className="h-12 flex-shrink-0 bg-bg-secondary border-b border-border flex items-center justify-between px-6">
      {title ? (
        <h1 className="text-text-primary text-base font-semibold truncate">{title}</h1>
      ) : (
        <span />
      )}

      <div className="flex items-center gap-4 flex-shrink-0">
        <StatusDot color={gatewayColor} label={gatewayLabel} />
        <StatusDot color={wsColor} label={wsLabel} />
      </div>
    </header>
  );
}
