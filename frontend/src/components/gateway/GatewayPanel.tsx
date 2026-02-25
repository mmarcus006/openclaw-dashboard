/**
 * GatewayPanel — gateway status + action buttons.
 */

import React from 'react';
import { Play, Square, RotateCcw, Radio, Clock, Hash } from 'lucide-react';
import { Button } from '@/components/common/Button';
import { Card } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { Spinner } from '@/components/common/Spinner';
import { useGateway } from '@/hooks/useGateway';
import { useToastStore } from '@/stores/toastStore';

export function GatewayPanel(): React.ReactElement {
  const { status, loading, actionLoading, error, lastCommandOutput, performAction } = useGateway();
  const addToast = useToastStore((s) => s.addToast);

  const handleAction = async (action: 'start' | 'stop' | 'restart'): Promise<void> => {
    const result = await performAction(action);
    if (result) {
      addToast(result.success ? 'success' : 'error', result.message);
    } else {
      addToast('error', `Gateway ${action} failed`);
    }
  };

  if (loading && !status) {
    return (
      <div className="flex items-center justify-center py-16">
        <Spinner size="lg" label="Loading gateway status…" />
      </div>
    );
  }

  const isRunning = status?.running ?? false;

  return (
    <div className="max-w-2xl space-y-4">
      {/* Status card */}
      <Card>
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <Radio size={20} className={isRunning ? 'text-success' : 'text-text-secondary'} aria-hidden="true" />
            <div>
              <h3 className="text-text-primary font-semibold">Gateway</h3>
              <p className="text-text-secondary text-sm">openclaw gateway daemon</p>
            </div>
          </div>
          <Badge variant={isRunning ? 'success' : 'neutral'}>
            {isRunning ? 'Running' : 'Stopped'}
          </Badge>
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

        {error && !status?.error && (
          <div className="bg-danger/10 border border-danger/20 rounded-md px-3 py-2 mb-4">
            <p className="text-danger text-sm">{error}</p>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            size="md"
            loading={actionLoading}
            disabled={isRunning}
            onClick={() => void handleAction('start')}
          >
            <Play size={14} aria-hidden="true" />
            Start
          </Button>
          <Button
            variant="danger"
            size="md"
            loading={actionLoading}
            disabled={!isRunning}
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

      {/* Command output */}
      {lastCommandOutput && (
        <Card>
          <h4 className="text-text-secondary text-xs font-medium uppercase tracking-wide mb-2">
            Last Command Output
          </h4>
          <pre className="text-text-primary text-xs font-mono whitespace-pre-wrap bg-bg-primary rounded-md p-3 overflow-auto max-h-48">
            {lastCommandOutput}
          </pre>
        </Card>
      )}

      {/* Channel status */}
      {status?.channels && Object.keys(status.channels).length > 0 && (
        <Card>
          <h4 className="text-text-secondary text-xs font-medium uppercase tracking-wide mb-2">
            Channels
          </h4>
          <pre className="text-text-primary text-xs font-mono whitespace-pre-wrap">
            {JSON.stringify(status.channels, null, 2)}
          </pre>
        </Card>
      )}
    </div>
  );
}
