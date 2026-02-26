/**
 * AgentCard — summary card for fleet grid.
 */

import React from 'react';
import { Clock } from 'lucide-react';
import { Badge, statusVariant } from '@/components/common/Badge';
import { Card } from '@/components/common/Card';
import type { AgentSummary } from '@/types';

interface AgentCardProps {
  agent: AgentSummary;
  onClick: (agentId: string) => void;
}

function formatRelativeTime(isoString: string | null): string {
  if (!isoString) return 'Never';
  const diff = Date.now() - new Date(isoString).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function shortenModel(model: string): string {
  // e.g. "anthropic/claude-opus-4-6" → "claude-opus-4-6"
  const parts = model.split('/');
  return parts[parts.length - 1] ?? model;
}

export function AgentCard({ agent, onClick }: AgentCardProps): React.ReactElement {
  return (
    <Card hoverable onClick={() => onClick(agent.id)}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-text-primary font-semibold text-sm">{agent.name}</h3>
          <p className="text-text-secondary text-xs mt-0.5 font-mono">{agent.id}</p>
        </div>
        {/* Status dot */}
        <span
          className={`w-3 h-3 rounded-full flex-shrink-0 mt-0.5 ${
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
