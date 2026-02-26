/**
 * SessionList — displays session list for an agent with load-more pagination.
 */

import React, { useEffect } from 'react';
import { Clock, MessageSquare, Coins, ChevronDown, AlertTriangle } from 'lucide-react';
import { Skeleton } from '@/components/common/Skeleton';
import { EmptyState } from '@/components/common/EmptyState';
import { Button } from '@/components/common/Button';
import { useSessionStore } from '@/stores/sessionStore';
import type { SessionSummary } from '@/api/sessions';

function formatTimestamp(ms: number): string {
  return new Date(ms).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatTokens(tokens: number | null): string {
  if (tokens === null || tokens === undefined) return '--';
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`;
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(1)}K`;
  return String(tokens);
}

function shortenSessionId(sessionId: string): string {
  // "agent:main:telegram:123:direct:456" → "telegram:123:direct:456"
  const parts = sessionId.split(':');
  if (parts.length > 2) {
    return parts.slice(2).join(':');
  }
  return sessionId;
}

interface SessionRowProps {
  session: SessionSummary;
  selected: boolean;
  onSelect: (sessionId: string) => void;
}

function SessionRow({ session, selected, onSelect }: SessionRowProps): React.ReactElement {
  return (
    <button
      onClick={() => onSelect(session.session_id)}
      className={`w-full text-left px-4 py-3 border-b border-border transition-colors hover:bg-bg-hover/40 ${
        selected ? 'bg-accent/10 border-l-2 border-l-accent' : ''
      }`}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm text-text-primary font-mono truncate max-w-[60%]">
          {session.label || shortenSessionId(session.session_id)}
        </span>
        {session.model && (
          <span className="text-[10px] text-text-secondary bg-bg-hover px-1.5 py-0.5 rounded font-mono">
            {session.model}
          </span>
        )}
      </div>
      <div className="flex items-center gap-3 text-[11px] text-text-secondary">
        <span className="flex items-center gap-1">
          <Clock size={10} />
          {formatTimestamp(session.updated_at)}
        </span>
        {session.total_tokens !== null && (
          <span className="flex items-center gap-1">
            <Coins size={10} />
            {formatTokens(session.total_tokens)}
          </span>
        )}
      </div>
    </button>
  );
}

function SessionListSkeleton(): React.ReactElement {
  return (
    <div className="space-y-0">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="px-4 py-3 border-b border-border">
          <Skeleton height="16px" width="70%" className="mb-2" />
          <Skeleton height="12px" width="50%" />
        </div>
      ))}
    </div>
  );
}

interface SessionListProps {
  agentId: string;
}

export function SessionList({ agentId }: SessionListProps): React.ReactElement {
  const sessions = useSessionStore((s) => s.sessions);
  const loading = useSessionStore((s) => s.loading);
  const error = useSessionStore((s) => s.error);
  const total = useSessionStore((s) => s.total);
  const warning = useSessionStore((s) => s.warning);
  const selectedSessionId = useSessionStore((s) => s.selectedSessionId);
  const fetchSessions = useSessionStore((s) => s.fetchSessions);
  const loadMore = useSessionStore((s) => s.loadMoreSessions);
  const selectSession = useSessionStore((s) => s.selectSession);

  useEffect(() => {
    void fetchSessions(agentId);
  }, [agentId, fetchSessions]);

  if (loading && sessions.length === 0) {
    return <SessionListSkeleton />;
  }

  if (error) {
    return (
      <EmptyState
        icon={<AlertTriangle size={40} />}
        title="Could not load sessions"
        description={error}
        action={
          <Button variant="secondary" size="sm" onClick={() => void fetchSessions(agentId)}>
            Retry
          </Button>
        }
      />
    );
  }

  if (sessions.length === 0) {
    return (
      <EmptyState
        icon={<MessageSquare size={40} />}
        title="No sessions found"
        description="This agent has no recorded sessions yet."
      />
    );
  }

  return (
    <div>
      {warning && (
        <div className="flex items-center gap-2 px-4 py-2 bg-warning/10 text-warning text-xs">
          <AlertTriangle size={12} />
          {warning}
        </div>
      )}
      <div className="text-xs text-text-secondary px-4 py-2 border-b border-border">
        {total} sessions
      </div>
      {sessions.map((session) => (
        <SessionRow
          key={session.session_id}
          session={session}
          selected={selectedSessionId === session.session_id}
          onSelect={selectSession}
        />
      ))}
      {sessions.length < total && (
        <div className="flex justify-center py-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => void loadMore()}
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Load more'}
            <ChevronDown size={14} />
          </Button>
        </div>
      )}
    </div>
  );
}
