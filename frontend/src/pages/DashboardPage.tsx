/**
 * DashboardPage — fleet overview.
 */

import React from 'react';
import { Layout } from '@/components/layout/Layout';
import { AgentGrid } from '@/components/agents/AgentGrid';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { useAgents } from '@/hooks/useAgents';
import { useGatewayStore } from '@/stores/gatewayStore';
import type { AgentSummary } from '@/types';

interface DashboardStatsProps {
  agents: AgentSummary[];
}

function DashboardStats({ agents }: DashboardStatsProps): React.ReactElement {
  const gatewayStatus = useGatewayStore((s) => s.status);

  const activeCount = agents.filter((a) => a.status === 'active').length;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
      <div className="bg-bg-card border border-border rounded-lg p-4">
        <p className="text-text-secondary text-xs mb-1">Total Agents</p>
        <p className="text-text-primary font-semibold text-2xl">{agents.length}</p>
      </div>
      <div className="bg-bg-card border border-border rounded-lg p-4">
        <p className="text-text-secondary text-xs mb-1">Active</p>
        <p className={`font-semibold text-2xl ${activeCount > 0 ? 'text-success' : 'text-text-secondary'}`}>{activeCount}</p>
      </div>
      <div className="bg-bg-card border border-border rounded-lg p-4">
        <p className="text-text-secondary text-xs mb-1">Gateway</p>
        <p className={`font-semibold text-2xl ${gatewayStatus?.running ? 'text-success' : 'text-text-secondary'}`}>
          {gatewayStatus === null ? '…' : gatewayStatus.running ? 'On' : 'Off'}
        </p>
      </div>
      <div className="bg-bg-card border border-border rounded-lg p-4">
        <p className="text-text-secondary text-xs mb-1">Idle</p>
        <p className="text-warning font-semibold text-2xl">
          {agents.filter((a) => a.status === 'idle').length}
        </p>
      </div>
    </div>
  );
}

function DashboardContent(): React.ReactElement {
  const { agents, loading, error } = useAgents();

  return (
    <>
      <DashboardStats agents={agents} />
      <AgentGrid agents={agents} loading={loading} error={error} />
    </>
  );
}

export default function DashboardPage(): React.ReactElement {
  return (
    <Layout title="Fleet Overview">
      <ErrorBoundary label="Dashboard error">
        <DashboardContent />
      </ErrorBoundary>
    </Layout>
  );
}
