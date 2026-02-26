/**
 * AgentCard — summary card for fleet grid.
 */

import React from 'react';
import { Clock } from 'lucide-react';
import { Badge, statusVariant } from '@/components/common/Badge';
import { Card } from '@/components/common/Card';
import { formatRelativeTime } from '@/utils/time';
import type { AgentSummary } from '@/types';

interface AgentCardProps {
  agent: AgentSummary;
  onClick: (agentId: string) => void;
}

function shortenModel(model: string): string {
  // e.g. "anthropic/claude-opus-4-6" → "claude-opus-4-6"
  const parts = model.split('/');
  return parts[parts.length - 1] ?? model;
}

const STATUS_BORDER: Record<string, string> = {
  active: 'border-l-4 border-l-success',
  idle: 'border-l-4 border-l-warning',
  stopped: 'border-l-4 border-l-text-secondary',
  unknown: 'border-l-4 border-l-text-secondary',
};

export function AgentCard({ agent, onClick }: AgentCardProps): React.ReactElement {
  const borderClass = STATUS_BORDER[agent.status] ?? 'border-l-4 border-l-text-secondary';

  return (
    <Card
      hoverable
      onClick={() => onClick(agent.id)}
      className={`${borderClass} hover:translate-y-[-1px] hover:shadow-lg transition-all duration-150`}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-text-primary font-semibold text-sm">{agent.name}</h3>
          <p className="text-text-secondary text-xs mt-0.5 font-mono">{agent.id}</p>
        </div>
        {/* Status dot */}
        <span
          className={`w-3 h-3 rounded-full flex-shrink-0 mt-0.5 transition-colors duration-300 ${
            agent.status === 'active'
              ? 'bg-success animate-pulse'
              : agent.status === 'idle'
              ? 'bg-warning'
              : 'bg-text-secondary'
          }`}
          aria-label={`Status: ${agent.status}`}
          title={agent.status}
        />
      </div>

      {/* Model badge */}
      <Badge variant={statusVariant(agent.status)} className="mb-3">
        {shortenModel(agent.model)}
      </Badge>

      {/* Metadata */}
      <div className="flex items-center gap-4 text-text-secondary text-xs">
        <span className="flex items-center gap-1">
          <Clock size={11} aria-hidden="true" />
          {formatRelativeTime(agent.last_activity ?? null)}
        </span>
      </div>
    </Card>
  );
}
