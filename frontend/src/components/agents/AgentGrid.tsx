/**
 * AgentGrid — responsive grid of AgentCards.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Bot } from 'lucide-react';
import { AgentCard } from './AgentCard';
import { Spinner } from '@/components/common/Spinner';
import type { AgentSummary } from '@/types';

interface AgentGridProps {
  agents: AgentSummary[];
  loading: boolean;
  error: string | null;
}

export function AgentGrid({ agents, loading, error }: AgentGridProps): React.ReactElement {
  const navigate = useNavigate();

  const handleAgentClick = (agentId: string): void => {
    void navigate(`/agents/${encodeURIComponent(agentId)}`);
  };

  if (loading && agents.length === 0) {
    return (
      <div className="flex items-center justify-center py-16">
        <Spinner size="lg" label="Loading agents…" />
      </div>
    );
  }

  if (error && agents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
        <Bot size={40} className="text-text-secondary" />
        <p className="text-danger text-sm">{error}</p>
        <p className="text-text-secondary text-xs">Is the backend running on :8400?</p>
      </div>
    );
  }

  if (agents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
        <Bot size={40} className="text-text-secondary" />
        <p className="text-text-primary font-medium">No agents configured</p>
        <p className="text-text-secondary text-sm">Add agents to openclaw.json to see them here</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {agents.map((agent) => (
        <AgentCard key={agent.id} agent={agent} onClick={handleAgentClick} />
      ))}
    </div>
  );
}
