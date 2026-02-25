/**
 * AgentPage — agent detail view.
 */

import React, { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { AgentDetail } from '@/components/agents/AgentDetail';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { useAgentStore } from '@/stores/agentStore';

function AgentPageContent(): React.ReactElement {
  const { agentId } = useParams<{ agentId: string }>();
  const selectedAgent = useAgentStore((s) => s.selectedAgent);
  const detailLoading = useAgentStore((s) => s.detailLoading);
  const error = useAgentStore((s) => s.error);
  const fetchAgent = useAgentStore((s) => s.fetchAgent);
  const clearSelectedAgent = useAgentStore((s) => s.clearSelectedAgent);

  useEffect(() => {
    if (agentId) {
      void fetchAgent(agentId);
    }
    return () => clearSelectedAgent();
  }, [agentId, fetchAgent, clearSelectedAgent]);

  return (
    <AgentDetail
      agent={selectedAgent}
      loading={detailLoading}
      error={error}
    />
  );
}

export default function AgentPage(): React.ReactElement {
  const { agentId } = useParams<{ agentId: string }>();

  return (
    <Layout title={agentId ? `Agent: ${agentId}` : 'Agent Detail'}>
      <ErrorBoundary label="Agent detail error">
        <AgentPageContent />
      </ErrorBoundary>
    </Layout>
  );
}
