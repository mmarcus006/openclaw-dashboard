/**
 * GatewayPanel — gateway status + action buttons + channels table + command history.
 */

import React from 'react';
import { Play, Square, RotateCcw, Radio, Clock, Hash, AlertTriangle, ExternalLink } from 'lucide-react';
import { Button } from '@/components/common/Button';
import { Card } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { useGateway } from '@/hooks/useGateway';
import { useToastStore } from '@/stores/toastStore';

export function GatewayPanel(): React.ReactElement {
  const { status, loading, actionLoading, error, timedOut, history, performAction } = useGateway();
  const addToast = useToastStore((s) => s.addToast);

  const handleAction = async (action: 'start' | 'stop' | 'restart'): Promise<void> => {
    const result = await performAction(action);
    if (result) {
      addToast(result.success ? 'success' : 'error', result.message);
    } else {
      addToast('error', `Gateway ${action} failed`);
    }
  };

  // Timeout or error state — show error instead of infinite spinner
  if ((timedOut || error) && !status) {
    return (
      <div className="max-w-4xl space-y-4">
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <AlertTriangle size={20} className="text-warning" aria-hidden="true" />
            <div>
              <h3 className="text-text-primary font-semibold">Gateway Status Unavailable</h3>
              <p className="text-text-secondary text-sm">
                {timedOut
                  ? 'The gateway status request timed out after 5 seconds.'
                  : error}
              </p>
            </div>
          </div>
          <Button variant="secondary" size="md" onClick={() => void performAction('start')}>
            Try Again
          </Button>
        </Card>
      </div>
    );
  }

  // Still loading (first fetch, before timeout)
  if (loading && !status) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="flex items-center gap-3 text-text-secondary text-sm">
          <div className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          Loading gateway status…
        </div>
      </div>
    );
  }

  const isRunning = status?.running ?? false;
  const cliNotInstalled = status?.error?.includes('not found in PATH');
  const channels = status?.channels ?? {};
  const channelEntries = Object.entries(channels);

  // Gateway CLI not installed
  if (cliNotInstalled) {
    return (
      <div className="max-w-4xl space-y-4">
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <AlertTriangle size={20} className="text-warning" aria-hidden="true" />
            <div>
              <h3 className="text-text-primary font-semibold">Gateway Not Installed</h3>
              <p className="text-text-secondary text-sm">
                The <code className="text-text-primary font-mono">openclaw</code> CLI was not found in PATH.
              </p>
            </div>
          </div>
          <a
            href="https://docs.openclaw.ai/gateway/install"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-accent hover:text-accent-hover text-sm"
          >
            <ExternalLink size={13} aria-hidden="true" />
            Installation Guide
          </a>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl space-y-4">
      {/* Gateway Stopped — prominent card with Start button */}
      {!isRunning && (
        <Card>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <Radio size={20} className="text-text-secondary" aria-hidden="true" />
              <div>
                <h3 className="text-text-primary font-semibold">Gateway Stopped</h3>
                <p className="text-text-secondary text-sm">The gateway daemon is not running.</p>
              </div>
            </div>
            <Button
              variant="primary"
              size="md"
              loading={actionLoading}
              onClick={() => void handleAction('start')}
            >
              <Play size={14} aria-hidden="true" />
              Start Gateway
            </Button>
          </div>
        </Card>
      )}

      {/* Status card (when running) */}
      {isRunning && (
        <Card>
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <Radio size={20} className="text-success" aria-hidden="true" />
              <div>
                <h3 className="text-text-primary font-semibold">Gateway</h3>
                <p className="text-text-secondary text-sm">openclaw gateway daemon</p>
              </div>
            </div>
            <Badge variant="success">Running</Badge>
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            {status?.pid && (
              <div className="flex items-center gap-2 text-text-secondary text-sm">
                <Hash size={13} aria-hidden="true" />
                <span>PID: <code className="text-text-primary font-mono">{status.pid}</code></span>
              </div>
            )}
            {status?.uptime && (
              <div className="flex items-center gap-2 text-text-secondary text-sm">
                <Clock size={13} aria-hidden="true" />
                <span>Uptime: <span className="text-text-primary">{status.uptime}</span></span>
              </div>
            )}
          </div>

          {status?.error && (
            <div className="bg-danger/10 border border-danger/20 rounded-md px-3 py-2 mb-4">
              <p className="text-danger text-sm">{status.error}</p>
            </div>
          )}

          {/* Action buttons with disabled tooltips */}
          <div className="flex items-center gap-3">
            <span title="Gateway is already running">
              <Button
                variant="primary"
                size="md"
                loading={actionLoading}
                disabled={true}
                onClick={() => void handleAction('start')}
              >
                <Play size={14} aria-hidden="true" />
                Start
              </Button>
            </span>
            <Button
              variant="danger"
              size="md"
              loading={actionLoading}
              onClick={() => void handleAction('stop')}
            >
              <Square size={14} aria-hidden="true" />
              Stop
            </Button>
            <Button
              variant="secondary"
              size="md"
              loading={actionLoading}
              onClick={() => void handleAction('restart')}
            >
              <RotateCcw size={14} aria-hidden="true" />
              Restart
            </Button>
          </div>
        </Card>
      )}

      {/* When stopped, show Stop/Restart with appropriate disabled states */}
      {!isRunning && (
        <div className="flex items-center gap-3">
          <span title="Gateway is not running">
            <Button variant="danger" size="md" disabled={true}>
              <Square size={14} aria-hidden="true" />
              Stop
            </Button>
          </span>
          <Button
            variant="secondary"
            size="md"
            loading={actionLoading}
            onClick={() => void handleAction('restart')}
          >
            <RotateCcw size={14} aria-hidden="true" />
            Restart
          </Button>
        </div>
      )}

      {/* Channels table */}
      <Card>
        <h4 className="text-text-secondary text-xs font-medium uppercase tracking-wide mb-3">
          Channels
        </h4>
        {channelEntries.length === 0 ? (
          <p className="text-text-tertiary text-sm py-4 text-center">No channels configured</p>
        ) : (
          <div className="overflow-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-text-secondary text-xs uppercase tracking-wide">
                  <th className="text-left py-2 pr-4 font-medium">Channel</th>
                  <th className="text-left py-2 pr-4 font-medium">Status</th>
                  <th className="text-left py-2 font-medium">Provider</th>
                </tr>
              </thead>
              <tbody>
                {channelEntries.map(([name, value]) => {
                  const info = typeof value === 'object' && value !== null ? value as Record<string, unknown> : {};
                  return (
                    <tr key={name} className="border-b border-border/50">
                      <td className="py-2 pr-4 text-text-primary font-mono text-xs">{name}</td>
                      <td className="py-2 pr-4">
                        <Badge variant={info.connected ? 'success' : 'neutral'}>
                          {info.connected ? 'Connected' : String(info.status ?? 'Unknown')}
                        </Badge>
                      </td>
                      <td className="py-2 text-text-secondary text-xs">{String(info.provider ?? '—')}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Command history */}
      <Card>
        <h4 className="text-text-secondary text-xs font-medium uppercase tracking-wide mb-3">
          Last Command Output
        </h4>
        {history.length === 0 ? (
          <p className="text-text-tertiary text-sm">No recent commands</p>
        ) : (
          <div className="space-y-2">
            {history.slice(0, 5).map((entry, i) => (
              <div key={`${entry.timestamp}-${i}`} className="flex items-start gap-3 text-xs">
                <span
                  className={`font-mono font-bold ${entry.exit_code === 0 ? 'text-success' : 'text-danger'}`}
                >
                  {entry.exit_code}
                </span>
                <span className="text-text-secondary font-mono">
                  {new Date(entry.timestamp).toLocaleTimeString()}
                </span>
                <span className="text-text-primary font-mono">{entry.command}</span>
                {entry.output && (
                  <span className="text-text-secondary truncate max-w-xs" title={entry.output}>
                    {entry.output.split('\n')[0]}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
